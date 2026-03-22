import asyncio
import os
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    with open("static/index.html") as f:
        return HTMLResponse(f.read())

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
    
    # We configure for AUDIO responses
    config = {"response_modalities": ["AUDIO"]}
    
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
                    # Async iterator for messages sent by the Live API
                    async for msg in session.receive():
                        server_content = getattr(msg, "server_content", None)
                        if server_content is not None:
                            model_turn = getattr(server_content, "model_turn", None)
                            if model_turn is not None:
                                for part in getattr(model_turn, "parts", []):
                                    inline_data = getattr(part, "inline_data", None)
                                    # Forward inline data to client
                                    if inline_data and getattr(inline_data, "data", None):
                                        await websocket.send_bytes(inline_data.data)
                                    # You can also handle text here if text is passed instead
                                    elif getattr(part, "text", None):
                                        await websocket.send_text(json.dumps({"text": part.text}))
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
