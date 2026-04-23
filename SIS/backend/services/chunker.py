CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def chunk_text(text: str) -> list[dict]:
    """Split text into fixed-size overlapping chunks."""
    chunks = []
    start = 0
    index = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]

        if chunk.strip():
            chunks.append({"chunk_index": index, "text": chunk.strip()})
            index += 1

        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks
