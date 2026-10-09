# Milo — Your orders, answered.

Milo is an AI-powered order intelligence assistant for ecommerce operations. Users ask natural-language questions about an order dataset (`orders.csv`), and Milo uses a native Gemini tool-calling loop coupled with deterministic Python functions to deliver accurate, mathematical facts—never hallucinations or fabricated data.

---

## Architecture & Data Flow

```text
[ Browser / React SPA ]
         │
         ▼  (HTTP POST /api/chat)
[ FastAPI Backend ]
         │
         ▼
[ Milo Agent (google-genai SDK) ] ◄───► [ Gemini 2.0 Flash ]
         │                                (Decides function call)
         ▼ (Dispatches deterministic execution)
[ Python Tools (pandas) ]
   ├── lookup_order()
   └── analyze_orders()
         │
         ▼ (Structured JSON result)
[ Gemini 2.0 Flash ] ──► Formulates concise natural-language response
         │
         ▼ (HTTP 200 { reply, error: null })
[ React Glassmorphism UI ]
```

---

## Features & Supported Inquiries

- **Order Lookup**: Retrieve real-time status, items, date, price, and customer details for any specific order ID (e.g. `ORD-1025`).
- **Revenue Analytics**: Deterministically calculate exact INR totals across categories, date ranges, cities, or statuses.
- **Order Metrics & Counts**: Count order volume by status (e.g. `Cancelled`, `Delivered`, `Returned`) or date window.
- **Customer Insights**: Aggregate transaction totals to rank top spenders with automatic tie handling.
- **Resilient Glassmorphism UI**: Dark purple/lavender glassmorphism theme (`#100B18`), responsive from 320px mobile to 1440px desktop, keyboard accessible, with zero inert controls.

---

## Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4, Lucide React, React-Markdown |
| **Backend** | Python 3.10+, FastAPI, Pydantic v2, Pandas, Uvicorn, Python-Dotenv |
| **AI / LLM** | Google Gemini (`gemini-2.0-flash`) via the official `google-genai` SDK |
| **Testing** | Pytest, Pytest-Asyncio, HTTPX, FastAPI TestClient |
| **Deployment** | Dockerless single-service deployment via Render (`render.yaml`) |

---

## Project Structure

```text
milo/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── agent.py          # Gemini function calling loop & custom exceptions
│   │   ├── config.py         # Environment variables & path resolution
│   │   ├── data_loader.py    # CSV loading, validation & helper columns
│   │   ├── main.py           # FastAPI routes, SPA serving & error handlers
│   │   ├── schemas.py        # Pydantic models for chat, health, & dataset
│   │   └── tools.py          # Deterministic tools (lookup & analyze) & Gemini declarations
│   ├── tests/
│   │   ├── conftest.py       # Fixtures & path setups
│   │   ├── test_agent.py     # Mocked Gemini agent loop & error mapping tests
│   │   ├── test_api.py       # FastAPI endpoint & validation tests
│   │   ├── test_data.py      # Schema integrity & DatasetError edge cases
│   │   └── test_tools.py     # Independent pandas mathematical parity tests
│   ├── requirements.txt      # Pinned Python dependencies
│   ├── run_live_qa.py        # Script for executing live QA against Gemini
│   └── verify_gemini.py      # Minimal script to test model function calling & quota
├── frontend/
│   ├── public/
│   │   ├── milo-logo.png     # Product brand logo
│   │   └── wallpaper.webp    # Optimized misty mountain wallpaper
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts     # Typed API client with 60s timeout & error mappings
│   │   ├── components/
│   │   │   ├── AppShell.tsx           # Glassmorphism window wrapper
│   │   │   ├── ChatWindow.tsx         # Message list with smart auto-scroll
│   │   │   ├── ErrorMessage.tsx       # Accessible error banner with retry
│   │   │   ├── FeatureCard.tsx        # Interactive capability cards
│   │   │   ├── Header.tsx             # Gemini pill & live health indicator
│   │   │   ├── LoadingIndicator.tsx   # "Analysing orders..." pulse indicator
│   │   │   ├── MessageBubble.tsx      # Markdown bubble with tool badges
│   │   │   ├── MessageComposer.tsx    # Multiline composer with 42px send button
│   │   │   ├── Sidebar.tsx            # Glowing orb, New Chat, & dataset card
│   │   │   ├── SuggestedQueryCard.tsx # Clickable query suggestion card
│   │   │   └── WelcomeScreen.tsx      # Initial brand landing state
│   │   ├── App.tsx           # State management & lifecycle polling
│   │   ├── index.css         # Design tokens & glassmorphism utilities
│   │   ├── main.tsx          # React entry point
│   │   └── types.ts          # TypeScript domain models
│   ├── package.json          # Frontend dependencies
│   └── vite.config.ts        # Vite config with dev proxy (/api -> :8000)
├── orders.csv                # Public 60-row dataset
├── package.json              # Root convenience scripts (PowerShell-safe)
├── render.yaml               # Render single-service deployment blueprint
├── README.md                 # Project documentation
└── WRITEUP.md                # Technical reflection & architecture writeup
```

