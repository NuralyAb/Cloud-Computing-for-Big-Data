# IT4IT & Reflective Summary

## Project: RAG Telegram Bot Builder for SMEs

**Author:** Nuraly Abenov
**Course:** Cloud Computing for Big Data — SIS (Week 12): Integrated Agentic Mini-Project

---

## 1. IT4IT Value Stream Mapping

### 1.1 Strategy to Portfolio (S2P) — Business Problem & Investment Rationale

**The Problem:**
Small and medium enterprises (SMEs) in Central Asia — local shops, fitness clubs, language schools, delivery services — face a common challenge: they cannot afford dedicated customer support teams, yet they receive dozens of repetitive questions daily via Telegram (the dominant messaging platform in the region). Questions like "What are your working hours?", "How much does delivery cost?", "Do you have size L in stock?" consume staff time that could be spent on core business activities.

**Why an AI Agent is the Right Investment:**
- **Cost**: Hiring a customer support agent costs ~150,000–250,000 KZT/month. An AI-powered Telegram bot running on OpenAI GPT-4o-mini costs under 5,000 KZT/month for a typical SME workload (~1,000 queries/month).
- **Availability**: The bot operates 24/7, unlike human operators.
- **Scalability**: A single platform instance can serve multiple businesses, each with its own knowledge base and Telegram bot — a classic B2B SaaS model.
- **No Technical Expertise Required**: The business owner simply pastes their FAQ/product catalog text into the web interface. No coding, no prompt engineering, no AI knowledge needed.

**Target Market:** Local businesses in Kazakhstan that already use Telegram as their primary customer communication channel — clothing stores, food delivery, auto services, education providers.

---

### 1.2 Requirement to Deploy (R2D) — Agentic Architecture & Development Process

The entire application was developed using an AI coding agent (Claude Code) acting as the implementation engine, while I served as the Product Architect directing the design and integration decisions.

**Architectural Decisions Made by the Architect (me):**

1. **RAG over Fine-Tuning**: Chose Retrieval-Augmented Generation instead of model fine-tuning because SME knowledge bases change frequently (menu updates, price changes) and RAG allows instant updates without retraining.

2. **Technology Selection**:
   - FastAPI for the backend (async-native, critical for handling Telegram bot polling + API requests concurrently)
   - Supabase with pgvector for vector storage (managed PostgreSQL, no infrastructure overhead)
   - React + Tailwind for the frontend (fast to prototype, modern UX)
   - OpenAI text-embedding-3-small (cost-effective, 1536-dim vectors, sufficient quality for FAQ-level retrieval)

3. **Multi-Tenant Architecture**: Each project gets its own vector table with HNSW indexing. This ensures data isolation between businesses and O(log n) similarity search performance.

4. **Chunking Strategy**: Fixed-size chunks (500 characters, 50-character overlap) chosen as optimal for FAQ-style content where entries are typically short paragraphs.

5. **Bot Lifecycle Management**: In-memory asyncio task tracking for bot instances, with start/stop/status controls exposed via REST API.

**The AI agent handled:**
- Writing all FastAPI route handlers and Pydantic models
- Implementing the chunking, embedding, and RAG pipeline
- Building the React frontend with components, routing, and API integration
- Configuring Tailwind CSS, Vite, and project dependencies
- Writing the Telegram bot message handler with typing indicators

**See:** `Antigravity_Session_Logs.md` for the complete transcript of architectural prompts and AI iterations.

---

### 1.3 Request to Fulfill (R2F) — How SMEs Consume the Tool

The tool is delivered through **two interfaces**:

**For the Business Owner (Admin Panel):**
- A responsive web application (React) where the SME owner:
  1. Creates a new project by entering a name, Telegram bot token, and knowledge base text
  2. Starts/stops the bot with a single click
  3. Monitors bot status (running/stopped) in real-time
  4. Manages multiple bots from a single dashboard

**For the End Customer (Telegram):**
- The customer interacts with the business's Telegram bot naturally:
  1. Opens the bot in Telegram
  2. Types a question in natural language (e.g., "Do you deliver to Almaty?")
  3. Receives an AI-generated answer grounded in the business's actual knowledge base
  4. If the answer is not in the KB, the bot transparently says "I don't have information about that"

