import asyncio
import os
from google import genai
from google.genai import types

async def main():
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "dummy_key"))
    # We just want to inspect the structure of the pydantic or typed dictionaries it accepts.
    config = types.LiveConnectConfig(
        response_modalities=[types.LiveConfigModality.AUDIO]
    )
    print("Modality enum:", types.LiveConfigModality.AUDIO)
    try:
        data = b"dummy_audio"
        # Dummy attempt to construct the input
        # check type of LiveClientRealtimeInput
        req = types.LiveClientRealtimeInput(media_chunks=[types.Blob(mime_type="audio/pcm;rate=16000", data=data)])
        print("req:", req)
    except Exception as e:
        print("Error construction:", e)

if __name__ == "__main__":
    asyncio.run(main())
