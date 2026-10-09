# Milo — Your orders, answered.

An AI-powered order intelligence assistant. Ask natural-language questions about order data and get accurate, tool-backed answers.

## Stack

| Layer    | Tech                                                    |
|----------|---------------------------------------------------------|
| Frontend | React + TypeScript + Vite + Tailwind CSS + lucide-react |
| Backend  | Python 3.12, FastAPI, pydantic, pandas                  |
| AI       | Gemini Developer API (google-genai SDK, function calling)|
| Tests    | pytest + httpx                                          |
| Hosting  | Render (single web service)                             |

## Local Development

### Prerequisites
- Python 3.12+
- Node.js 20+
- A Gemini API key

### Setup

```bash
# Clone
git clone <repo-url> && cd milo

# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install

# Environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY
```

### Run

```bash
# Terminal 1 — Backend
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend (proxies /api to backend)
cd frontend && npm run dev
```

### Test

```bash
cd backend && python -m pytest tests/ -v
```

## Deployment

Push to GitHub → connect to Render → set `GEMINI_API_KEY` in Render dashboard → deploy.

See `render.yaml` for the service configuration.

## Architecture

- **CSV loaded once at startup**, kept in memory — never reloaded per request
- **Gemini function calling** — the LLM decides which tool to call, Python executes it deterministically, Gemini explains the result
- **The LLM never does math** — all computation is in the tool functions
- **Indian currency formatting** — ₹1,12,282 style
