from typing import List, Dict


def create_batches(
    chunks: List[Dict],
    batch_size: int = 10
) -> List[List[Dict]]:
    """
    Group candidate chunks into batches for efficient processing.

    Each original chunk dictionary is preserved, including:
    - page_number
    - source_document
    - chunk_text

    The function is generic and does not depend on any
    particular document, company, or fact schema.
    """

    if batch_size <= 0:
        raise ValueError("batch_size must be greater than 0.")

    if not chunks:
        return []

    return [
        chunks[start:start + batch_size]
        for start in range(0, len(chunks), batch_size)
    ]