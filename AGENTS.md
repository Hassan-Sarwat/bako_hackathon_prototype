# Bakery Voice Assistant — Project Overview

## Description

A voice-powered assistant built for bakery staff to streamline daily inventory logging and sanitation tracking. Instead of filling out paper checklists or typing into a spreadsheet, staff simply talk to the AI — it walks them through each item, updates the database in real time, and reminds them what's left to do.

Built for the Bako Hackathon.

## Problem

Bakery teams lose time and accuracy with manual checklist logging. Paper forms get lost, entries get skipped, and there's no easy audit trail. This assistant makes the process hands-free and conversational, improving speed and documentation quality.

## Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3.13** | Core language |
| **uv** | Package and environment management |
| **Gemini Live API** | Real-time voice streaming and conversation |
| **google-genai SDK** | Python client for Gemini API |
| **PyAudio** | Microphone input and speaker output |
| **SQLite** | Persistent storage for checklists and logs |
| **python-dotenv** | Environment variable management |

## Agent Tools

The voice assistant has 6 callable tools that Gemini invokes via function calling:

| Tool | Description |
|---|---|
| `mark_item_complete` | Mark a checklist item as done (with optional notes) |
| `mark_item_incomplete` | Undo a completion |
| `get_remaining_items` | List all incomplete items for a checklist |
| `add_inventory_count` | Log the quantity of an inventory item |
| `log_cleaning_activity` | Record a cleaning action and the area it was done in |
| `get_checklist_summary` | Get completed vs total count for a checklist |

## Architecture

```
src/
├── main.py           # Entry point — Gemini Live API session, async audio streaming, tool dispatch
├── config.py         # Model name, audio settings, system prompt
├── db.py             # SQLite schema, seed data, all CRUD operations
├── tools.py          # Gemini function declarations (tool definitions)
├── tool_handlers.py  # Maps tool calls from Gemini to database operations
├── __main__.py       # Allows `uv run -m src`
```

**Data flow:**
1. Microphone audio → Gemini Live API (streaming)
2. Gemini responds with audio and/or tool calls
3. Tool calls are dispatched to SQLite via `tool_handlers.py`
4. Tool results are sent back to Gemini, which generates a follow-up voice response
5. Audio response → speaker output

## What's Done

- [x] Project setup with uv and dependency management
- [x] SQLite database with schema for checklists, inventory logs, and cleaning logs
- [x] Seed data for sanitation checklist (8 items) and inventory checklist (8 items)
- [x] All 6 agent tools defined and wired up
- [x] Tool handler dispatch layer (async-safe)
- [x] Gemini Live API integration with real-time audio streaming
- [x] System prompt tuned for bakery checklist workflow
- [x] Checklist reset functionality for new days
- [x] Environment config with `.env.example`

## What's Next

- [ ] **UI** — Build a frontend interface to visualize checklist progress, inventory logs, and cleaning history in real time alongside the voice assistant
- [ ] Session management for shifts longer than 15 minutes (Live API session limit)
- [ ] Multi-user support (identify which staff member is logging)
- [ ] Export reports (daily cleaning log, inventory snapshot as CSV/PDF)
- [ ] Custom checklist items (add/remove items per bakery)
