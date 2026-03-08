# Facts-Only Mutual Fund Assistant — RAG Architecture

## System Overview

A production-grade, Retrieval-Augmented Generation chatbot that answers **factual queries only** about 10 Quant Mutual Fund schemes listed on Groww.in. The architecture has **9 phases** (Phase 1 through Phase 8) plus a **Scheduler** for daily data refresh. The system is designed around strict compliance guardrails: no investment advice, no PII collection, and every response cites its exact source URL.

---

## Architecture Diagram (Text)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              PHASE 1 — DATA INGESTION (Offline / Scheduled)                 │
│     Scrape → Parse → Chunk → Embed → Index → Vector Store                   │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │  populates Vector Store (used by Phase 4 at runtime)
                               │
┌─────────────────────────────────────────────────────────────────────────────┐
│              SCHEDULER — Daily Data Refresh                                  │
│     Triggers Phase 1 pipeline daily (e.g. 6 AM IST)                         │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────────────────┐
│              PHASE 8 — FRONTEND (Next.js + TypeScript on Vercel)            │
│         Sidebar + Chat: History | Fund Dropdown | Chat Interface            │
│         Sends {query, active_fund, conversation_id} to Backend              │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │  User Query
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 2 — GUARDRAIL LAYER                           │
│                                                                             │
│  ┌───────────────┐   ┌──────────────────┐   ┌────────────────────────────┐ │
│  │  PII Detector  │   │  Intent Classifier│   │  Advice / Comparison Gate │ │
│  │  (regex + NER) │   │  (LLM zero-shot)  │   │  (keyword + LLM check)   │ │
│  └───────┬───────┘   └────────┬─────────┘   └────────────┬───────────────┘ │
│          │                    │                           │                  │
│          ▼                    ▼                           ▼                  │
│    PII found?           Is it factual?          Advice request?              │
│    → BLOCK & warn       → PASS                  → BLOCK & redirect          │
│                         Off-topic?                                           │
│                         → BLOCK & redirect                                  │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │  Clean, validated query
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PHASE 3 — QUERY PROCESSING                             │
│                                                                             │
│  ┌─────────────────────┐   ┌──────────────────────────────────────────┐    │
│  │  Query Rewriter      │   │  Fund Name Resolver                     │    │
│  │  (normalize slang,   │   │  (map "small cap quant" → exact scheme  │    │
│  │   fix typos, expand  │   │   name + canonical URL)                 │    │
│  │   abbreviations)     │   │                                         │    │
│  └──────────┬──────────┘   └──────────────────┬───────────────────────┘    │
│             │                                  │                            │
│             └──────────────┬───────────────────┘                            │
│                            ▼                                                │
│                   Enriched query + target fund metadata                     │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PHASE 4 — RETRIEVAL ENGINE                             │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     Vector Store (ChromaDB)                           │  │
│  │                                                                       │  │
│  │   Each document chunk stores:                                         │  │
│  │     • chunk_text          (the actual content)                        │  │
│  │     • source_url          (one of the 10 allowed URLs)                │  │
│  │     • fund_name           (canonical scheme name)                     │  │
│  │     • section             (overview / holdings / returns / risk etc.) │  │
│  │     • scraped_timestamp   (when the data was fetched)                 │  │
│  │                                                                       │  │
│  └──────────────────────────────┬───────────────────────────────────────┘  │
│                                 │                                           │
│  Query embedding ──► Similarity search (top-k=5) ──► Re-ranker (optional) │
│                                 │                                           │
│                                 ▼                                           │
│                    Retrieved chunks + metadata                              │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   PHASE 5 — RESPONSE GENERATION                            │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  System Prompt (hardcoded rules)                                    │    │
│  │  ─────────────────────────────                                      │    │
│  │  • You are a factual assistant for Quant Mutual Funds on Groww.     │    │
│  │  • ONLY use the retrieved context below. Never use training data.   │    │
│  │  • Never give investment advice, comparisons, or predictions.       │    │
│  │  • Max 5 sentences. Neutral tone.                                   │    │
│  │  • End every answer with: "Last updated from sources: <URL>"        │    │
│  │  • If context is insufficient, say "I don't have that information." │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  LLM (Groq API)                                                            │
│     Input  = system prompt + retrieved chunks + user query                  │
│     Output = factual response (≤5 sentences) + citation URL                │
│                                                                             │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                  PHASE 6 — OUTPUT GUARDRAIL & FORMATTING                   │
│  ┌────────────────────┐  ┌──────────────────┐  ┌───────────────────────┐  │
│  │ Post-gen PII scan   │  │ Advice leak check │  │ Citation validator    │  │
│  └────────┬───────────┘  └────────┬─────────┘  └──────────┬────────────┘  │
│           └───────────────────────┼─────────────────────────┘              │
│                                   ▼                                        │
│                      Validated, formatted response                         │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 8 — FRONTEND                                  │
│     Users ask questions → view responses (with citation + fund context)    │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │  POST /query {query, active_fund, conversation_id}
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 7 — BACKEND (FastAPI)                          │
│     Hosts Phases 2–6; exposes /query, /mutual-funds endpoints              │
│     Prepends active_fund to query for fund resolution                      │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │  {answer, citations, conversation_id}
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 8 — FRONTEND                                   │
│     Renders response in chat UI; persists conversation state               │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
                        Return to User
