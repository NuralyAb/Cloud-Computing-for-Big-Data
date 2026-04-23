from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


async def create_project_record(
    project_id: str,
    name: str,
    telegram_token: str,
    table_name: str,
    user_id: str,
    owner_tg_id: int | None = None,
) -> dict:
    """Insert a new project into the projects table."""
    data = {
        "id": project_id,
        "name": name,
        "telegram_token": telegram_token,
        "table_name": table_name,
        "user_id": user_id,
        "owner_tg_id": owner_tg_id,
    }
    result = supabase.table("projects").insert(data).execute()
    return result.data[0]


async def get_all_projects(user_id: str) -> list[dict]:
    """Fetch all projects for a specific user."""
    result = supabase.table("projects").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return result.data


async def get_project(project_id: str) -> dict | None:
    """Fetch a single project by ID."""
    result = supabase.table("projects").select("*").eq("id", project_id).execute()
    if result.data:
        return result.data[0]
    return None


async def delete_project(project_id: str) -> None:
    """Delete a project record."""
    supabase.table("projects").delete().eq("id", project_id).execute()


async def create_kb_table(table_name: str) -> None:
    """Create a knowledge base table with vector support."""
    sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id          BIGSERIAL PRIMARY KEY,
        chunk_index INT NOT NULL,
        content     TEXT NOT NULL,
        embedding   vector(1536) NOT NULL
    );
    CREATE INDEX IF NOT EXISTS {table_name}_embedding_idx
        ON {table_name} USING hnsw (embedding vector_cosine_ops);
    """
    supabase.postgrest.session.headers.update(
        {"Prefer": "return=minimal"}
    )
    supabase.rpc("exec_sql", {"query": sql}).execute()


async def drop_kb_table(table_name: str) -> None:
    """Drop a knowledge base table."""
    sql = f"DROP TABLE IF EXISTS {table_name} CASCADE;"
    supabase.rpc("exec_sql", {"query": sql}).execute()


async def insert_chunks(table_name: str, chunks: list[dict], embeddings: list[list[float]]) -> None:
    """Insert chunks with their embeddings into the KB table."""
    for chunk, embedding in zip(chunks, embeddings):
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        sql = f"""
        INSERT INTO {table_name} (chunk_index, content, embedding)
        VALUES ({chunk['chunk_index']}, $${chunk['text']}$$, '{embedding_str}');
        """
        supabase.rpc("exec_sql", {"query": sql}).execute()


async def similarity_search(table_name: str, query_embedding: list[float], top_k: int = 5) -> list[dict]:
    """Find the most similar chunks to the query embedding."""
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    result = supabase.rpc("match_chunks", {
        "target_table": table_name,
        "query_embedding": embedding_str,
        "match_count": top_k,
    }).execute()
    if result.data and isinstance(result.data, list):
        return result.data
    return []