---

## Prerequisites & Supported Runtimes

- **Python**: `3.10.x`, `3.11.x`, or `3.12.x`
- **Node.js**: `v18.x`, `v20.x`, or `v22.x`
- **npm**: `v9.x` or `v10.x`
- **OS**: Windows (PowerShell 5.1+ or PowerShell 7+), macOS, or Linux

---

## Local Setup (Windows PowerShell)

Open Windows PowerShell in the project root:

```powershell
# 1. Create Python virtual environment inside backend/
python -m venv backend/.venv

# 2. Activate virtual environment
.\backend\.venv\Scripts\Activate.ps1

# 3. Install backend dependencies
pip install -r backend/requirements.txt

# 4. Install root and frontend dependencies
npm install
npm install --prefix frontend

# 5. Set up environment variables
Copy-Item .env.example .env
# Edit .env and insert your real GEMINI_API_KEY
```

---

## Running the Application Locally

### Option A: Concurrent Development (Both Frontend & Backend)

```powershell
npm run dev
```

- Backend API: `http://localhost:8000`
- Frontend UI (Vite dev server with `/api` proxy): `http://localhost:5173`

### Option B: Separate Terminals

**Terminal 1 (Backend)**:
```powershell
.\backend\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000 --app-dir backend
```

**Terminal 2 (Frontend)**:
```powershell
npm run dev --prefix frontend
```

### Option C: Production Single-Service Mode (One Port)

```powershell
npm run build
uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend
```
Open `http://localhost:8000` in your browser. Both the React SPA and API are served from this single endpoint.

---

## Running Tests

Execute the complete test suite (64 tests across data integrity, tools, agent mocking, and API layer):

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests -v
```

### Real Test Output

```text
============================= test session starts =============================
platform win32 -- Python 3.10.11, pytest-8.3.4, pluggy-1.6.0
rootdir: C:\Users\georg\Milo - Torcue AI
plugins: anyio-4.15.1, asyncio-0.25.0
collected 64 items

