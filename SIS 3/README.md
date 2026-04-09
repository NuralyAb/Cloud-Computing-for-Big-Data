# RAG Telegram Bot Builder

An AI-powered platform that allows Small-to-Medium Enterprises (SMEs) to create custom Telegram chatbots backed by their own knowledge base. Upload your business information, connect a Telegram bot token, and get an intelligent assistant that answers customer questions using Retrieval-Augmented Generation (RAG).

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────┐
│  React UI   │───▶│  FastAPI      │───▶│  Supabase       │    │ Telegram │
│  (Vite +    │    │  Backend      │    │  (pgvector)     │    │ Bot API  │
│  Tailwind)  │◀───│              │◀───│                 │    │          │
└─────────────┘    └──────┬───────┘    └─────────────────┘    └────▲─────┘
                          │                                        │
                          │         ┌──────────────┐               │
                          └────────▶│  OpenAI API   │───────────────┘
                                    │  (Embeddings  │
                                    │   + GPT-4o)   │
                                    └──────────────┘
```

## Tech Stack

| Layer      | Technology                                      |
|------------|------------------------------------------------|
| Frontend   | React 18, Vite, Tailwind CSS, Axios            |
| Backend    | FastAPI, Uvicorn, python-telegram-bot           |
| Database   | Supabase (PostgreSQL + pgvector HNSW index)    |
| AI/ML      | OpenAI text-embedding-3-small, GPT-4o-mini     |
| Deployment | Local development (polling mode)                |

## Prerequisites

- Python 3.10+
- Node.js 18+
- Supabase account with pgvector extension enabled
- OpenAI API key
- Telegram Bot Token (create via [@BotFather](https://t.me/BotFather))

## Supabase Setup

Before running the application, create the required database objects in your Supabase SQL Editor:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    telegram_token TEXT NOT NULL,
    table_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- RPC function for similarity search
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding vector(1536),
    match_count int,
    target_table text
)
RETURNS TABLE (
    id bigint,
    text text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY EXECUTE format(
        'SELECT id, text, 1 - (embedding <=> %L::vector) AS similarity
         FROM %I
         ORDER BY embedding <=> %L::vector
         LIMIT %s',
        query_embedding, target_table, query_embedding, match_count
    );
END;
$$;
```

## Installation & Running

### 1. Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your actual keys:
#   SUPABASE_URL=https://your-project.supabase.co
#   SUPABASE_KEY=your-service-role-key
#   OPENAI_API_KEY=sk-...

# Run server
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment (optional, defaults to http://localhost:8000)
echo "VITE_API_URL=http://localhost:8000" > .env

# Run dev server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

## Usage

1. **Create a Project**: Click "+ New Project", enter a name, paste your Telegram bot token, and paste your knowledge base text.
2. **Start the Bot**: On the home page, click "Start" on your project card.
3. **Chat on Telegram**: Open your bot in Telegram and ask questions — it will answer based on your knowledge base.
4. **Manage Bots**: Stop, restart, or delete projects from the web interface.

## Test Knowledge Bases

The `test_knowledge_bases/` folder contains 7 ready-to-use example knowledge bases for various SME scenarios:

| File | Business Type |
|------|--------------|
| 01_clothing_store.md | Fashion retail store |
| 02_pizza_delivery.md | Pizza delivery service |
| 03_fitness_club.md | Fitness center |
| 04_language_school.md | Language courses |
| 05_car_service.md | Auto repair shop |
| 06_travel_agency.md | Travel agency |
| 07_it_courses.md | IT training school |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/api/projects` | Create project (chunks + embeds KB) |
| GET | `/api/projects` | List all projects |
| GET | `/api/projects/{id}` | Get project details |
| DELETE | `/api/projects/{id}` | Delete project and its data |
| POST | `/api/projects/{id}/start` | Start Telegram bot |
| POST | `/api/projects/{id}/stop` | Stop Telegram bot |
| GET | `/api/projects/{id}/status` | Check bot running status |
