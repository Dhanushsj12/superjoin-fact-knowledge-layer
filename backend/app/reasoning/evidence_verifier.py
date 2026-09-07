from typing import Dict


def normalize_text(text: str) -> str:
    """
    Normalize text for reliable evidence matching.

    This handles differences such as:
    - multiple spaces
    - line breaks
    - leading/trailing whitespace
    """
    return " ".join(text.split()).lower()


def verify_evidence(fact: Dict, chunk_text: str) -> bool:
    """
    Check whether the extracted evidence exists in the source chunk.

    Returns:
        True  -> evidence is supported by the source text
        False -> evidence could not be found
    """

    evidence = fact.get("evidence")

    if not evidence or not chunk_text:
        return False

    normalized_evidence = normalize_text(evidence)
    normalized_chunk = normalize_text(chunk_text)

    return normalized_evidence in normalized_chunk