**Fulfillment Flow:**
```
SME Owner → Web UI → Creates Project → Bot Starts on Telegram
Customer → Telegram → Asks Question → RAG Pipeline → Answer from KB
```

---

### 1.4 Detect to Correct (D2C) — Monitoring, FinOps & Error Handling

**FinOps — LLM API Cost Monitoring:**
- **Embedding costs**: text-embedding-3-small at $0.02/1M tokens. A typical SME knowledge base (5,000 words) costs ~$0.001 to embed. Negligible one-time cost per project.
- **Query costs**: GPT-4o-mini at $0.15/1M input tokens, $0.60/1M output tokens. At ~500 tokens per query (context + question + answer), 1,000 monthly queries cost approximately $0.50.
- **Monitoring approach**: OpenAI usage dashboard tracks token consumption per API key. For production, implement per-project token counters in the database to enable per-tenant billing.

**Hallucination Detection & Mitigation:**
- **System prompt constraint**: The RAG system prompt explicitly instructs the model: "Answer using ONLY the provided context. If the answer is not in the knowledge base, say 'I don't have information about that.'" This grounds responses in retrieved chunks.
- **Top-K retrieval with similarity threshold**: Only the 5 most similar chunks are passed as context. If similarity scores are low, the model is more likely to trigger the "no information" fallback.
- **Future improvement**: Log all queries and responses to a monitoring table. Flag responses where the model's answer does not overlap with retrieved chunk content (extractive overlap score < threshold).

**System Error Handling:**
- **Bot crash recovery**: If a Telegram polling task fails, the error is caught and the bot status is updated. The admin can restart from the web UI.
- **API failures**: OpenAI API errors (rate limits, timeouts) are caught in the embedding and generation services with user-friendly error messages returned to both the web UI and Telegram users.
- **Database resilience**: Supabase provides managed backups, point-in-time recovery, and automatic failover.

**Production Monitoring Roadmap:**
| Metric | Tool | Action |
|--------|------|--------|
| API token usage | OpenAI Dashboard / custom counters | Alert if monthly cost exceeds budget |
| Bot uptime | Health check endpoint + cron ping | Auto-restart on failure |
| Response quality | Query-response logging + human review | Flag low-similarity retrievals |
| Latency | FastAPI middleware timing | Investigate if P95 > 3 seconds |

---

## 2. Reflective Summary: Managing an AI Agent vs. Writing Code

### What It Was Like

Working as a Product Architect rather than a programmer fundamentally changed how I approached the project. Instead of thinking about syntax, imports, and debugging stack traces, I focused on **system-level decisions**: which database to use, how to structure the API, what the user experience should feel like, and how the components should interact.

The AI agent was remarkably effective at translating high-level architectural instructions into working code. When I said "create a FastAPI backend with routes for project CRUD and bot lifecycle management," it produced a well-structured codebase with proper separation of concerns — routers, services, models — without me specifying the file structure.

### Hardest Architectural Bottlenecks to Explain

1. **Multi-tenant vector isolation**: Explaining that each business should get its own pgvector table (not rows in a shared table) required multiple iterations. The AI initially wanted a single embeddings table with a project_id filter. I had to explain the performance and security implications of per-tenant table isolation with HNSW indexes.

2. **Async bot lifecycle management**: The trickiest part was explaining how Telegram bot polling should work as background asyncio tasks that can be started and stopped independently. The AI's first approach used blocking threads, which conflicted with FastAPI's async event loop. It took several prompts to arrive at the correct `asyncio.create_task()` pattern with proper cleanup.

3. **RAG grounding constraints**: Getting the AI to understand that the system prompt must explicitly prevent hallucination was important. The initial version produced creative but ungrounded responses. I had to architect the prompt to include strict "answer ONLY from context" instructions and a clear fallback message.

4. **Chunking strategy trade-offs**: The AI defaulted to sentence-level splitting. I had to explain why fixed-size overlapping chunks work better for diverse SME content (mixed formats: tables, bullet points, paragraphs) where sentence boundaries are unreliable.

### Key Takeaway

The role of the architect is not to write code — it is to make decisions that the AI cannot make on its own: **what** to build, **why** to build it, and **how** the pieces fit together for a real business user. The AI excels at the "how to implement" once the architecture is clear. The bottleneck was never the coding — it was communicating the business context and system constraints clearly enough for the agent to make the right implementation choices.
