# TripMate AI

TripMate AI is a FastAPI web app that uses a LangGraph multi-agent workflow to generate travel plans. It combines live flight status data, hotel/web search results, and an LLM-generated itinerary into a complete trip response that can be viewed in the browser, copied, or downloaded as a PDF.

## Features

- FastAPI backend with a browser-based travel planner UI
- LangGraph workflow with separate flight, hotel, itinerary, and final response agents
- OpenRouter LLM integration for itinerary generation
- Tavily search integration for hotel and travel research
- AviationStack integration for live flight data
- PostgreSQL checkpointing for conversation/thread state
- Nigeria/Lagos default flight origin, with support for natural-language routes
- Markdown rendering and PDF export in the frontend

## Tech Stack

- Python 3.14+
- FastAPI
- LangGraph
- LangChain
- OpenRouter
- Tavily
- AviationStack
- PostgreSQL
- Jinja2, HTML, CSS, JavaScript

## Project Structure

```text
Tripmate/
|-- app.py                 # FastAPI app and HTTP routes
|-- backend.py             # LangGraph agents and workflow
|-- tools/
|   |-- flight_tool.py     # AviationStack flight lookup and route parsing
|   `-- tavily_tool.py     # Tavily search helper
|-- templates/
|   `-- index.html         # Main UI template
|-- static/
|   |-- script.js          # Frontend API calls, copy, PDF download
|   `-- style.css          # Frontend styles
|-- pyproject.toml         # Project metadata and dependencies
|-- uv.lock                # Locked dependency versions
`-- README.md
```

## Requirements

Create a `.env` file in the project root with these values:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
TAVILY_API_KEY=your_tavily_api_key
AVIATIONSTACK_API_KEY=your_aviationstack_api_key
DATABASE_URL=your_postgresql_connection_url
DEFAULT_ORIGIN_IATA=LOS
```

`DEFAULT_ORIGIN_IATA` is optional. If it is not set, the app defaults to `LOS` for Lagos, Nigeria.

## Setup

Install dependencies with `uv`:

```bash
uv sync
```

Or install manually into an active virtual environment:

```bash
pip install -e .
```

## Run the App

Start the FastAPI server:

```bash
uv run python app.py
```

Or run with Uvicorn directly:

```bash
uv run uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

Open the app in your browser:

```text
http://127.0.0.1:8000
```

## API Endpoints

### Health Check

```http
GET /health
```

### Generate Travel Plan

```http
POST /api/travel
Content-Type: application/json
```

Request body:

```json
{
  "message": "Plan a complete 7 days Japan trip from Nigeria including flights, hotels and sightseeing.",
  "thread_id": null
}
```

Response includes:

- `thread_id`
- `answer`
- `flight_results`
- `hotel_results`
- `itinerary`
- `llm_calls`

## Example Prompts

- `Plan a complete 7 days Japan trip from Nigeria including flights, hotels and sightseeing under 2 million naira.`
- `Plan a 5 days Dubai trip from Lagos with flights, hotels and sightseeing.`
- `Plan a 7 days Thailand trip from Nigeria with budget hotels and sightseeing.`
- `Give me all country flight info.`

## Notes

- AviationStack provides live/status flight data, not ticket fare pricing.
- PostgreSQL is required because LangGraph checkpointing is configured with `PostgresSaver`.
- The frontend stores the current `thread_id` in browser local storage so follow-up requests can continue the same thread.