```

---

## Phase-by-Phase Design

---

### Phase 1 — Data Ingestion Pipeline (Offline / Scheduled)

**Purpose:** Scrape, parse, chunk, embed, and index content from the 10 allowed Groww URLs.

| Step | Detail |
|------|--------|
| **1.1 Scheduler** | Run the ingestion pipeline **daily** using a scheduler (e.g., cron, APScheduler). Schedule at a fixed time (e.g., 6 AM IST) to capture NAV/AUM updates without overlapping runs. |
| **1.2 Web Scraper** | Use **Playwright** headless browser to fetch and download documents from each of the 10 URLs. Groww pages are JS-rendered; Playwright handles dynamic content. **Polite scraping:** implement request throttling (e.g., delay between requests), caching (avoid re-downloading unchanged pages), and duplicate-download checks (e.g., by URL + last-modified or content hash) so the scraper does not hit the website repeatedly and risk getting blocked. |
| **1.3 HTML Parser** | Extract structured sections: Fund Name, NAV, Expense Ratio, AUM, Fund Manager, Category, Risk Rating, Holdings (top 10), Returns table, Investment Objective, Exit Load, Min Investment, Fund House info. |
| **1.4 Section-Aware Chunking** | Split content **by logical section** (not arbitrary token windows). Each chunk retains its `section` label, `fund_name`, and `source_url`. Target chunk size: 200–400 tokens with 50-token overlap for boundary sections. |
| **1.5 Embedding** | Generate vector embeddings using `text-embedding-3-small` (OpenAI) or `sentence-transformers/all-MiniLM-L6-v2` (open-source). |
| **1.6 Vector Store Indexing** | Store chunks + metadata in the vector database (see Phase 4). Each record: `{id, chunk_text, embedding, source_url, fund_name, section, scraped_at}`. |

**Output of Phase 1**
- Populated **ChromaDB** vector store with embedded document chunks and metadata.
- Cache/store of raw or parsed content (if used for caching) and `scraped_at` timestamps per source URL for staleness tracking.

**Allowed Source URLs (exhaustive, hardcoded):**

| # | Fund | URL |
|---|------|-----|
| 1 | Quant Small Cap Fund | `https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth` |
| 2 | Quant Infrastructure Fund | `https://groww.in/mutual-funds/quant-infrastructure-fund-direct-growth` |
| 3 | Quant Flexi Cap Fund | `https://groww.in/mutual-funds/quant-flexi-cap-fund-direct-growth` |
| 4 | Quant ELSS Tax Saver Fund | `https://groww.in/mutual-funds/quant-elss-tax-saver-fund-direct-growth` |
| 5 | Quant Large Cap Fund | `https://groww.in/mutual-funds/quant-large-cap-fund-direct-growth` |
| 6 | Quant ESG Integration Strategy Fund | `https://groww.in/mutual-funds/quant-esg-integration-strategy-fund-direct-growth` |
| 7 | Quant Mid Cap Fund | `https://groww.in/mutual-funds/quant-mid-cap-fund-direct-growth` |
| 8 | Quant Multi Cap Fund | `https://groww.in/mutual-funds/quant-multi-cap-fund-direct-growth` |
| 9 | Quant Aggressive Hybrid Fund | `https://groww.in/mutual-funds/quant-aggressive-hybrid-fund-direct-growth` |
| 10 | Quant Focused Fund | `https://groww.in/mutual-funds/quant-focused-fund-direct-growth` |

---

### Scheduler — Daily Data Refresh

**Purpose:** Run the Data Ingestion pipeline (Phase 1) on a fixed schedule so that the vector store and any cached fund data stay up to date with the 10 Groww scheme pages.

| Aspect | Detail |
|--------|--------|
| **Schedule** | **Daily** at a fixed time (e.g. 6:00 AM IST) to capture NAV/AUM and content updates without overlapping runs. |
| **Implementation** | Use a scheduler such as **cron** (Linux/macOS) or **APScheduler** (Python). The job invokes the Phase 1 pipeline (scrape → parse → chunk → embed → index → vector store). |
| **Scope** | One full run per day over all 10 allowed URLs; optional: incremental or change-based refresh if supported by the ingestion logic. |
| **Failure handling** | Log failures and optionally alert; consider retries or a follow-up run if the daily run fails. |

**Output of Scheduler**
- No direct artifact; the scheduler ensures that Phase 1 runs daily, so the **output** is an up-to-date vector store and data store for use by the Backend (Phase 7) at runtime.

---

### Phase 2 — Input Guardrail Layer (Runtime)

