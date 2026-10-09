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
- **Bounded Tool Iterations**: The agent execution loop is strictly bounded by `MAX_TOOL_ITERATIONS = 5`. Runaway agent loops or repeated failed calls trigger `MiloIterationLimitError`.
- **Truthful Error Surfacing**: When a tool fails or an argument is invalid, the structured error dictionary is returned back into the tool response part. The model is instructed to truthfully convey the error to the user rather than hallucinating success.
- **Security & Secret Containment**: All error handlers catch internal exceptions and return sanitized messages, preventing stack trace or system path disclosure. API keys and file paths are never included in API responses.

---

## 4. Deployment Configuration

- **Single Service on Render**: Defined via [`render.yaml`](./render.yaml). During build, Render installs Python dependencies from `backend/requirements.txt` and compiles the React application into `frontend/dist`.
- **Unified Serving**: Uvicorn serves both the FastAPI endpoints (`/api/*`) and the static React SPA fallback from a single port. API routes take strict precedence; unmatched client-side routes fallback to `index.html`, while missing `/api/*` routes return 404 JSON instead of HTML.
- **Cold-Start Resilience**: The frontend client includes a 60-second `AbortController` timeout to gracefully absorb free-tier spin-up latency.

---

## 5. Improvements with More Time

1. **Server-Sent Events (SSE) Streaming**: Stream token chunks and display intermediate function execution steps in real-time.
2. **Interactive Data Tables**: Render `list_orders` results in sortable, filterable client-side grid tables with CSV export.
3. **Multi-Turn Chat History**: Persist session conversations in Redis or SQLite to support contextual follow-up questions.
4. **Authentication & Multi-Tenant Datasets**: Add OAuth2/JWT auth and support uploading customer-specific CSV datasets.
5. **Observability**: Integrate OpenTelemetry tracing to monitor LLM token consumption and tool dispatch latency.

---

## 6. AI Tools Used

In accordance with transparency requirements, the following AI tools were utilized during the development of Milo:
- **Google Antigravity**: Primary autonomous development agent used for architecture design, code generation, refactoring, and test execution.
- **Gemini 2.0 Flash / Gemini 3.8 Flash**: LLM used for function calling, natural-language reasoning, and tool evaluation.
