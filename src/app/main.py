import asyncio
import os
import json
import sys
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Let's add the project root to sys.path in case it's run without python -m
sys.path.append(str(Path(__file__).parent.parent.parent))

from src import db
from src.tools import all_tools
from src.tool_handlers import handle_tool_call
from src.config import SYSTEM_INSTRUCTION

db.init_db()

load_dotenv()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def read_root():
    with open(STATIC_DIR / "index.html") as f:
        return HTMLResponse(f.read())

def _action_summary(fn_name: str, fn_args: dict) -> str | None:
    """Return a concise human-readable summary for mutating tool calls, or None for read-only ones."""
    if fn_name == "update_material_count":
        return f"{fn_args.get('item_name', 'Material')} auf {fn_args.get('count', '?')} aktualisiert."
    if fn_name == "raise_ticket":
        urgency_map = {"urgent": "dringend", "high": "hoch", "normal": "normal", "low": "niedrig"}
        urgency = urgency_map.get(fn_args.get("urgency", ""), fn_args.get("urgency", ""))
        return f"Ticket gemeldet: {fn_args.get('title', 'Problem')} ({urgency})."
    if fn_name == "mark_item_complete":
        return "Hygiene-Aufgabe abgehakt."
    if fn_name == "mark_item_incomplete":
        return "Hygiene-Aufgabe wieder geöffnet."
    if fn_name == "mark_cleaning_complete":
        return "Reinigungsaufgabe abgehakt."
    if fn_name == "mark_cleaning_incomplete":
        return "Reinigungsaufgabe wieder geöffnet."
    return None  # read-only tools — Gemini speaks the result, no transcript update needed


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Ensure GEMINI_API_KEY is available
    if not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY environment variable is not set")
        await websocket.close()
        return

    # Initialize genai client
    client = genai.Client()
    
    # We configure for AUDIO responses, tools, and system instructions
    config = {
        "response_modalities": ["AUDIO"],
        "system_instruction": SYSTEM_INSTRUCTION,
        "tools": [all_tools],
    }
    
    # Placeholder for staff_id until we pass it dynamically from the frontend
    staff_id = "test-user"
    
    try:
        # Connect to Live connect session 
        async with client.aio.live.connect(model="gemini-2.5-flash-native-audio-preview-12-2025", config=config) as session:
            print("Connected to Gemini Live")
            
            async def receive_from_client():
                try:
                    while True:
                        # Receive PCM audio bytes from front-end
                        data = await websocket.receive_bytes()
                        
                        # Send PCM audio to Gemini
                        await session.send(input={"data": data, "mime_type": "audio/pcm"}, end_of_turn=False)
                except WebSocketDisconnect:
                    print("Client disconnected")
                except Exception as e:
                    print(f"Error reading from client: {e}")
            
            async def receive_from_gemini():
                try:
                    while True:
                        # Re-subscribe after each completed turn for continuous listening
                        async for msg in session.receive():
                            server_content = getattr(msg, "server_content", None)
                            if server_content is not None:
                                model_turn = getattr(server_content, "model_turn", None)
                                if model_turn is not None:
                                    for part in getattr(model_turn, "parts", []):
                                        inline_data = getattr(part, "inline_data", None)
                                        # Forward audio to client; skip raw text (model reasoning)
                                        if inline_data and getattr(inline_data, "data", None):
                                            await websocket.send_bytes(inline_data.data)

                            # Handle tool calls
                            tool_call = getattr(msg, "tool_call", None)
                            if tool_call is not None:
                                for fc in getattr(tool_call, "function_calls", []):
                                    fn_name = fc.name
                                    fn_args = dict(fc.args) if fc.args else {}

                                    print(f"  [Tool Call] {fn_name}({json.dumps(fn_args, ensure_ascii=False)})")

                                    if fn_name == "end_session":
                                        print("User said goodbye — shutting down session.")
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
                                        # Graceful close (wait a bit to ensure it gets sent)
                                        await asyncio.sleep(2)
                                        await websocket.close()
                                        return

                                    result = await handle_tool_call(
                                        function_name=fn_name,
                                        args=fn_args,
                                        staff_id=staff_id,
                                    )
                                    print(f"  [Tool Result] {json.dumps(result, ensure_ascii=False)}")

                                    # Show concise action summary on the frontend
                                    summary = _action_summary(fn_name, fn_args)
                                    if summary:
                                        await websocket.send_text(json.dumps({"text": summary}))

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
                except Exception as e:
                    print(f"Error receiving from gemini: {e}")
            
            t1 = asyncio.create_task(receive_from_client())
            t2 = asyncio.create_task(receive_from_gemini())
            
            done, pending = await asyncio.wait([t1, t2], return_when=asyncio.FIRST_COMPLETED)
            for t in pending:
                t.cancel()

    except Exception as e:
        print(f"Error connecting to Gemini: {e}")
        try:
            await websocket.close()
        except:
            pass
