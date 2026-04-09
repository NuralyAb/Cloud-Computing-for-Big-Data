from openai import AsyncOpenAI
from config import OPENAI_API_KEY

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

MODEL = "text-embedding-3-small"
BATCH_SIZE = 100


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts, batching to avoid rate limits."""
    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        response = await client.embeddings.create(model=MODEL, input=batch)
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings


async def embed_query(text: str) -> list[float]:
    """Generate embedding for a single query."""
    response = await client.embeddings.create(model=MODEL, input=[text])
    return response.data[0].embedding
