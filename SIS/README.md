# RAG Telegram Bot Builder

A full-stack application for creating RAG-powered Telegram bots. Users provide a Telegram bot token and a knowledge base text — the system chunks, embeds, and stores the text in Supabase (pgvector), then launches a Telegram bot that answers questions using retrieval-augmented generation.

## Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React (Vite + Tailwind CSS)
- **Vector DB**: Supabase (pgvector)
- **Embeddings**: OpenAI text-embedding-3-small
- **LLM**: Anthropic Claude (claude-sonnet-4-20250514)
- **Telegram**: python-telegram-bot v20+

## Supabase Setup

1. Create a Supabase project at [supabase.com](https://supabase.com)

2. Enable the pgvector extension. Go to **SQL Editor** and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

3. Create the `projects` table:

```sql
CREATE TABLE projects (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name         TEXT NOT NULL,
  telegram_token TEXT NOT NULL,
  table_name   TEXT NOT NULL UNIQUE,
  created_at   TIMESTAMPTZ DEFAULT now()
);
```

4. Create a helper function for executing raw SQL (used by the backend for dynamic table creation):

```sql
CREATE OR REPLACE FUNCTION exec_sql(query TEXT)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result JSONB;
BEGIN
  EXECUTE query;
  RETURN '[]'::JSONB;
EXCEPTION WHEN others THEN
  RETURN jsonb_build_array(jsonb_build_object('error', SQLERRM));
END;
$$;
```

5. For similarity search, create a function that returns results:

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
  -- If the query is not a SELECT, just execute it
  BEGIN
    EXECUTE query;
    RETURN '[]'::JSONB;
  EXCEPTION WHEN others THEN
    RETURN jsonb_build_array(jsonb_build_object('error', SQLERRM));
  END;
END;
$$;
```

## Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

Run the backend:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

## Frontend Setup

```bash
cd frontend
npm install
```

Run the frontend:

```bash
npm run dev
```

The frontend runs at `http://localhost:5173` and connects to the backend at `http://localhost:8000`.

## Usage

1. Get a Telegram bot token from [@BotFather](https://t.me/BotFather)
2. Open `http://localhost:5173`
3. Click **+ New Project**
4. Enter a project name, paste the bot token, and paste your knowledge base text
5. Click **Create & Index** — the system chunks and embeds the text
6. On the home page, click **Start** to launch the bot
7. Message your bot on Telegram — it will answer questions from the knowledge base