**Purpose:** Intercept and classify every user query before it reaches the retrieval engine.

#### 2.1 PII Detector
- **Regex patterns** for: PAN (`[A-Z]{5}[0-9]{4}[A-Z]`), Aadhaar (`\d{4}\s?\d{4}\s?\d{4}`), phone numbers, email addresses, bank account patterns.
- **NER model** (spaCy or a lightweight transformer) as a secondary check for names, addresses.
- **Action on detection:** Immediately return a canned response: *"I cannot process personal information. Please do not share sensitive details like PAN, Aadhaar, or bank information."* Query is **not forwarded**.

#### 2.2 Intent Classifier
Classify the query into one of:
| Intent | Action |
|--------|--------|
| `factual_query` | Proceed to retrieval |
| `investment_advice` | Block → canned redirect |
| `comparison_request` | Block → canned redirect with fund page links |
| `greeting / chitchat` | Return a brief greeting + scope reminder |
| `off_topic` | Block → *"I can only answer factual questions about the listed Quant Mutual Funds."* |

- **Implementation:** Zero-shot LLM classification or a fine-tuned lightweight classifier (DistilBERT).

#### 2.3 Advice / Comparison Gate
- Keyword triggers: `"should I invest"`, `"which is better"`, `"recommend"`, `"best fund"`, `"compare returns"`, `"will it go up"`, etc.
- LLM double-check on borderline queries.
- **Action:** *"I'm unable to provide investment advice or compare fund performance. You can review the fund details here: [URL]."*

**Output of Phase 2**
- Either a **clean, validated query** (and intent label) passed to Phase 3, or a **canned response** (PII warning, advice redirect, off-topic message, or greeting) returned directly to the user with no further processing.

---

### Phase 3 — Query Processing (Runtime)

**Purpose:** Normalize and enrich the validated query for optimal retrieval.

#### 3.1 Query Rewriter
- Fix common typos (`"expnse ratio"` → `"expense ratio"`)
- Expand abbreviations (`"NAV"` → `"Net Asset Value (NAV)"`, `"AUM"` → `"Assets Under Management (AUM)"`)
- Normalize fund name references (`"small cap quant"` → `"Quant Small Cap Fund Direct Plan Growth"`)

#### 3.2 Fund Name Resolver
- Maintain a **lookup table** mapping aliases/partial names to canonical fund names + URLs.
- If the query doesn't mention a specific fund, ask the user to clarify.
- If multiple funds are mentioned, handle each independently (or limit to one per query for simplicity in v1).

#### 3.3 Metadata Filter Construction
- Build a pre-filter: `fund_name = <resolved_name>` so the vector search is scoped to the correct fund.
- Optionally filter by `section` if the query clearly targets a specific section (e.g., "holdings" → `section = "holdings"`).

**Output of Phase 3**
- **Enriched query** (rewritten, normalized) and **target fund metadata** (canonical fund name, optional section filter) used as input to the retrieval engine.

---

### Phase 4 — Retrieval Engine (Runtime)

**Purpose:** Fetch the most relevant chunks from the vector store.

**Vector Store:** Use **ChromaDB** as the vector database to store and query embeddings. ChromaDB is used for similarity search over the ingested document chunks.

#### 4.1 Embedding the Query
- Use the **same embedding model** as ingestion (critical for alignment).
- Embed the rewritten query.

#### 4.2 Similarity Search
- **Top-k = 5** chunks, filtered by `fund_name` metadata.
- Distance metric: **cosine similarity**.
- Minimum similarity threshold: **0.7** — if no chunk exceeds this, return *"I don't have enough information to answer that."*

#### 4.3 Re-Ranker (Optional, Phase 4 enhancement)
- Use a cross-encoder re-ranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`) to re-score the top-k results.
- Improves precision for nuanced queries.

#### 4.4 Context Assembly
- Concatenate top chunks into a context block.
- Attach `source_url` and `scraped_at` metadata for citation.
- Cap total context to **~1500 tokens** to leave room for the system prompt and response.

**Output of Phase 4**
- **Retrieved context**: ranked list of top-k chunks with `chunk_text`, `source_url`, `fund_name`, and `scraped_at`, assembled into a single context string (and optional metadata structure) for the LLM.

---

### Phase 5 — Response Generation (Runtime)

**Purpose:** Generate a factual, cited, concise answer using a single LLM call per user query.

**LLM inference:** Use the **Groq API** for LLM inference when generating responses. Store the Groq API key in a **`.env`** file to securely manage credentials; the application must read the API key from **environment variables** (e.g., `GROQ_API_KEY`) and must not hardcode it. Ensure **only one LLM call is made per user query**: retrieve relevant context first (Phase 4), then send that context and the user query in a **single prompt** to the LLM—avoid multiple sequential LLM calls.

#### 5.1 System Prompt (Hardcoded, Non-Overridable)

```text
You are a factual assistant for Quant Mutual Fund schemes listed on Groww.in.

