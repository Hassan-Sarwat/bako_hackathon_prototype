let ws;
let audioContext;
let processor;
let mediaStream;
let isRecording = false;

const talkButton = document.getElementById('talkButton');
const statusText = document.getElementById('statusText');
const micIcon = document.getElementById('micIcon');
const transcript = document.getElementById('transcript');

const SAMPLE_RATE = 16000; 
let nextPlayTime = 0;

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
            statusText.textContent = "Connecting to Audio...";
            talkButton.classList.add('pulsate');
            micIcon.classList.add('scale-110');
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
                if (!isRecording || ws.readyState !== WebSocket.OPEN) return;
                
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
            
            statusText.textContent = "Listening...";
        };
        
        ws.onclose = () => {
            stopCommunication();
            statusText.textContent = "Disconnected.";
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
        statusText.textContent = "Hardware error check console.";
        stopCommunication();
    }
}

function stopCommunication() {
    isRecording = false;
    talkButton.classList.remove('pulsate');
    micIcon.classList.remove('scale-110');
    statusText.textContent = "Click to connect";
    
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
    } catch (e) {
        console.error("Error playing audio: ", e);
    }
}