backend/tests/test_agent.py::test_tool_dispatched_and_final_text_produced PASSED [  1%]
backend/tests/test_agent.py::test_multiple_tool_calls_parallel PASSED    [  3%]
backend/tests/test_agent.py::test_multiple_tool_calls_sequential PASSED  [  4%]
backend/tests/test_agent.py::test_invalid_args_passed_to_model PASSED    [  6%]
backend/tests/test_agent.py::test_missing_order_handled_truthfully PASSED [  7%]
backend/tests/test_agent.py::test_iteration_limit_stops_runaway_loop PASSED [  9%]
backend/tests/test_agent.py::test_provider_quota_error_mapped PASSED     [ 10%]
backend/tests/test_agent.py::test_safety_block_mapped PASSED             [ 12%]
backend/tests/test_agent.py::test_empty_message_rejected PASSED          [ 14%]
backend/tests/test_api.py::test_health_endpoint_healthy PASSED           [ 15%]
backend/tests/test_api.py::test_health_endpoint_data_not_ready PASSED    [ 17%]
backend/tests/test_api.py::test_dataset_endpoint_success PASSED          [ 18%]
backend/tests/test_api.py::test_dataset_endpoint_not_ready PASSED        [ 20%]
backend/tests/test_api.py::test_chat_valid_request PASSED                [ 21%]
backend/tests/test_api.py::test_chat_empty_and_whitespace_rejected PASSED [ 23%]
backend/tests/test_api.py::test_chat_exceeds_max_length PASSED           [ 25%]
backend/tests/test_api.py::test_chat_wrong_types PASSED                  [ 26%]
backend/tests/test_api.py::test_chat_malformed_json PASSED               [ 28%]
backend/tests/test_api.py::test_chat_provider_failure_handled PASSED     [ 29%]
backend/tests/test_api.py::test_chat_safety_block_handled PASSED         [ 31%]
backend/tests/test_api.py::test_chat_unexpected_exception_hides_stack_trace PASSED [ 32%]
backend/tests/test_data.py::test_csv_loads_60_rows PASSED                [ 34%]
backend/tests/test_data.py::test_csv_has_all_required_columns PASSED     [ 35%]
backend/tests/test_data.py::test_no_nulls_in_required_columns PASSED     [ 37%]
backend/tests/test_data.py::test_no_duplicate_ids PASSED                 [ 39%]
backend/tests/test_data.py::test_totals_match PASSED                     [ 40%]
backend/tests/test_data.py::test_date_range PASSED                       [ 42%]
backend/tests/test_data.py::test_status_values PASSED                    [ 43%]
backend/tests/test_data.py::test_category_values PASSED                  [ 45%]
backend/tests/test_data.py::test_sanity_ord_1025 PASSED                  [ 46%]
backend/tests/test_data.py::test_dataset_metadata PASSED                 [ 48%]
backend/tests/test_data.py::test_normalised_helper_columns PASSED        [ 50%]
backend/tests/test_data.py::test_validation_missing_file PASSED          [ 51%]
backend/tests/test_data.py::test_validation_empty_dataset PASSED         [ 53%]
backend/tests/test_data.py::test_validation_missing_column PASSED        [ 54%]
backend/tests/test_data.py::test_validation_duplicate_ids PASSED         [ 56%]
backend/tests/test_data.py::test_validation_bad_numeric_negative PASSED  [ 57%]
backend/tests/test_data.py::test_validation_bad_numeric_string PASSED    [ 59%]
backend/tests/test_data.py::test_validation_total_mismatch PASSED        [ 60%]
backend/tests/test_data.py::test_validation_invalid_date PASSED          [ 62%]
backend/tests/test_tools.py::TestFormatINR::test_small_number PASSED     [ 64%]
backend/tests/test_tools.py::TestFormatINR::test_four_digits PASSED      [ 65%]
backend/tests/test_tools.py::TestFormatINR::test_six_digits PASSED       [ 67%]
backend/tests/test_tools.py::TestFormatINR::test_large_number PASSED     [ 68%]
backend/tests/test_tools.py::TestLookupOrder::test_existing_order PASSED [ 70%]
backend/tests/test_tools.py::TestLookupOrder::test_nonexistent_order PASSED [ 71%]
backend/tests/test_tools.py::TestLookupOrder::test_empty_order_id PASSED [ 73%]
backend/tests/test_tools.py::TestLookupOrder::test_whitespace_padded_order_id PASSED [ 75%]
backend/tests/test_tools.py::TestLookupOrder::test_case_insensitive_lookup PASSED [ 76%]
backend/tests/test_tools.py::TestAnalyzeOrders::test_cancelled_count PASSED [ 78%]
backend/tests/test_tools.py::TestAnalyzeOrders::test_electronics_august_revenue PASSED [ 79%]
backend/tests/test_tools.py::TestAnalyzeOrders::test_top_customer PASSED [ 81%]
backend/tests/test_tools.py::TestAnalyzeOrders::test_boundary_dates_inclusive PASSED [ 82%]
backend/tests/test_tools.py::TestAnalyzeOrders::test_category_and_status_combined PASSED [ 84%]
backend/tests/test_tools.py::TestAnalyzeOrders::test_empty_result PASSED [ 85%]
backend/tests/test_tools.py::TestAnalyzeOrders::test_invalid_date_format PASSED [ 87%]
backend/tests/test_tools.py::TestAnalyzeOrders::test_start_greater_than_end_date PASSED [ 89%]
backend/tests/test_tools.py::TestAnalyzeOrders::test_unsupported_operation PASSED [ 90%]
backend/tests/test_tools.py::TestAnalyzeOrders::test_revenue_uses_total_inr_and_count_not_quantity_sum PASSED [ 92%]
backend/tests/test_tools.py::TestAnalyzeOrders::test_list_orders_truncation_and_fields PASSED [ 93%]
backend/tests/test_tools.py::TestDispatchTool::test_dispatch_lookup PASSED [ 95%]
backend/tests/test_tools.py::TestDispatchTool::test_dispatch_analyze PASSED [ 96%]
backend/tests/test_tools.py::TestDispatchTool::test_dispatch_unknown_tool PASSED [ 98%]
backend/tests/test_tools.py::TestDispatchTool::test_dispatch_invalid_args_type PASSED [100%]

