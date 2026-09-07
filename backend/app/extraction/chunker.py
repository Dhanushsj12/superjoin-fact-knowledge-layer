from typing import List, Dict


def create_chunks(
    pages: List[Dict],
    chunk_size: int = 1500,
    min_chunk_size: int = 100,
    source_document: str = ""
) -> List[Dict]:

    chunks = []

    for page in pages:
        text = page["text"].strip()

        if not text:
            continue

        for start in range(0, len(text), chunk_size):
            chunk_text = text[start:start + chunk_size].strip()

            # Ignore very small fragments
            if len(chunk_text) < min_chunk_size:
                continue

            chunks.append({
    "page_number": page["page_number"],
    "chunk_text": chunk_text,
    "source_document": source_document
})

    return chunks