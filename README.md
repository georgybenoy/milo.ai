<div align="center">

<img src="frontend/public/milo-logo.png" alt="Milo Logo" width="130" style="border-radius: 24px; box-shadow: 0 8px 32px rgba(180, 91, 255, 0.25);" />

# Milo
### *Your orders, answered.*

An AI-powered order intelligence assistant for ecommerce operations.<br>
Ask natural-language questions about orders, revenue, and customer spending with **100% deterministic mathematical accuracy**.

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-v4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Gemini](https://img.shields.io/badge/Google_Gemini-2.29+-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![Tests](https://img.shields.io/badge/Tests-64%20Passing-53D6A0?style=for-the-badge&logo=pytest&logoColor=white)](#-running-tests)
[![Deployment](https://img.shields.io/badge/Render-Live-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://milo-ai-tlx1.onrender.com)

[**💻 Localhost Setup**](#-localhost-setup--running-guide) • [**🌐 Live Application**](https://milo-ai-tlx1.onrender.com) • [**📁 GitHub Repository**](https://github.com/georgybenoy/milo.ai) • [**📝 Technical Writeup**](./WRITEUP.md)

</div>

---

> [!NOTE]
> **Core Principle**: The Large Language Model **never performs arithmetic** or fabricates order data. A Gemini model decides which backend tool to invoke, Python executes the tool deterministically over `orders.csv`, and Gemini synthesizes the structured result for the user.

---

## 🏛 Architecture & Data Flow

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Client Browser / React SPA                        │
│             (Glassmorphic Dark UI · #100B18 · Tabular INR Formatting)       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP POST /api/chat
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FastAPI Backend Server                           │
│        (Lifespan in-memory DataFrame · CORS · Sanitized Exception Shield)   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Milo Tool-Calling Agent                            │
│                 (google-genai SDK · Bounded Loop · Turn Limits)             │
│                                      │                                      │
│               User Intent            ▼              Tool Decision           │
│        ┌──────────────────────► [ Gemini ] ─────────────────────┐           │
│        │                                                        │           │
│        │ Natural Explanation                                    ▼           │
│        └────────────────────── [ Gemini ] ◄────────────── [ Execution ]     │
└──────────────────────────────────────────────────────────────┬──────────────┘
                                                               │
                                  ┌────────────────────────────┴─────────────┐
                                  ▼                                          ▼
                     lookup_order(order_id)                   analyze_orders(op, ...)
                     • Case-insensitive ID                    • count_orders
                     • Length & whitespace sanitization       • sum_revenue (exact INR)
                     • Not-found handled safely               • top_customer (tie-handling)
                                                              • list_orders (capped at 25)
```

1. **Deterministic Execution**: Pure pandas computations guarantee mathematical parity across currency sums, row counts, and date windows.
2. **Thought Signature Handling**: Built with `google-genai` SDK (v2.29+) to preserve reasoning state tokens across function-calling turns.
3. **Single-Port Production Serving**: FastAPI and Uvicorn directly serve the compiled React SPA with client-side fallback routes.

---

## ✨ Features & Supported Inquiries

- 🔍 **Precision Order Lookup**: Retrieve real-time status, customer, item count, date, and price for any order ID (e.g. `ORD-1025`).
- 💰 **Authoritative Revenue Analysis**: Deterministically calculate exact INR totals filtered by category, date range, city, or status.
- 📊 **Transaction Metrics**: Compute order volume counts across fulfillment statuses (`Delivered`, `Cancelled`, `Returned`).
- 🏆 **Customer Intelligence**: Aggregate and rank customer spend with automatic tie detection.
- 🛡 **Robust Safety Guardrails**: Nonexistent IDs (`ORD-9999`) return structured not-found responses; out-of-scope requests ("refund my order") are politely declined.
- 🎨 **Cinematic Glassmorphism UI**: Custom purple mountain backdrop, dark tokens (`#100B18`), glowing orb, custom logo tab favicon, and keyboard accessibility.

### 🧪 Benchmark Queries & Verified Results

| Inquiry Type | User Question | Verified Result | Dispatch Function |
|---|---|---|---|
| **Order Lookup** | *"What is the status of order ORD-1025?"* | *"The status of order ORD-1025 is **delivered**."* | `lookup_order(order_id="ORD-1025")` |
| **Status Count** | *"How many orders were cancelled?"* | *"There are **7** cancelled orders in the dataset."* | `analyze_orders(operation="count_orders", status="Cancelled")` |
| **Category Revenue** | *"What was the total revenue from Electronics in August?"* | *"The total revenue from Electronics for August 2026 was **₹27,189** (2026-08-01 to 2026-08-31)."* | `analyze_orders(operation="sum_revenue", category="Electronics", ...)` |
| **Top Customer** | *"Which customer has spent the most?"* | *"The customer who has spent the most across all recorded orders is **Rohan Das** with a total spend of **₹1,12,282** across 7 orders."* | `analyze_orders(operation="top_customer")` |
| **Missing Order** | *"What is the status of order ORD-9999?"* | *"Order ID ORD-9999 was not found in the dataset."* | `lookup_order(order_id="ORD-9999")` |
| **Out-of-Scope** | *"Please refund my order"* | Explains Milo is a read-only analytics assistant and cannot perform transactional mutations. | *None (Declined safely)* |

---

## 🛠 Tech Stack

| Layer | Technology | Details |
|---|---|---|
| **Frontend** | React 19, TypeScript, Vite 8.3 | High-performance SPA with client-side routing |
| **Design System** | Tailwind CSS v4, Lucide React | Custom dark glassmorphism theme (`#100B18`, `#B45BFF`) |
| **Backend** | Python 3.10+, FastAPI 0.115+, Uvicorn | Async web framework with static SPA fallback |
| **Data Engine** | Pandas 2.2+, Pydantic v2.14+ | In-memory dataset caching, strict schema validation |
| **AI / LLM** | Google Gemini (`google-genai` v2.29+) | Native tool calling with automatic protocol compliance |
| **Testing** | Pytest, Pytest-Asyncio, HTTPX | 64 unit and integration tests |
| **Deployment** | Render Web Service (`render.yaml`) | Dockerless single-service deployment |

---

## 📁 Project Structure

```text
milo/
├── backend/
│   ├── app/
│   │   ├── agent.py          # Gemini function-calling loop, bounded turns & custom exceptions
│   │   ├── config.py         # Environment variables & path resolution
│   │   ├── data_loader.py    # CSV loading, validation & helper columns
│   │   ├── main.py           # FastAPI routes, SPA serving & sanitized error handlers
│   │   ├── schemas.py        # Pydantic models for chat, health, dataset, & tools
│   │   └── tools.py          # Deterministic tools (lookup & analyze) & Gemini declarations
│   ├── tests/
│   │   ├── test_agent.py     # Mocked Gemini agent loop & error mapping tests
│   │   ├── test_api.py       # FastAPI endpoint, validation, & 4xx/5xx tests
│   │   ├── test_data.py      # Schema integrity & DatasetError edge cases
│   │   └── test_tools.py     # Mathematical parity & pandas aggregation tests
│   ├── requirements.txt      # Pinned Python dependencies
│   ├── run_live_qa.py        # Script for executing live QA against Gemini
│   └── verify_gemini.py      # Minimal verification script for model function calling
├── frontend/
│   ├── public/
│   │   ├── favicon.ico       # Multi-resolution branded tab icon (16x16 to 256x256)
│   │   ├── favicon-32x32.png # 32x32 crisp tab icon
│   │   ├── favicon.png       # 256x256 high-resolution logo
│   │   ├── milo-logo.png     # Official product brand logo
│   │   └── wallpaper.webp    # Optimized misty mountain wallpaper
│   ├── src/
│   │   ├── api/client.ts     # Typed API client with 60s timeout & error mappings
│   │   ├── components/       # Glassmorphism UI components (AppShell, Composer, Cards, etc.)
│   │   ├── App.tsx           # State management & lifecycle polling
│   │   ├── index.css         # Design tokens & glassmorphism utilities
│   │   └── main.tsx          # React entry point
│   ├── package.json          # Frontend dependencies
│   └── vite.config.ts        # Vite config with dev proxy (/api -> :8000)
├── orders.csv                # Public 60-row dataset
├── package.json              # Root convenience scripts (Windows PowerShell-safe)
├── render.yaml               # Render single-service deployment blueprint
├── README.md                 # Project documentation
└── WRITEUP.md                # Technical reflection & architecture writeup
```

---

## ⚡ Local Setup (Windows PowerShell)

### Prerequisites
- **Python**: `3.10.x`, `3.11.x`, or `3.12.x`
- **Node.js**: `v18.x`, `v20.x`, or `v22.x`
- **npm**: `v9.x` or `v10.x`

### Installation Steps

```powershell
# 1. Clone repository
git clone https://github.com/georgybenoy/milo.ai.git
cd milo.ai

# 2. Create Python virtual environment inside backend/
python -m venv backend/.venv

# 3. Activate virtual environment
.\backend\.venv\Scripts\Activate.ps1

# 4. Install backend dependencies
pip install -r backend/requirements.txt

# 5. Install root and frontend dependencies
npm install
npm install --prefix frontend

# 6. Configure environment variables
Copy-Item .env.example .env
# Edit .env and insert your real GEMINI_API_KEY
```

---

## 🚀 Running the Application

### Option A: Concurrent Development (Both Frontend & Backend)

```powershell
npm run dev
```

- **Frontend UI**: `http://localhost:5173` (Vite dev server with hot reload and `/api` proxy)
- **Backend API**: `http://localhost:8000`

> [!TIP]
> The root `npm run dev` script is cross-platform and automatically detects your Windows `.venv` Python executable.

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

## 🧪 Running Tests

Execute the complete test suite (64 tests across data integrity, tools, agent mocking, and API layer):

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests -v
```

<details open>
<summary><b>View Verified Pytest Execution Output (64 Passed)</b></summary>

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

======================= 64 passed in 2.49s =======================
```
</details>

---

## 📐 Metric Definitions

1. **Revenue**: Defined as the sum of recorded `total_inr` across matching rows. Unless a status filter is explicitly specified (e.g. "delivered only"), revenue includes all recorded statuses (including cancelled or returned orders) in line with recorded ledger totals.
2. **Order Count**: Counts the number of order transactions (rows), *not* the cumulative quantity of items sold.
3. **Top Customer**: Grouped by `customer_name` and ranked by cumulative `total_inr`. Any ties for highest spend are reported.
4. **Dates**: Date filters (`start_date`, `end_date`) are inclusive on both ends (`>=` start and `<=` end). When a user asks about "August", it resolves strictly to August 2026 (`2026-08-01` to `2026-08-31`) matching the dataset span.

---

## 🔐 Environment Variables

| Variable | Description | Default | Required in Production |
|---|---|---|:---:|
| `GEMINI_API_KEY` | Google Gemini Developer API key | `""` | **Yes** |
| `GEMINI_MODEL` | Gemini model identifier | `gemini-flash-lite-latest` | No |
| `APP_ENV` | Application environment (`development` or `production`) | `development` | **Yes** |
| `CSV_PATH` | Optional explicit path override for `orders.csv` | Relative `REPO_ROOT/orders.csv` | No |

---

## 💻 Localhost Setup & Running Guide

Follow this guide to run Milo completely on your local machine (`http://localhost:5173` or `http://localhost:8000`).

### 1. Prerequisites Check
Ensure you have the following installed on your machine:
- **Python**: `3.10+` (Verify with `python --version`)
- **Node.js**: `v18+` or `v20+` (Verify with `node --version`)
- **npm**: `v9+` or `v10+` (Verify with `npm --version`)
- **Git** (Verify with `git --version`)

---

### 2. Step-by-Step Installation

Clone the repository and install all dependencies:

```powershell
# 1. Clone the repository
git clone https://github.com/georgybenoy/milo.ai.git
cd milo.ai

# 2. Create the Python virtual environment inside backend/
python -m venv backend/.venv

# 3. Activate the virtual environment
# Windows PowerShell:
.\backend\.venv\Scripts\Activate.ps1
# macOS / Linux:
# source backend/.venv/bin/activate

# 4. Install backend Python dependencies
pip install -r backend/requirements.txt

# 5. Install root and frontend dependencies
npm install
npm install --prefix frontend
```

---

### 3. Environment Variable Configuration

Create your private `.env` file in the project root:

```powershell
Copy-Item .env.example .env
```

Open `.env` in your editor and provide your Gemini credentials:

```dotenv
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-flash-lite-latest
APP_ENV=development
```

> [!TIP]
> Get a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey). The `.env` file is git-ignored and stays strictly on your local machine.

---

### 4. Running the Local Development Servers

You have three options for running locally:

#### ⚡ Option A: Single-Command Concurrent Mode (Recommended)

Run both the FastAPI backend and Vite frontend together in a single terminal:

```powershell
npm run dev
```

- **Frontend UI**: [http://localhost:5173](http://localhost:5173) (Vite dev server with hot reload and automatic `/api` proxy)
- **Backend API**: [http://localhost:8000](http://localhost:8000)

*(The root script automatically locates your virtual environment's Python executable).*

#### 🖥 Option B: Running in Separate Terminals

If you prefer dedicated terminal windows for backend and frontend logs:

**Terminal 1 — Backend API**:
```powershell
.\backend\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000 --app-dir backend
```

**Terminal 2 — Frontend UI**:
```powershell
npm run dev --prefix frontend
```
Visit **[http://localhost:5173](http://localhost:5173)** in your browser.

#### 📦 Option C: Production Single-Port Mode (One Port)

Build the frontend bundle and serve everything (UI + API) directly from FastAPI on a single port:

```powershell
# Build React SPA into frontend/dist
npm run build

# Start FastAPI serving both API and static frontend
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend
```
Visit **[http://localhost:8000](http://localhost:8000)** in your browser.

---

### 5. Verifying Localhost Health & Connectivity

You can verify that your local backend and dataset are running properly via PowerShell:

```powershell
# Check health status
Invoke-RestMethod -Uri "http://localhost:8000/api/health"

# Expected Output:
# status : ok
# data_loaded : True
# ai_configured : True

# Check dataset metadata
Invoke-RestMethod -Uri "http://localhost:8000/api/dataset"

# Expected Output:
# record_count : 60
# start_date   : 2026-06-01
# end_date     : 2026-09-28
```

---

### 6. Localhost Troubleshooting

| Symptom | Cause | Solution |
|---|---|---|
| `[vite] http proxy error: ECONNREFUSED` | The backend on port 8000 is not running yet | Start the backend using Option A (`npm run dev`) or Option B |
| `Activate.ps1 cannot be loaded because running scripts is disabled` | PowerShell ExecutionPolicy restriction | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` |
| `GEMINI_API_KEY is not set` | Missing `.env` file | Copy `.env.example` to `.env` in the root folder and add your key |
| `Port 8000 already in use` | Another process is occupying the port | Run `Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force` |

---

## ⚠️ Known Limitations

- **Read-Only Architecture**: The assistant is strictly read-only; it cannot modify rows, cancel orders, process refunds, or alter order statuses.
- **Listing Pagination Limit**: The `list_orders` tool caps return records at 25 items with a `truncated: true` flag to prevent context window saturation.
- **Free Tier Cold Starts**: Render's free tier spins down after idle periods; the initial request requires cold-start spin-up time.

---

## 🔗 Repository & Live Links

- **GitHub Repository**: [https://github.com/georgybenoy/milo.ai](https://github.com/georgybenoy/milo.ai)
- **Live Deployment URL**: [https://milo-ai-tlx1.onrender.com](https://milo-ai-tlx1.onrender.com)
