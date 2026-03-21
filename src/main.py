"""Bakery Voice Assistant - main entry point.

Connects to Gemini Live API for real-time voice interaction,
with tool calling for checklist and inventory management.
"""

import asyncio
import sys
import traceback

import pyaudio
from dotenv import load_dotenv
from google import genai
from google.genai import types

from .config import (
    CHANNELS,
    CHUNK_SIZE,
    MODEL,
    RECEIVE_SAMPLE_RATE,
    SEND_SAMPLE_RATE,
    SYSTEM_INSTRUCTION,
)
from .db import init_db
from .tool_handlers import handle_tool_call
from .tools import all_tools

load_dotenv()

# Audio format
FORMAT = pyaudio.paInt16


async def run():
    """Main async loop: connect to Gemini Live API and stream audio."""
    # Initialize database
    init_db()
    print("Database initialized with bakery checklists.")

    # Create Gemini client
    client = genai.Client(http_options={"api_version": "v1alpha"})

    # Live API config
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=types.Content(
            parts=[types.Part(text=SYSTEM_INSTRUCTION)]
        ),
        tools=[all_tools],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
            )
        ),
    )

    # Audio queues
    audio_in_queue: asyncio.Queue[bytes] = asyncio.Queue()
    audio_out_queue: asyncio.Queue[bytes] = asyncio.Queue()

    # PyAudio setup
    pya = pyaudio.PyAudio()

    async def listen_microphone():
        """Capture audio from microphone and put into queue."""
        mic_stream = pya.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
        )
        print("Microphone ready. Start speaking!")
        print("(Press Ctrl+C to exit)\n")

        try:
            while True:
                data = await asyncio.to_thread(mic_stream.read, CHUNK_SIZE, exception_on_overflow=False)
                audio_in_queue.put_nowait(data)
        except Exception:
            pass
        finally:
            mic_stream.stop_stream()
            mic_stream.close()

    async def send_audio(session):
        """Send microphone audio to the Gemini session."""
        while True:
            data = await audio_in_queue.get()
            await session.send_realtime_input(
                audio=types.Blob(data=data, mime_type=f"audio/pcm;rate={SEND_SAMPLE_RATE}")
            )

    async def receive_audio(session):
        """Receive responses from Gemini - handle both audio and tool calls."""
        while True:
            try:
                async for response in session.receive():
                    # Handle server content (audio responses)
                    server_content = response.server_content
                    if server_content and server_content.model_turn:
                        for part in server_content.model_turn.parts:
                            if part.inline_data:
                                audio_out_queue.put_nowait(part.inline_data.data)

                    # Handle tool calls
                    if response.tool_call:
                        function_responses = []
                        for fc in response.tool_call.function_calls:
                            result = await handle_tool_call(fc.name, fc.args)
                            function_responses.append(
                                types.FunctionResponse(
                                    id=fc.id,
                                    name=fc.name,
                                    response=result,
                                )
                            )
                        await session.send_tool_response(
                            function_responses=function_responses
                        )
            except Exception as e:
                if "close" in str(e).lower() or "cancelled" in str(e).lower():
                    break
                traceback.print_exc()
                break

    async def play_audio():
        """Play received audio through speakers."""
        speaker_stream = pya.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
            frames_per_buffer=CHUNK_SIZE,
        )
        try:
            while True:
                data = await audio_out_queue.get()
                await asyncio.to_thread(speaker_stream.write, data)
        except Exception:
            pass
        finally:
            speaker_stream.stop_stream()
            speaker_stream.close()

    print(f"Connecting to Gemini Live API ({MODEL})...")

    async with client.aio.live.connect(model=MODEL, config=config) as session:
        print("Connected! The assistant will greet you shortly.\n")

        async with asyncio.TaskGroup() as tg:
            tg.create_task(listen_microphone())
            tg.create_task(send_audio(session))
            tg.create_task(receive_audio(session))
            tg.create_task(play_audio())


def main():
    """Entry point."""
    print("=" * 50)
    print("  Bakery Voice Assistant")
    print("  Sanitation & Inventory Checklist Manager")
    print("=" * 50)
    print()
    print("TIP: Use headphones to prevent echo feedback.")
    print()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n\nGoodbye! Have a great baking day!")
        sys.exit(0)


if __name__ == "__main__":
    main()
