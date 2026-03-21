# Bakery Voice Assistant

Voice-powered checklist assistant for bakery staff. Uses Gemini Live API for real-time voice interaction to walk through sanitation and inventory checklists.

## Features

- **Voice-first** — talk naturally, the AI walks you through each item
- **Sanitation Checklist** — track cleaning tasks (prep surfaces, ovens, floors, etc.)
- **Inventory Checklist** — count and log ingredient stock levels (flour, sugar, eggs, etc.)
- **Persistent logging** — all completions, inventory counts, and cleaning logs saved to SQLite
- **Smart reminders** — ask what's left at any time

## Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Set up your API key:**
   ```bash
   cp .env.example .env
   # Edit .env and add your Google Gemini API key
   # Get one at https://aistudio.google.com/apikey
   ```

3. **Run the assistant:**
   ```bash
   uv run -m src
   ```

## Usage

- The assistant will greet you and ask which checklist to start with
- Confirm items as you complete them — the assistant marks them off
- For inventory items, say the count (e.g., "We have 12 bags of flour")
- Ask "What's left?" at any time to hear remaining items
- Use headphones to prevent echo feedback

## Project Structure

```
src/
├── main.py           # Entry point, Gemini Live API audio streaming
├── config.py         # Constants, model config, system prompt
├── db.py             # SQLite schema, seed data, query helpers
├── tools.py          # Gemini function declarations
└── tool_handlers.py  # Routes tool calls to database operations
```

## Tech Stack

- **Gemini Live API** — real-time voice streaming with function calling
- **PyAudio** — microphone input and speaker output
- **SQLite** — persistent checklist and log storage
- **uv** — Python package management
