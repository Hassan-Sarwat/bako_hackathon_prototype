"""
Voice test for the bakery assistant — talk to it with your mic, hear responses.

Tests latency, voice quality, and tool execution in real-time.
Uses a separate test_bakery.db so your real data is untouched.

Run:  python test_voice.py
      python test_voice.py --use-real-db      (use real bakery.db)
      python test_voice.py --staff-id alice    (set staff name)

Controls (type in terminal while voice is running):
  /db       — dump database state
  /logs     — show audit log
  /reset    — reset checklists
  /quit     — exit
"""

import argparse
import asyncio
import json
import os
import sys
import time
import traceback
from datetime import date
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

load_dotenv()

# ── Args ─────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Voice test for bakery assistant")
parser.add_argument("--staff-id", default="test-user", help="Staff ID (default: test-user)")
parser.add_argument("--use-real-db", action="store_true", help="Use real bakery.db")
args = parser.parse_args()

# ── Patch DB for test isolation ──────────────────────────────
if not args.use_real_db:
    TEST_DB = Path(__file__).parent / "test_bakery.db"
    import src.config
    src.config.DB_PATH = TEST_DB
    print(f"[setup] Using test database: {TEST_DB}")
else:
    print("[setup] Using real database: bakery.db")

from src import db
from src.config import (
    CHANNELS,
    CHUNK_SIZE,
    MODEL,
    RECEIVE_SAMPLE_RATE,
    SEND_SAMPLE_RATE,
    SYSTEM_INSTRUCTION,
)
from src.tool_handlers import handle_tool_call
from src.tools import all_tools

import pyaudio
from google import genai

# ── Init ─────────────────────────────────────────────────────
db.init_db()
client = genai.Client()
STAFF_ID = args.staff_id

# Latency tracking
latency_samples = []



def dump_db():
    """Print database state."""
    conn = db.get_connection()
    cur = conn.cursor()

    print("\n" + "=" * 60)
    print("  DATABASE STATE")
    print("=" * 60)

    print("\n-- Sanitation Checklist --")
    cur.execute("SELECT id, item_name, is_complete, completed_by, notes FROM checklist_items WHERE checklist_type='sanitation'")
    for row in cur.fetchall():
        status = "DONE" if row["is_complete"] else "    "
        by = f" (by {row['completed_by']})" if row["completed_by"] else ""
        notes = f" [{row['notes']}]" if row["notes"] else ""
        print(f"  [{status}] #{row['id']} {row['item_name']}{by}{notes}")

    print("\n-- Materials --")
    cur.execute("SELECT id, item_name, count, updated_at, updated_by FROM materials ORDER BY item_name")
    for row in cur.fetchall():
        by = f" (by {row['updated_by']})" if row["updated_by"] else ""
        at = f" [{row['updated_at']}]" if row["updated_at"] else ""
        print(f"  #{row['id']} {row['item_name']}: {row['count']}{by}{at}")

    today = date.today().isoformat()
    print(f"\n-- Cleaning Tasks ({today}) --")
    cur.execute("SELECT id, area, action, is_complete, completed_by, notes FROM cleaning_tasks WHERE task_date=?", (today,))
    rows = cur.fetchall()
    if rows:
        for row in rows:
            status = "DONE" if row["is_complete"] else "    "
            by = f" (by {row['completed_by']})" if row["completed_by"] else ""
            notes = f" [{row['notes']}]" if row["notes"] else ""
            print(f"  [{status}] #{row['id']} {row['area']}: {row['action']}{by}{notes}")
    else:
        print("  (no tasks yet)")

    print("\n-- Open Tickets --")
    cur.execute("SELECT id, title, category, urgency, raised_by FROM tickets WHERE status='open' ORDER BY CASE urgency WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'normal' THEN 2 WHEN 'low' THEN 3 END")
    rows = cur.fetchall()
    if rows:
        for row in rows:
            print(f"  [{row['urgency'].upper()}] #{row['id']} {row['title']} ({row['category']}) — by {row['raised_by']}")
    else:
        print("  (no open tickets)")

    if latency_samples:
        avg = sum(latency_samples) / len(latency_samples)
        print(f"\n-- Latency Stats --")
        print(f"  Samples: {len(latency_samples)}")
        print(f"  Avg: {avg:.0f}ms | Min: {min(latency_samples):.0f}ms | Max: {max(latency_samples):.0f}ms")

    print("=" * 60 + "\n")
    conn.close()


def dump_logs(limit=10):
    """Print recent audit log."""
    entries = db.get_audit_log(limit=limit)
    print("\n" + "=" * 60)
    print(f"  AUDIT LOG (last {limit})")
    print("=" * 60)
    if not entries:
        print("  (empty)")
    for e in reversed(entries):
        print(f"\n  [{e['created_at']}] staff={e['staff_id']}")
        if e["tool_name"]:
            print(f"    tool: {e['tool_name']}({e['tool_args']})")
            print(f"    result: {e['tool_result']}")
        if e["user_message"]:
            print(f"    user: {e['user_message']}")
        if e["ai_response"]:
            resp = e["ai_response"][:200] + "..." if len(e["ai_response"] or "") > 200 else e["ai_response"]
            print(f"    ai: {resp}")
    print("=" * 60 + "\n")


async def stdin_listener(stop_event: asyncio.Event):
    """Listen for typed commands while voice session is running."""
    loop = asyncio.get_event_loop()
    while not stop_event.is_set():
        try:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            cmd = line.strip().lower()
            if cmd == "/db":
                dump_db()
            elif cmd == "/logs":
                dump_logs()
            elif cmd == "/reset":
                res = db.reset_checklists()
                print(f"  -> {res}")
            elif cmd in ("/quit", "/exit", "/end"):
                print("\n[info] Shutting down...")
                stop_event.set()
                break
        except Exception:
            break