STRICT RULES:
1. ONLY use the CONTEXT provided below. Do NOT use your training knowledge.
2. If the context does not contain the answer, say: "I don't have that information
   from the available sources."
3. NEVER provide investment advice, fund recommendations, return comparisons,
   portfolio suggestions, or market predictions.
4. Keep responses to a MAXIMUM of 5 sentences.
5. Use a factual, neutral tone.
6. End every response with: "Last updated from sources: <source_url>"
   where <source_url> is the specific URL the information came from.
7. If a user shares personal information, respond: "I cannot process personal
   information. Please avoid sharing sensitive details."
```

#### 5.2 LLM (Groq API)
- Use **Groq API** for inference (e.g., Llama or Mixture-of-Experts models available on Groq).
- API key: stored in `.env`, read via environment variables (e.g., `GROQ_API_KEY`).
- **Single call per query:** context from Phase 4 and the user query are combined into one prompt; no multi-turn or sequential LLM calls for a single answer.

#### 5.3 Prompt Assembly

```
[System Prompt]

CONTEXT:
---
{chunk_1_text}
Source: {chunk_1_url}
---
{chunk_2_text}
Source: {chunk_2_url}
---

USER QUESTION: {user_query}

ANSWER:
```

#### 5.4 Generation Parameters
- `temperature = 0.0` (deterministic, factual)
- `max_tokens = 300`
- `top_p = 1.0`

**Output of Phase 5**
- **Raw LLM response**: a factual, cited answer (≤5 sentences) including the “Last updated from sources: <URL>” line, ready for Phase 6 validation and formatting.

---

### Phase 6 — Output Guardrail & Formatting (Runtime)

**Purpose:** Validate the LLM's output before it reaches the user.

#### 6.1 Post-Generation PII Scan
- Run the same PII regex + NER pipeline on the generated response.
- Strip or block if PII is detected (defense-in-depth).

#### 6.2 Advice Leak Detection
- Scan for advisory language: `"you should"`, `"I recommend"`, `"invest in"`, `"better returns"`, etc.
- If detected, replace with the canned redirect response.

#### 6.3 Citation Validator
- Verify the `source_url` in the response is in the **allowed URL whitelist**.
- If the LLM hallucinated a URL, replace it with the correct one from chunk metadata.

#### 6.4 Response Formatter
- Enforce the 5-sentence cap (truncate gracefully if exceeded).
- Append `Last updated from sources: <URL>` if the LLM omitted it.
- Format for the UI (markdown, links, etc.).

**Output of Phase 6**
- **Validated, formatted response** safe to display: no PII or advice leaks, citation URL whitelisted, length and format enforced. This is passed to the UI Layer for display.

---

### Phase 7 — Backend

**Purpose:** Host the runtime RAG pipeline (Phases 2–6) and expose an API so that the Frontend can send user queries and receive factual, cited responses.

| Aspect | Detail |
|--------|--------|
| **Role** | Application server (e.g. **FastAPI**) that receives the user query from the Frontend, runs Input Guardrail (Phase 2) → Query Processing (Phase 3) → Retrieval (Phase 4) → Response Generation (Phase 5) → Output Guardrail (Phase 6), and returns the validated response. |
| **API** | Expose: `POST /query` (accepts `{query, active_fund, conversation_id}`, returns `{answer, citations, conversation_id}`), `GET /mutual-funds` (returns list of supported fund names), and optionally `GET /conversations` / `POST /conversations`. When `active_fund` is provided, prepend it to the query so downstream phases resolve the fund correctly. |
| **State** | Stateless per request; no server-side session or PII storage. The `active_fund` and `conversation_id` come from the client on each request. Reads from the vector store and configuration (e.g. Groq API key from environment). |
| **Deployment** | Runs as a separate process or container from the Frontend; can be scaled independently. |

**Output of Phase 7**
- **API response** (e.g. JSON) containing the formatted answer and source URL, or a guardrail message (PII warning, advice redirect, off-topic, etc.), consumed by the Frontend (Phase 8).

---

### Phase 8 — Frontend (Apple Mac-Inspired Chatbot UI)

**Purpose:** Provide a clean, minimal chatbot interface for querying Quant Mutual Fund facts. The design follows Apple macOS aesthetics — generous whitespace, subtle shadows, system fonts, rounded surfaces, and a restrained colour palette.

---

#### 8.1 Technology Stack

| Technology | Role |
|------------|------|
| **Next.js 16 + TypeScript** | React-based frontend framework with SSR/SSG, deployed on Vercel |
| **TailwindCSS v4** | Utility-first CSS framework for Apple macOS-inspired design system |
| **Vercel** | Edge-optimised hosting for the frontend (automatic CI/CD from GitHub) |

---

#### 8.2 UI Layout — Sidebar + Chat

```
┌─────────────────┬───────────────────────────────────────────┐
│                  │                                           │
│  Chat History    │           Chat Interface                  │
│  (Sidebar)       │                                           │
│                  │   ┌─────────────────────────────────┐     │
│  ● New Chat      │   │  Fund: [dropdown ▾] [✕ Clear]   │     │
│  ● Prev chats    │   └─────────────────────────────────┘     │
│                  │                                           │
│  Data refreshed: │   💬  User message                       │
│  07 Mar 2026     │   🤖  Assistant reply + citation          │
│                  │   ...                                     │
│                  │                                           │
│                  │   ┌─────────────────────────────────┐     │
│                  │   │  Ask about Quant Mutual Funds…   │     │
│                  │   └─────────────────────────────────┘     │
└─────────────────┴───────────────────────────────────────────┘
```

There is **no right panel**. Fund selection is done via an inline dropdown above the chat area.

---

#### 8.3 Sidebar — Conversation History

| Feature | Detail |
|---------|--------|
| **New Chat button** | Starts a fresh conversation (no messages, no active fund). |
| **Conversation list** | Previous conversations, each showing title and optional fund tag. Sorted newest-first. Only conversations with messages are shown. |
| **Switch conversations** | Clicking restores messages and selected fund. |
| **Data refresh timestamp** | Displays last scheduler run date. |

**Conversation data model:**
```
{
  conversation_id: string,
  title: string,
  messages: Message[],
  active_fund: string | null,
  created_at: string,
  updated_at: string
}
```

---

#### 8.4 Chat Interface (Main Area)

| Feature | Detail |
|---------|--------|
| **Fund dropdown** | A `<select>` dropdown at the top of the chat area listing all 10 funds (fetched from `GET /mutual-funds`) plus a "No fund selected" option. Selecting a fund sets `active_fund` for the conversation. A "Clear" button resets it to `null`. |
| **Message display** | User and assistant message bubbles with citations (clickable source links). |
| **Input box** | Always-visible chat input at the bottom. Enter-to-send. |
| **Sample questions** | On new/empty chats, display 5 random sample questions the user can click to start a conversation. |

**Fund dropdown behaviour:**
- When a fund is selected, all queries in that conversation are scoped to that fund automatically (the user does not need to name the fund in their message).
- When "No fund selected" is chosen, the user must reference the fund explicitly in their query.
- The dropdown selection persists per conversation — switching conversations restores the previously selected fund.

**Message data model:**
```
{
  id: string,
  role: "user" | "assistant",
  content: string,
  citations?: string[],
  created_at: string
}
```

---

#### 8.5 Fund Context Memory

Each conversation maintains its own `active_fund`. When a fund is selected via the dropdown, follow-up queries are automatically scoped to that fund.

**Example:**
1. User selects "Quant Small Cap Fund" from dropdown → `active_fund = "Quant Small Cap Fund"`
2. User asks "What is the NAV?" → Frontend sends query with `active_fund` so the backend interprets it as "What is the NAV of Quant Small Cap Fund?"
3. User asks "What is the P/E ratio?" → Same fund context is preserved.
4. User clears the dropdown → `active_fund = null` → user must mention the fund name in queries.

**Every request to the backend includes:**
```
{
  conversation_id: string,
  query: string,
  active_fund: string | null
}
```

---

#### 8.6 Backend API Contract

The Backend (Phase 7) exposes these endpoints for the Frontend:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/query` | POST | Send a user query with conversation context; returns answer + citations. |
| `/mutual-funds` | GET | Return the list of supported mutual fund names. |
| `/last-updated` | GET | Return the last data-refresh timestamp. |

