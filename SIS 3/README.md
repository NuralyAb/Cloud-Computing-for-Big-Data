# RAG Telegram Bot Builder

A self-serve platform for building knowledge-base-powered Telegram bots. Users sign up, upload a knowledge base (plain text, document, or a web page URL), and the system automatically chunks, embeds and stores it in a dedicated `pgvector` table. One click launches a Telegram bot that answers user questions using **Retrieval-Augmented Generation** — with built-in analytics and human handoff when the bot doesn't know the answer.

---

## Features

- **Multi-user platform** — email/password registration, bcrypt password hashing, JWT-based sessions (30 days).
- **Multiple knowledge-base sources**
  - Paste raw text
  - Upload a file (`PDF`, `DOCX`, `TXT`, `MD`)
  - Pull content from a URL (HTML is cleaned — `<script>`, `<style>`, `<nav>`, `<header>`, `<footer>` stripped)
- **Isolated per-project vector stores** — every project gets its own `pgvector` table with an HNSW cosine index, so knowledge bases never leak between projects.
- **One-click bot lifecycle** — start / stop / status endpoints run each bot as an async task inside the FastAPI process (Telegram long polling).
- **RAG pipeline** — OpenAI `text-embedding-3-small` (1536-d) for embeddings, top-5 cosine retrieval, OpenAI `gpt-4o-mini` for generation with a strict "answer only from context" system prompt.
- **Human handoff** — when the bot can't answer, the project owner receives a Telegram DM with the user's question and handle (`@username`), so they can jump in manually.
- **Conversation logging & analytics per project**
  - Total / answered / unanswered messages
  - Unique users
  - 14-day activity timeline
  - Top-10 most asked questions
  - Grouped list of unanswered questions (for improving the knowledge base)
- **Ownership enforcement** — every API call checks that the caller owns the project; other users get `403`.

---

## How it works

```
 ┌────────────┐   upload KB    ┌────────────────┐
 │  Frontend  │ ─────────────▶ │   FastAPI API  │
 │  (React)   │ ◀───────────── │                │
 └────────────┘   JWT token    └───────┬────────┘
                                       │
                   chunk → embed (OpenAI)
                                       │
                                       ▼
                            ┌──────────────────────┐
                            │ Supabase (pgvector)  │
                            │  - users             │
                            │  - projects          │
                            │  - conversations     │
                            │  - kb_<project>_... │
                            └──────────┬───────────┘
                                       │
                          ┌────────────┴─────────────┐
                          │                          │
                ┌─────────▼─────────┐      ┌─────────▼─────────┐
                │  Telegram Bot(s)  │      │    Analytics UI   │
                │ (python-telegram- │      │                   │
                │  bot, polling)    │      │                   │
                └───────────────────┘      └───────────────────┘
```

On each user message:
1. Embed the question (OpenAI).
2. Retrieve top-5 similar chunks from the project's `pgvector` table (HNSW cosine).
3. Generate an answer with `gpt-4o-mini` constrained to the retrieved context.
4. Log the Q&A (answered / unanswered flag).
5. If unanswered and an owner Telegram ID is configured — DM the owner.

---

## Tech stack

| Layer        | Tech                                                                 |
|--------------|----------------------------------------------------------------------|
| Frontend     | React 18, Vite, Tailwind CSS, React Router, axios, react-hot-toast   |
| Backend      | FastAPI, Pydantic, uvicorn                                           |
| Auth         | `python-jose` (JWT, HS256), `passlib[bcrypt]`                        |
| Vector DB    | Supabase PostgreSQL + `pgvector` (HNSW cosine)                       |
| Embeddings   | OpenAI `text-embedding-3-small`                                      |
| LLM          | OpenAI `gpt-4o-mini`                                                 |
| Telegram     | `python-telegram-bot` v20+ (async, long polling)                     |
| Extraction   | `pypdf`, `python-docx`, `beautifulsoup4`, `httpx`                    |

---

## Prerequisites

