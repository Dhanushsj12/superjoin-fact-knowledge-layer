from typing import List, Dict


def extract_facts_from_chunks(chunks: List[Dict]) -> List[Dict]:
    """
    Prepare document chunks for fact extraction.

    Each chunk keeps its source information so that
    every extracted fact can later be linked back
    to the exact evidence and page.
    """

    facts = []

    for chunk in chunks:
        fact_candidate = {
            "entity": None,
            "metric": None,
            "value": None,
            "unit": None,
            "period": None,
            "scope": None,
            "evidence": chunk["chunk_text"],
            "page_number": chunk["page_number"],
            "source_document": chunk.get("source_document"),
        }

        facts.append(fact_candidate)

    return facts