**POST /query — Request:**
```json
{
  "conversation_id": "abc-123",
  "query": "What is the NAV?",
  "active_fund": "Quant Small Cap Fund"
}
```

**POST /query — Response:**
```json
{
  "answer": "The NAV of Quant Small Cap Fund is ...",
  "citations": ["https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth"],
  "conversation_id": "abc-123"
}
```

---

#### 8.7 Design Language — Apple macOS Aesthetic

| Element | Style |
|---------|-------|
| **Fonts** | System font stack (`-apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue"`) |
| **Sidebar** | Frosted-glass translucent background (`#f5f5f7` / `rgba(245,245,247,0.9)`), subtle border |
| **Main area** | Pure white (`#ffffff`) with generous padding |
| **Accent colour** | macOS blue (`#007AFF`) for active states, buttons, links |
| **Cards / bubbles** | Rounded corners (`12px`), faint shadows (`0 1px 3px rgba(0,0,0,0.06)`) |
| **Inputs** | Rounded, light border, subtle focus ring |
| **Palette** | Neutral grays (`#1d1d1f`, `#86868b`, `#f5f5f7`), minimal colour |

---

#### 8.8 Error Handling

Handle gracefully: API failure (backend unreachable), LLM failure (Groq timeout / rate limit), network errors, and "insufficient information" responses. Display user-friendly inline error messages.

---

#### 8.9 Accessibility

