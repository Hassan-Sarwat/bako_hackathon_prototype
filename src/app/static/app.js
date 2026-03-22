let ws;
let audioContext;
let processor;
let mediaStream;
let isRecording = false;
let geminiSpeaking = false;
let geminiSpeakingTimer = null;

const talkButton   = document.getElementById('talkButton');
const statusText   = document.getElementById('statusText');
const micIconOn    = document.getElementById('micIconOn');
const micIconOff   = document.getElementById('micIconOff');
const buttonLabel  = document.getElementById('buttonLabel');
const transcript   = document.getElementById('transcript');
const glowEffect   = document.getElementById('glowEffect');
const wave1        = document.getElementById('wave1');
const wave2        = document.getElementById('wave2');
const wave3        = document.getElementById('wave3');

const SAMPLE_RATE = 16000;
let nextPlayTime = 0;

function setWaveActive(active) {
    [wave1, wave2, wave3].forEach((el, i) => {
        if (active) {
            el.classList.add('wave-active');
            if (i === 1) el.classList.add('delay-1');
            if (i === 2) el.classList.add('delay-2');
        } else {
            el.classList.remove('wave-active', 'delay-1', 'delay-2');
        }
    });
}

function setButtonActive(active) {
    if (active) {
        talkButton.classList.add('pulsate');
        micIconOff.classList.add('hidden');
        micIconOn.classList.remove('hidden');
        buttonLabel.textContent = 'Zuhören...';
        glowEffect.classList.remove('scale-125', 'opacity-20');
        glowEffect.classList.add('scale-150', 'opacity-40');
    } else {
        talkButton.classList.remove('pulsate');
        micIconOn.classList.add('hidden');
        micIconOff.classList.remove('hidden');
        buttonLabel.textContent = 'Cast';
        glowEffect.classList.remove('scale-150', 'opacity-40');
        glowEffect.classList.add('scale-125', 'opacity-20');
    }
}

talkButton.addEventListener('click', async () => {
    if (isRecording) {
        stopCommunication();
    } else {
        await startCommunication();
    }
});

async function startCommunication() {
    try {
        ws = new WebSocket(`${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`);
        ws.binaryType = 'arraybuffer';

        ws.onopen = async () => {
            statusText.textContent = "Verbinde......";
            setButtonActive(true);
            setWaveActive(true);
            isRecording = true;
            nextPlayTime = 0;

            audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: SAMPLE_RATE
            });

            mediaStream = await navigator.mediaDevices.getUserMedia({ audio: {
                channelCount: 1,
                sampleRate: SAMPLE_RATE,
                echoCancellation: true,
                noiseSuppression: true
            } });

            // Wait, if the websocket closed while we were getting user media,
            // stopCommunication() will have been called, making audioContext null.
            if (!audioContext) {
                if (mediaStream) {
                    mediaStream.getTracks().forEach(track => track.stop());
                }
                return;
            }

            const source = audioContext.createMediaStreamSource(mediaStream);
            processor = audioContext.createScriptProcessor(4096, 1, 1);

            processor.onaudioprocess = (e) => {
                if (!isRecording || ws.readyState !== WebSocket.OPEN || geminiSpeaking) return;

                const inputData = e.inputBuffer.getChannelData(0);
                const pcmData = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    const s = Math.max(-1, Math.min(1, inputData[i]));
                    pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }
                ws.send(pcmData.buffer);
            };

            source.connect(processor);
            processor.connect(audioContext.destination);

            statusText.textContent = "Listening for Spell...";
        };

        ws.onclose = () => {
            stopCommunication();
            statusText.textContent = "Verbindung getrennt.";
        };

        ws.onmessage = async (event) => {
            if (event.data instanceof ArrayBuffer) {
                // Play received PCM audio
                playAudioChunk(event.data);
            } else if (typeof event.data === 'string') {
                try {
                    const msg = JSON.parse(event.data);
                    if (msg.text) {
                        transcript.textContent = msg.text;
                    }
                } catch(e) {}
            }
        };

    } catch (e) {
        console.error("Error setting up audio/ws: ", e);
        statusText.textContent = "Hardwarefehler – Konsole prüfen.";
        stopCommunication();
    }
}

function stopCommunication() {
    isRecording = false;
    geminiSpeaking = false;
    if (geminiSpeakingTimer) { clearTimeout(geminiSpeakingTimer); geminiSpeakingTimer = null; }
    setButtonActive(false);
    setWaveActive(false);
    statusText.textContent = "Zum Starten klicken";

    if (processor) {
        processor.disconnect();
        processor = null;
    }
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }
    if (audioContext && audioContext.state !== 'closed') {
        audioContext.close();
        audioContext = null;
    }
    if (ws) {
        ws.close();
        ws = null;
    }
}

async function playAudioChunk(arrayBuffer) {
    if (!audioContext || audioContext.state === 'closed') return;
    try {
        const int16Array = new Int16Array(arrayBuffer);
        const float32Array = new Float32Array(int16Array.length);
        for (let i = 0; i < int16Array.length; i++) {
            float32Array[i] = int16Array[i] / 32768.0;
        }

        const buffer = audioContext.createBuffer(1, float32Array.length, 24000);
        buffer.getChannelData(0).set(float32Array);

        const source = audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(audioContext.destination);

        const currentTime = audioContext.currentTime;
        if (nextPlayTime < currentTime) {
            nextPlayTime = currentTime;
        }

        source.start(nextPlayTime);
        nextPlayTime += buffer.duration;

        // Mute microphone while Gemini is speaking to prevent echo confusing the VAD.
        // Re-enable 400ms after the last scheduled chunk finishes playing.
        geminiSpeaking = true;
        statusText.textContent = "Spricht...";
        if (geminiSpeakingTimer) clearTimeout(geminiSpeakingTimer);
        const msUntilDone = Math.max(0, (nextPlayTime - audioContext.currentTime) * 1000) + 400;
        geminiSpeakingTimer = setTimeout(() => {
            geminiSpeaking = false;
            geminiSpeakingTimer = null;
            if (isRecording) statusText.textContent = "Zuhören...";
        }, msUntilDone);
    } catch (e) {
        console.error("Error playing audio: ", e);
    }
}
