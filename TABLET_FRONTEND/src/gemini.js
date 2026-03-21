/**
 * Gemini audio service — send an audio blob, get a text response back.
 *
 * Model: gemini-2.0-flash
 *   • Supports inline audio input (wav, mp3, ogg, flac, aac, …)
 *   • Fast, low-latency, multimodal
 *   • Use the standard generateContent REST API (not the Live/WebSocket API)
 */

const GEMINI_MODEL = 'gemini-2.0-flash';
const GEMINI_API_URL = `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent`;

/**
 * Convert an audio Blob to a base64 string.
 * @param {Blob} blob
 * @returns {Promise<string>} base64-encoded audio bytes
 */
function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      // reader.result is "data:<mime>;base64,<data>" — strip the prefix
      const base64 = reader.result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

/**
 * Send an audio blob to Gemini and receive a text response.
 *
 * @param {Blob}   audioBlob   - Audio recorded from the microphone (webm/ogg/wav)
 * @param {string} [prompt]    - Optional text prompt to accompany the audio
 * @returns {Promise<string>}  - Gemini's text reply
 */
export async function sendAudioToGemini(audioBlob, prompt = 'Transcribe and respond to the audio.') {
  const apiKey = import.meta.env.VITE_GEMINI_API_KEY;
  console.log('[Gemini] API key present:', !!apiKey);

  if (!apiKey) {
    throw new Error('VITE_GEMINI_API_KEY is not set in .env');
  }

  console.log('[Gemini] Audio blob size:', audioBlob.size, 'type:', audioBlob.type);

  const base64Audio = await blobToBase64(audioBlob);
  const mimeType = audioBlob.type || 'audio/webm';

  console.log('[Gemini] Sending request to:', GEMINI_API_URL);
  console.log('[Gemini] MIME type:', mimeType, '| base64 length:', base64Audio.length);

  const requestBody = {
    contents: [
      {
        parts: [
          { text: prompt },
          {
            inline_data: {
              mime_type: mimeType,
              data: base64Audio,
            },
          },
        ],
      },
    ],
  };

  const response = await fetch(`${GEMINI_API_URL}?key=${apiKey}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody),
  });

  console.log('[Gemini] Response status:', response.status, response.statusText);

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    console.error('[Gemini] Error body:', err);
    throw new Error(`Gemini API error ${response.status}: ${err?.error?.message ?? response.statusText}`);
  }

  const data = await response.json();
  console.log('[Gemini] Full response:', JSON.stringify(data, null, 2));

  const text = data?.candidates?.[0]?.content?.parts?.[0]?.text;
  console.log('[Gemini] Extracted text:', text);

  if (!text) {
    throw new Error('No text response from Gemini');
  }
  return text;
}