- Full keyboard navigation (Tab, Enter, Escape)
- Screen reader support (ARIA labels)
- Responsive layout (sidebar collapses on small screens)

---

#### 8.10 Testing Requirements

| Test Area | What to Verify |
|-----------|----------------|
| **Chat flow** | User sends query → backend returns response → message renders correctly. |
| **Fund memory** | User selects fund from dropdown → follow-up queries resolve to the correct fund. |
| **Context clearing** | Clear dropdown → queries require explicit fund name. |
| **Conversation switching** | Each conversation retains its own messages and active fund. |
| **Error states** | API failure → user-friendly error displayed. |

---

#### 8.11 Acceptance Criteria

Phase 8 is complete when:
- Clean, minimal chatbot UI is implemented with Apple macOS aesthetic.
- Fund dropdown allows selecting/clearing a fund for the conversation.
- Fund context memory persists across messages within a conversation.
- `active_fund` is sent with every query to the backend.
- Conversation switching restores full state (messages + active fund).
- All tests pass.
- UI handles errors gracefully.

**Output of Phase 8**
- **User-facing experience:** users see their question and the system's response (or a guardrail message) in the chat interface. The "output" is the displayed conversation, fund dropdown state, and client-side state.

---

## Technology Stack (Recommended)

| Layer | Technology | Reason |
|-------|-----------|--------|
| **Web Scraping** | Playwright + BeautifulSoup | Handles JS-rendered Groww pages |
| **Chunking** | LangChain `RecursiveCharacterTextSplitter` + custom section splitter | Section-aware chunking |
| **Embeddings** | OpenAI `text-embedding-3-small` or `all-MiniLM-L6-v2` | Cost vs. self-hosted trade-off |
| **Vector Store** | ChromaDB | Vector database for embeddings (as per Phase 4) |
| **LLM** | Groq API | LLM inference; API key in `.env`, read from environment |
| **Orchestration** | LangChain or LlamaIndex | RAG pipeline management |
| **Guardrails** | Custom Python module + Guardrails AI library | PII, advice, citation checks |
| **API Layer** | FastAPI | Async, typed, fast |
| **Backend** | FastAPI | API server hosting Phases 2–6 (Phase 7) |
| **Frontend** | Next.js 16 + TypeScript + TailwindCSS | Apple macOS-inspired chatbot UI deployed on Vercel (Phase 8) |
| **Scheduler** | APScheduler or cron | Daily data refresh (triggers Phase 1) |
| **Logging** | Structured JSON logs + LangSmith | Observability, trace debugging |

---

## Data Flow Summary

```
User Query
    │
    ▼
[PII Check] ──(PII found)──► BLOCK: "Do not share personal info"
    │
    ▼
[Intent Classifier] ──(advice/comparison)──► BLOCK: "Cannot provide advice. See: <URL>"
    │                  ──(off-topic)────────► BLOCK: "I only cover Quant MF on Groww"
    │
    ▼
[Query Rewriter + Fund Resolver]
    │
    ▼
[Vector Search] ──(no relevant chunks)──► "I don't have that information"
    │
    ▼
[LLM Generation] (system prompt + context + query)
    │
    ▼
[Output Guardrail] ──(advice leak / bad URL)──► Replace with safe response
    │
    ▼
[Formatted Response] → User
```

---

## Viewing phase outputs

You can inspect the output of each phase in the following locations (similar to Phase 1’s raw and processed data):

| Phase | Where to see output | How to regenerate |
|-------|---------------------|--------------------|
| **Phase 1** | `data/raw/*.html` (raw HTML), `data/processed/*.json` (parsed fund data) | Run ingestion: `python -m phase1_data_ingestion.run_ingestion` or `--parse-only` |
| **Phase 2** | `phase2_input_guardrails/output/sample_guardrail_results.json` (sample queries → pass/block, reason, canned_response or intent) | `python -m phase2_input_guardrails.write_sample_outputs` |
| **Phase 3** | `phase3_query_processing/output/sample_query_processing_results.json` (sample queries → enriched_query, fund_resolved, canonical_name, url, section_filter) | `python -m phase3_query_processing.write_sample_outputs` |
| **Phase 4** | `phase4_retrieval_engine/output/sample_chunks.json` (how one fund is chunked), `sample_retrieval_result.json` (query → chunks + retrieved_context) | `python -m phase4_retrieval_engine.write_sample_outputs` |
| **Phase 5** | `phase5_response_generation/output/sample_response_generation.json` (user_query, context preview, raw_response, model_used, api_called) | `python -m phase5_response_generation.write_sample_outputs` (set `GROQ_API_KEY` for real LLM response) |
| **Phase 6** | `phase6_output_guardrails/output/sample_output_guardrail_results.json` (raw → validated_response, citation_url, pii_detected, advice_detected, citation_corrected) | `python -m phase6_output_guardrails.write_sample_outputs` |
| **Phase 7** | `phase7_backend/output/sample_api_responses.json` (request message → response, citation_url) | `python -m phase7_backend.write_sample_outputs` |
| **Phase 8** | `phase8_frontend/output/sample_ui_conversation.json` (sample UI conversation + quick_prompts) | `python -m phase8_frontend.write_sample_outputs` (Backend running for real responses) |