======================= 64 passed in 2.46s =======================
```

---

## Metric Definitions

1. **Revenue**: Defined as the sum of recorded `total_inr` across matching rows. Unless a status filter is explicitly specified (e.g., "delivered only"), revenue includes all recorded statuses (including cancelled or returned orders) in line with recorded ledger totals.
2. **Order Count**: Counts the number of order transactions (rows), *not* the cumulative quantity of items sold.
3. **Top Customer**: Grouped by `customer_name` and ranked by cumulative `total_inr`. Any ties for highest spend are reported.
4. **Dates**: Date filters (`start_date`, `end_date`) are inclusive on both ends (`>=` start and `<=` end). When a user asks about "August", it resolves strictly to August 2026 (`2026-08-01` to `2026-08-31`) matching the dataset span.

---

## Environment Variables

| Variable | Description | Default | Required in Production |
|---|---|---|---|
| `GEMINI_API_KEY` | Google Gemini Developer API key | `""` | Yes |
| `GEMINI_MODEL` | Gemini model identifier | `gemini-2.0-flash` | No |
| `APP_ENV` | Application environment (`development` or `production`) | `development` | Yes (`production`) |
| `CSV_PATH` | Optional explicit path override for `orders.csv` | Relative `REPO_ROOT/orders.csv` | No |

---

## Render Deployment Steps

Milo is pre-configured for seamless single-service deployment on Render using [`render.yaml`](./render.yaml).

1. **Push Code to GitHub**:
   Ensure all changes are committed and pushed to a public GitHub repository:
   ```powershell
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git branch -M main
   git push -u origin main
   ```

2. **Connect to Render**:
   - Navigate to [Render Dashboard](https://dashboard.render.com/).
   - Click **New +** and select **Blueprint**.
   - Connect your GitHub repository. Render will automatically parse `render.yaml`.

3. **Configure Environment Variables**:
   - In the service configuration prompt, provide your `GEMINI_API_KEY`.
   - Confirm `GEMINI_MODEL` defaults to `gemini-2.0-flash` (or your preferred active model) and `APP_ENV` is set to `production`.

4. **Deploy**:
   - Click **Apply**.
   - Render automatically runs the build command:
     ```bash
     pip install -r backend/requirements.txt && npm install --prefix frontend && npm run build --prefix frontend
     ```
   - Render starts the application via:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend
     ```
   - Render monitors health via `/api/health`.

5. **Verify Cold Start**:
   - Free tier instances enter sleep mode after 15 minutes of inactivity. The initial cold request may take 30–50 seconds. Milo's frontend client incorporates an extended 60-second timeout to handle this gracefully.

---

## Known Limitations

- **Read-Only Architecture**: The assistant is strictly read-only; it cannot modify rows, cancel orders, process refunds, or alter order statuses.
- **Listing Pagination Limit**: The `list_orders` tool caps return records at 25 items with a `truncated: true` flag to prevent context window saturation.
- **Free Tier Cold Starts**: Render's free tier spins down after idle periods; the initial request requires cold-start spin-up time.

---

## Repository & Live Links

- **GitHub Repository**: https://github.com/georgeb74/milo-order-intelligence *(replace with your public repo)*
- **Live Deployment URL**: https://milo-torcue-ai.onrender.com *(replace with your active Render URL)*

