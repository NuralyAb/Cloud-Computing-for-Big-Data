from openai import AsyncOpenAI
from config import OPENAI_API_KEY
from services.embedder import embed_query
from services.supabase_service import similarity_search

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question using ONLY "
    "the provided context. If the answer is not in the context, say: "
    "'I don't have information about that in my knowledge base.' "
    "Be concise and accurate."
)


async def retrieve(query: str, table_name: str, top_k: int = 5) -> list[dict]:
    """Embed query and retrieve similar chunks from the knowledge base."""
    query_embedding = await embed_query(query)
    results = await similarity_search(table_name, query_embedding, top_k)
    return results


async def generate(query: str, chunks: list[dict]) -> str:
    """Generate an answer using OpenAI with retrieved context."""
    if not chunks:
        return "I don't have information about that in my knowledge base."

    context = "\n\n---\n\n".join(
        chunk["content"] if isinstance(chunk, dict) and "content" in chunk else str(chunk)
        for chunk in chunks
    )

    user_message = f"Context:\n{context}\n\nQuestion: {query}"

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1024,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {str(e)}"