async def voice_session():
    """Run the Gemini Live API voice session with tool support."""
    stop_event = asyncio.Event()

    # Start stdin listener in background
    stdin_task = asyncio.create_task(stdin_listener(stop_event))

    pya = pyaudio.PyAudio()

    # Open mic input stream
    mic_stream = pya.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=SEND_SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
    )

    # Open speaker output stream
    speaker_stream = pya.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=RECEIVE_SAMPLE_RATE,
        output=True,
        frames_per_buffer=CHUNK_SIZE,
    )

    config = {
        "response_modalities": ["AUDIO"],
        "system_instruction": SYSTEM_INSTRUCTION,
        "tools": [all_tools],
    }

    print("\n" + "=" * 60)
    print("  VOICE TEST — Bakery Assistant")
    print(f"  Staff: {STAFF_ID} | Model: {MODEL}")
    print("  Speak into your mic. The assistant will respond.")
    print("  Type /db /logs /reset /quit in the terminal.")
    print("=" * 60)
    print("\n[mic] Listening... speak now!\n")

    last_speech_end = None
    first_audio_received = False

    try:
        async with client.aio.live.connect(model=MODEL, config=config) as session:

            # ── Task: send mic audio to Gemini ───────────────
            async def send_audio():
                nonlocal last_speech_end
                loop = asyncio.get_event_loop()
                while not stop_event.is_set():
                    try:
                        data = await loop.run_in_executor(
                            None, mic_stream.read, CHUNK_SIZE, False
                        )
                        await session.send_realtime_input(
                            audio=genai.types.Blob(data=data, mime_type="audio/pcm;rate=16000")
                        )
                    except OSError:
                        # Mic overflow — skip
                        pass
                    except Exception as e:
                        if not stop_event.is_set():
                            print(f"[mic error] {e}")
                        break

            # ── Task: receive from Gemini & play / handle tools ──
            async def receive_audio():
                nonlocal last_speech_end, first_audio_received
                while not stop_event.is_set():
                    try:
                        turn = session.receive()
                        first_audio_of_turn = True
                        turn_start = time.time()

                        async for response in turn:
                            # Handle server content (audio)
                            if response.server_content and response.server_content.model_turn:
                                for part in response.server_content.model_turn.parts:
                                    if part.inline_data:
                                        if first_audio_of_turn:
                                            latency_ms = (time.time() - turn_start) * 1000
                                            latency_samples.append(latency_ms)
                                            print(f"  [latency] {latency_ms:.0f}ms (first audio byte)")
                                            first_audio_of_turn = False

                                        speaker_stream.write(part.inline_data.data)

                                    if part.text:
                                        print(f"  [transcript] {part.text}")

                                # Check if turn is complete
                                if response.server_content.turn_complete:
                                    print("  [turn complete]")
                                    turn_start = time.time()
                                    first_audio_of_turn = True

                            # Handle tool calls
                            if response.tool_call:
                                for fc in response.tool_call.function_calls:
                                    fn_name = fc.name
                                    fn_args = dict(fc.args) if fc.args else {}

                                    print(f"\n  [Tool Call] {fn_name}({json.dumps(fn_args, ensure_ascii=False)})")

                                    # Handle end_session locally
                                    if fn_name == "end_session":
                                        print("\n[info] User said goodbye — shutting down...")
                                        result = {"status": "success", "message": "Sitzung wird beendet. Tschüss!"}
                                        await session.send_tool_response(
                                            function_responses=[
                                                genai.types.FunctionResponse(
                                                    id=fc.id,
                                                    name=fn_name,
                                                    response=result,
                                                )
                                            ]
                                        )
                                        # Let Gemini say goodbye, then stop
                                        await asyncio.sleep(3)
                                        stop_event.set()
                                        break

                                    result = await handle_tool_call(
                                        function_name=fn_name,
                                        args=fn_args,
                                        staff_id=STAFF_ID,
                                    )
                                    print(f"  [Tool Result] {json.dumps(result, ensure_ascii=False)}")

                                    # Send result back to Gemini
                                    await session.send_tool_response(
                                        function_responses=[
                                            genai.types.FunctionResponse(
                                                id=fc.id,
                                                name=fn_name,
                                                response=result,
                                            )
                                        ]
                                    )
                                    turn_start = time.time()
                                    first_audio_of_turn = True

                    except Exception as e:
                        if not stop_event.is_set():
                            print(f"[receive error] {e}")
                            traceback.print_exc()
                        break

            # Run send + receive concurrently
            send_task = asyncio.create_task(send_audio())
            recv_task = asyncio.create_task(receive_audio())

            # Wait until stop is signaled
            await stop_event.wait()

            send_task.cancel()
            recv_task.cancel()

    except KeyboardInterrupt:
        print("\n[info] Interrupted")
    except Exception as e:
        print(f"[error] {e}")
        traceback.print_exc()
    finally:
        mic_stream.stop_stream()
        mic_stream.close()
        speaker_stream.stop_stream()
        speaker_stream.close()
        pya.terminate()
        stdin_task.cancel()

        # Print final stats
        if latency_samples:
            avg = sum(latency_samples) / len(latency_samples)
            print(f"\n{'=' * 60}")
            print(f"  LATENCY SUMMARY")
            print(f"  Turns: {len(latency_samples)}")
            print(f"  Avg: {avg:.0f}ms | Min: {min(latency_samples):.0f}ms | Max: {max(latency_samples):.0f}ms")
            print(f"{'=' * 60}")

        print("\n[info] Session ended. Type /db or /logs to inspect, or check test_bakery.db directly.\n")


if __name__ == "__main__":
    asyncio.run(voice_session())
