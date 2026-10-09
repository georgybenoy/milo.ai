# Technical Writeup: Milo Order Intelligence Assistant

## 1. Architecture & Data Flow

Milo is built as a single-service, decoupled full-stack application designed to answer questions about ecommerce orders deterministically:

```text
User Question ──► Vite React UI ──► FastAPI (POST /api/chat)
                                           │
                                           ▼
                                 Gemini 2.0 Flash
                                (google-genai SDK)
                                           │
                                  [Native Tool Call]
                                           ▼
                                 Python / Pandas Tools
                             ┌─────────────┴─────────────┐
                             ▼                           ▼
                     lookup_order()              analyze_orders()
                             └─────────────┬─────────────┘
                                           ▼
                                  Structured Result
                                           ▼
                                 Gemini Explanation
                                           ▼
                                  Frontend Rendering
```

1. **State Persistence**: The CSV dataset (`orders.csv`, 60 rows) is parsed and validated once at backend startup during the FastAPI `lifespan` handler. It resides in memory as an immutable Pandas DataFrame, avoiding disk I/O on request paths.
2. **Deterministic Computation**: The LLM is never allowed to calculate revenue sums, order counts, or customer rankings directly. All math is performed by Python functions operating on the DataFrame.

---

## 2. Tool Routing: `lookup_order` vs `analyze_orders`

The agent provides two tightly scoped tools, with clear routing rules encoded directly into the Gemini tool schemas and system instructions:

- **`lookup_order(order_id)`**:
  - **Routing Rule**: Selected whenever the user provides or asks about a specific order identifier (e.g. `ORD-1025`).
  - **Behavior**: Case-insensitive exact ID match, strips whitespace, validates length (≤32 chars). Missing orders return `{found: false, order: null}`, explicitly preventing the LLM from inventing placeholder records.
- **`analyze_orders(operation, ...filters)`**:
  - **Routing Rule**: Selected for all aggregates, counts, financial totals, customer rankings, or multi-order listings.
  - **Supported Operations**:
    - `count_orders`: Counts matching rows (transactions), not cumulative item quantities.
    - `sum_revenue`: Sums recorded `total_inr`. Unless a status filter is requested, revenue sums all recorded orders (including cancelled and returned).
    - `top_customer`: Groups by customer and sums spend, correctly identifying top spenders and reporting ties.
    - `list_orders`: Returns matching rows, capped at 25 items with a `truncated: true` flag to prevent context window saturation.

---

## 3. Guardrails & Safety Engineering

- **Strict Validation**: The data loader validates file existence, schema completeness (all 11 columns), absence of duplicates or nulls, valid calendar dates, positive quantities/prices, and mathematical consistency (`total_inr == quantity * unit_price_inr`). If corrupted, the app raises `DatasetError` and reports `data-not-ready` instead of treating it as empty.
- **Deterministic Math**: The LLM is strictly prohibited from performing manual arithmetic or guessing totals. All statistics, currency calculations, date windowing, and rankings are computed by pure Python functions and passed back as immutable facts.
- **Bounded Tool Iterations**: The agent execution loop is strictly bounded by `MAX_TOOL_ITERATIONS = 5`. Runaway agent loops or repeated failed calls trigger `MiloIterationLimitError` and yield safe fallback messaging.
- **Missing-Result & Scope Handling**: When an order is not found (e.g. `ORD-9999`), tools return `{found: false, order: null}`, and the system prompt explicitly forbids inventing placeholder orders. For action-oriented requests outside of order intelligence (e.g. "refund my order", "cancel order"), Milo politely explains it is a read-only analytics assistant and cannot perform mutations.
- **Security & Secret Containment**: All error handlers catch internal exceptions and return sanitized messages, preventing stack trace or system path disclosure. API keys, credentials, and filesystem paths are never serialized in API responses or committed to source control.

---

## 4. Deployment Configuration

- **Single Service on Render**: Defined via [`render.yaml`](./render.yaml). During build, Render installs Python dependencies from `backend/requirements.txt` and compiles the React application into `frontend/dist`.
- **Unified Serving**: Uvicorn serves both the FastAPI endpoints (`/api/*`) and the static React SPA fallback from a single port. API routes take strict precedence; unmatched client-side routes fallback to `index.html`, while missing `/api/*` routes return 404 JSON instead of HTML.
- **Cold-Start Resilience**: The frontend client includes a 60-second `AbortController` timeout to gracefully absorb free-tier spin-up latency.

---

## 5. Improvements with More Time

1. **Server-Sent Events (SSE) Streaming**: Stream token chunks to provide sub-second time-to-first-token feedback.
2. **Tool-Step Display**: Visual collapsible pills in the UI displaying intermediate function calls, arguments, and return payloads.
3. **Interactive Data Tables & Pagination**: Rich data tables for `list_orders` results featuring client-side sorting, column filtering, pagination, and CSV export.
4. **Session Persistence**: Storing multi-turn conversation history in SQLite or Redis to support conversational context across turns.
5. **Authentication & Multi-Tenancy**: User authentication (OAuth2 / JWT) and tenant isolation for organizations uploading proprietary order databases.
6. **Observability & Monitoring**: OpenTelemetry tracing and structured logging to track token usage, latency percentiles, and provider error rates.
7. **Live Gemini Integration Tests**: Automated CI/CD pipeline tests executing live tool-calling assertions against Gemini test environments to catch upstream model behavior shifts.

---

## 6. AI Tools Used

In accordance with transparency requirements, the following AI tools were utilized during the development of Milo:
- **Google Antigravity**: Primary autonomous development agent used for codebase implementation, full-stack scaffolding, refactoring, and automated test execution.
- **Gemini (via Google GenAI SDK)**: Large language model powering the runtime application for intent parsing, native function calling, and natural-language synthesis.
- **ChatGPT & Claude**: Utilized during the preparatory phases for architectural planning, requirements decomposition, and system prompt engineering/generation.

