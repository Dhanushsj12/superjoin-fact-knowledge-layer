from typing import List, Dict


def extract_mock_facts(chunks: List[Dict]) -> List[Dict]:
    """
    Deterministic fact extractor used for local development and tests.

    This does not call an external LLM. It is intentionally small and
    exists only so the reasoning pipeline can be tested without API
    availability or quota limitations.
    """

    facts = []

    for chunk in chunks:
        text = chunk["chunk_text"].lower()

        # Only generate test facts when the chunk contains
        # recognizable numerical evidence.
        if "revenue from services" in text and "2076" in text:
            facts.append({
                "entity": "Delhivery Limited",
                "metric": "Revenue from Services",
                "value": 2076,
                "unit": "Cr",
                "period": "Q4 FY24",
                "scope": None,
                "evidence": "Revenue from Services 2,076 Cr",
                "page_number": chunk["page_number"],
                "source_document": chunk["source_document"],
                "evidence_verified": True,
            })

        if "freight tonnage" in text and "384" in text:
            facts.append({
                "entity": "Delhivery Limited",
                "metric": "PTL Freight Tonnage",
                "value": 384000,
                "unit": "Tons",
                "period": "Q4 FY24",
                "scope": None,
                "evidence": "384K Tons",
                "page_number": chunk["page_number"],
                "source_document": chunk["source_document"],
                "evidence_verified": True,
            })

    return facts