Each phase’s `output/` folder includes a README describing the files.

---

## Compliance & Security Considerations

| Concern | Mitigation |
|---------|-----------|
| PII leakage | Dual-layer PII detection (input + output), no PII stored in logs |
| Hallucinated advice | Intent classifier + output advice scanner |
| Hallucinated sources | Citation whitelist validator (only 10 URLs allowed) |
| Stale data | Daily scrape refresh + `scraped_at` timestamp in responses |
| Prompt injection | System prompt is hardcoded and non-overridable; user input is clearly delimited |
| Data privacy | No user data persisted; stateless queries; no authentication required for chatbot |
| Audit trail | Every query-response pair logged with timestamp, retrieved chunks, and model output for review |

---

## Phased Delivery Plan

| Phase / Component | Scope | Timeline |
|-------------------|-------|----------|
| **Phase 1** | Data ingestion pipeline (scrape, chunk, embed, index) | Week 1 |
| **Scheduler** | Daily run of Phase 1 (cron / APScheduler) | Week 1 |
| **Phase 2** | Input guardrails (PII, intent, advice gate) | Week 1–2 |
| **Phase 3** | Query processing (rewriter, fund resolver) | Week 2 |
| **Phase 4** | Retrieval engine (vector search, re-ranker) | Week 2–3 |
| **Phase 5** | Response generation (LLM integration, prompt engineering) | Week 3 |
| **Phase 6** | Output guardrails + formatting | Week 3–4 |
| **Phase 7** | Backend (FastAPI, host Phases 2–6, chat endpoint) | Week 4 |
| **Phase 8** | Frontend (Next.js + TypeScript + TailwindCSS, deployed on Vercel) | Week 4–5 |
| **Phase 9** | Testing, evaluation, edge-case hardening | Week 4–5 |
| **Phase 10** | Production deployment + monitoring | Week 5–6 |

---

## Integration Testing

End-to-end integration tests verify that Phases 2–8 communicate correctly as a complete system. The test suite lives in **`integration_tests/`** and covers:

- **Pipeline E2E:** `run_rag()` (Phase 2 → 3 → 4 → 5 → 6) for guardrail blocks (PII, advice, comparison, greeting), no-fund clarification, and full RAG path (factual query with citation).
- **API E2E:** Phase 7 `POST /query` and `POST /chat` with the same scenarios; response shape and validation.
- **Frontend–Backend contract:** Phase 8 Next.js frontend expects `{answer, citations, conversation_id}` from `POST /query` and a string array from `GET /mutual-funds`; tests assert the API response shape is consumable by the Frontend.
- **Fund context memory:** Sending `active_fund` with a query correctly scopes the answer to that fund without the user needing to mention it explicitly.

Run all: `pytest integration_tests/ -v`. Optionally exclude slow tests (index build / full RAG): `pytest integration_tests/ -v -m "not e2e_slow"`.

---

## Evaluation Strategy

| Metric | Method |
|--------|--------|
| **Retrieval accuracy** | Manual test set of 50 questions → measure if correct chunk is in top-5 |
| **Answer correctness** | Human review of 50 responses against source pages |
| **Guardrail effectiveness** | Red-team with 30 adversarial queries (PII, advice, injection) |
| **Citation accuracy** | Automated check: every response URL must be in the allowed list |
| **Latency** | Target: < 3 seconds end-to-end (p95) |
| **Hallucination rate** | Compare LLM output against retrieved chunks; flag unsupported claims |

---

## Deployment Architecture

### Overview

```
┌─────────────────────────────────────────┐
│          GitHub Actions (Scheduler)      │
│   Runs daily at 11:00 AM IST            │
│   Scrapes → Parses → Commits data       │
└────────────────────┬────────────────────┘
                     │ git push (data/processed/, data/chroma/, data/last_updated.json)
                     ▼
┌─────────────────────────────────────────┐
│        GitHub Repository                 │
└──────┬──────────────────────┬───────────┘
       │                      │
       ▼                      ▼
┌──────────────────┐   ┌──────────────────┐
│  Railway          │   │  Vercel           │
│  (Backend)        │   │  (Frontend)       │
│                   │   │                   │
│  FastAPI          │◄──│  Next.js + TS     │
│  Phases 2–6       │   │  TailwindCSS      │
│  ChromaDB         │   │                   │
│  Sentence-Transf. │   │  NEXT_PUBLIC_     │
│  Groq API         │   │  API_URL → Railway│
│                   │   │                   │
│  Port: $PORT      │   │  Edge CDN         │
│  Health: /health  │   │  Auto-deploy from │
│                   │   │  GitHub push      │
└──────────────────┘   └──────────────────┘
```