- **Python** 3.11+
- **Node.js** 18+
- **Supabase** project (free tier works)
- **OpenAI** API key
- A **Telegram bot token** per bot you want to run (from [@BotFather](https://t.me/BotFather))

---

## Setup

### 1. Supabase

Create a project at [supabase.com](https://supabase.com). In the **SQL Editor** run the following blocks one by one.

**Enable pgvector:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**Users table:**
```sql
CREATE TABLE users (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email          TEXT NOT NULL UNIQUE,
  password_hash  TEXT NOT NULL,
  created_at     TIMESTAMPTZ DEFAULT now()
);
```

**Projects table:**
```sql
CREATE TABLE projects (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name           TEXT NOT NULL,
  telegram_token TEXT NOT NULL,
  table_name     TEXT NOT NULL UNIQUE,
  owner_tg_id    BIGINT,
  created_at     TIMESTAMPTZ DEFAULT now()
);
```

**Conversations table:**
```sql
CREATE TABLE conversations (
  id          BIGSERIAL PRIMARY KEY,
  project_id  UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_tg_id  BIGINT,
  username    TEXT,
  question    TEXT NOT NULL,
  answer      TEXT NOT NULL,
  answered    BOOLEAN NOT NULL DEFAULT true,
  created_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON conversations (project_id, created_at DESC);
```

**`exec_sql` helper** — the backend creates per-project KB tables and runs aggregation queries through this function:
```sql
CREATE OR REPLACE FUNCTION exec_sql(query TEXT)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result JSONB;
BEGIN
  EXECUTE 'SELECT COALESCE(jsonb_agg(row_to_json(t)), ''[]''::jsonb) FROM (' || query || ') t' INTO result;
  RETURN result;
EXCEPTION WHEN others THEN
  BEGIN
    EXECUTE query;
    RETURN '[]'::JSONB;
  EXCEPTION WHEN others THEN
    RETURN jsonb_build_array(jsonb_build_object('error', SQLERRM));
  END;
END;
$$;
```

**`match_chunks` similarity-search function** — called on every bot message:
```sql
CREATE OR REPLACE FUNCTION match_chunks(
  target_table    TEXT,
  query_embedding vector(1536),
  match_count     INT
)
RETURNS TABLE (content TEXT, similarity FLOAT)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY EXECUTE format(
    'SELECT content, 1 - (embedding <=> %L) AS similarity
     FROM %I
     ORDER BY embedding <=> %L
     LIMIT %L',
    query_embedding, target_table, query_embedding, match_count
  );
END;
$$;
```

> Use the **service-role key** for `SUPABASE_KEY` in the backend — the backend creates and drops tables dynamically.

### 2. Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env` (see [backend/.env.example](backend/.env.example)):

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
OPENAI_API_KEY=sk-...
JWT_SECRET=replace-with-a-long-random-string
```

Run:

```bash
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173 and expects the backend at http://localhost:8000.

---

## Usage

1. Open http://localhost:5173 and **register** a new account.
2. In Telegram, open [@BotFather](https://t.me/BotFather) → `/newbot` → copy the token.
3. *(Optional)* Get your numeric Telegram ID from [@userinfobot](https://t.me/userinfobot) if you want handoff notifications.
4. Click **+ New Project** and fill in:
   - Project name
   - Telegram bot token
   - Your Telegram user ID (optional, for handoff)
   - Knowledge base — choose **Text**, **File**, or **URL** and provide the source.
5. Click **Create & Index**. The backend:
   - Extracts the text (from file / URL if needed)
   - Chunks it (500 chars, 50-char overlap)
   - Embeds all chunks via OpenAI
   - Creates a dedicated `kb_<name>_<id>` table with an HNSW index and inserts the chunks
6. From the dashboard click **Start** — the bot begins long-polling Telegram.
7. Message your bot. Every conversation is logged.
8. Open **Analytics / Unanswered** to see usage stats and which questions are hurting your KB.

---

## API overview

All `/api/projects/*` endpoints require `Authorization: Bearer <jwt>`.

| Method | Path                                    | Purpose                                |
|--------|-----------------------------------------|----------------------------------------|
| POST   | `/api/auth/register`                    | Create account, return JWT             |
| POST   | `/api/auth/login`                       | Login, return JWT                      |
| GET    | `/api/auth/me`                          | Current user                           |
| POST   | `/api/projects`                         | Create project + index KB (multipart)  |
| GET    | `/api/projects`                         | List my projects                       |
| GET    | `/api/projects/{id}`                    | Get one project                        |
| DELETE | `/api/projects/{id}`                    | Stop bot + drop KB table + delete row  |
| POST   | `/api/projects/{id}/start`              | Start the Telegram bot                 |
| POST   | `/api/projects/{id}/stop`               | Stop the Telegram bot                  |
| GET    | `/api/projects/{id}/status`             | `{ running: bool }`                    |
| GET    | `/api/projects/{id}/analytics`          | Aggregated stats                       |
| GET    | `/api/projects/{id}/unanswered`         | Grouped unanswered questions           |

---

## Project structure

```
.
├── backend/
│   ├── main.py                 # FastAPI app + CORS + routers
│   ├── config.py               # env + JWT settings
│   ├── models.py               # pydantic schemas
│   ├── dependencies.py         # get_current_user (JWT)
│   ├── routers/
│   │   ├── auth.py             # /api/auth/*
│   │   ├── projects.py         # /api/projects CRUD + indexing
│   │   └── bots.py             # start/stop/status/analytics/unanswered
│   └── services/
│       ├── auth_service.py     # bcrypt + JWT
│       ├── chunker.py          # fixed-size chunking
│       ├── embedder.py         # OpenAI embeddings (batched)
│       ├── rag.py              # retrieve() + generate()
│       ├── text_extractor.py   # PDF / DOCX / TXT / MD / URL
│       ├── supabase_service.py # tables, RPC, similarity search
│       ├── bot_manager.py      # per-project asyncio bot tasks
│       ├── conversation_service.py # logging + analytics
│       └── handoff_service.py  # DM owner on unanswered
├── frontend/
│   └── src/
│       ├── pages/              # Login / Register / Dashboard / CreateProject / Home
│       ├── components/         # Navbar / ProjectCard / ProtectedRoute / StatusBadge
│       ├── context/            # AuthContext (JWT in localStorage)
│       └── api/client.js       # axios instance with auth header
└── test_knowledge_bases/       # sample KBs for demo (clothing store, pizza, fitness, ...)
```

---

## Notes and limits

- **Single-process bot runtime.** Bots run as `asyncio` tasks inside the FastAPI process, so restarting the backend stops every bot. For production, move bots to a separate worker / supervisor.
- **Permissive CORS.** `allow_origins=["*"]` is fine for local dev — tighten before deploying.
- **`exec_sql` is powerful.** It's required for creating per-project KB tables and running analytics aggregations. It executes arbitrary SQL on the service-role connection — only call it from the trusted backend, never expose the service-role key to clients.
- **Telegram token stored in plaintext.** The service-role `projects.telegram_token` column is readable by the backend. If you share the DB, encrypt it at rest or use a KMS.
- **Chunking is character-based** (500 / 50 overlap). Good enough for demos; swap to token- or semantic-based chunking for production KBs.