### Backend — Railway

| Aspect | Detail |
|--------|--------|
| **Platform** | [Railway](https://railway.app/) |
| **Runtime** | Docker (Python 3.12-slim) |
| **Config** | `Dockerfile` + `railway.toml` at project root |
| **Deps** | `requirements-backend.txt` (FastAPI, ChromaDB, sentence-transformers, Groq) |
| **Env vars** | `GROQ_API_KEY` (set in Railway dashboard) |
| **Health check** | `GET /health` — returns `{"status": "ok"}` |
| **Data** | `data/processed/`, `data/chroma/`, `data/last_updated.json` bundled in Docker image; updated via GitHub Actions → redeploy |
| **Start command** | `uvicorn phase7_backend.app:app --host 0.0.0.0 --port $PORT` |

### Frontend — Vercel

| Aspect | Detail |
|--------|--------|
| **Platform** | [Vercel](https://vercel.com/) |
| **Framework** | Next.js 16 + TypeScript + TailwindCSS v4 |
| **Root directory** | `frontend/` (set in Vercel project settings) |
| **Config** | `frontend/vercel.json` |
| **Env vars** | `NEXT_PUBLIC_API_URL` = Railway backend URL (set in Vercel dashboard) |
| **Build** | `npm run build` → static + edge-optimised output |
| **Deploy trigger** | Automatic on push to `main` branch |

### Scheduler — GitHub Actions

| Aspect | Detail |
|--------|--------|
| **Platform** | GitHub Actions |
| **Workflow** | `.github/workflows/daily-data-refresh.yml` |
| **Schedule** | Daily at 11:00 AM IST (`cron: "30 5 * * *"`) |
| **What it does** | Runs Phase 1 (scrape + parse) → Phase 4 (rebuild ChromaDB index) → commits updated `data/` to repo |
| **Secrets** | `GROQ_API_KEY` in repository secrets |
| **Logs** | Uploaded as GitHub Actions artifacts (`logs/scheduler.log`) |

### Deployment Steps

1. **Push to GitHub:** `git remote add origin <repo-url> && git push -u origin main`
2. **Railway (backend):**
   - Connect Railway to the GitHub repo (root directory)
   - Set env var `GROQ_API_KEY` in Railway dashboard
   - Railway auto-detects `Dockerfile` and deploys
   - Note the public URL (e.g. `https://your-app.up.railway.app`)
3. **Vercel (frontend):**
   - Import the GitHub repo in Vercel dashboard
   - Set **Root Directory** to `frontend/`
   - Set env var `NEXT_PUBLIC_API_URL` = Railway backend URL
   - Vercel auto-builds and deploys
4. **GitHub Actions (scheduler):**
   - Add `GROQ_API_KEY` to GitHub repo Settings → Secrets
   - Workflow runs daily at 11 AM IST; can also be triggered manually

---

## Appendix — Domain Terminology

The following glossary helps the chatbot correctly interpret abbreviations and terms in user queries. Use these definitions when resolving fund-related language and when configuring the system prompt or query rewriter.

| Abbreviation | Full form | Description |
|--------------|-----------|-------------|
| **AMC** | Asset Management Company | Entity that manages mutual funds; pools investor money and invests in securities. Quant Mutual Fund is managed by Quant Mutual Fund (AMC). |
| **MF** | Mutual Fund | Investment vehicle that pools money from many investors to buy securities (equity, debt, hybrid). |
| **ELSS** | Equity Linked Savings Scheme | Type of equity mutual fund with a lock-in period (e.g., 3 years) and tax deduction under Section 80C. |
| **SIP** | Systematic Investment Plan | Method of investing a fixed amount in a mutual fund at regular intervals (e.g., monthly). |
| **SEBI** | Securities and Exchange Board of India | Regulator for the Indian securities market; regulates mutual funds and AMCs. |
| **AMFI** | Association of Mutual Funds in India | Industry body that represents AMCs; maintains standards and investor education. |
| **FAQ** | Frequently Asked Questions | Common questions and answers; the chatbot may answer FAQ-style queries from scheme documents. |
| **Q&A** | Question and Answer | General question-and-answer format; the chatbot provides Q&A-style factual responses. |
| **KIM** | Key Information Memorandum | Short document summarizing a scheme’s key facts (risk, objective, charges). |
| **SID** | Scheme Information Document | Legal document describing a scheme’s features, objectives, and terms. |
| **PII** | Personally Identifiable Information | Data that can identify a person (e.g., PAN, Aadhaar, phone, email). The chatbot must not collect or process PII. |
| **PAN** | Permanent Account Number | Indian tax ID; the chatbot must not accept or store PAN. |
| **OTP** | One-Time Password | Single-use code for verification; the chatbot must not accept or process OTPs. |

This glossary should be available to the system (e.g., in the system prompt or as reference) so that user phrases like “ELSS lock-in” or “AMC name” are interpreted correctly and responses stay factual and aligned with scheme documents.
