import re
from typing import List, Dict


# Generic signals that a chunk may contain a meaningful fact.
# These are not tied to any company, document, or metric.
CURRENCY_PATTERN = re.compile(
    r"(₹|\$|€|£|inr|usd|eur|gbp)",
    re.IGNORECASE
)

PERCENT_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s*%"
)

NUMBER_PATTERN = re.compile(
    r"\b\d[\d,]*(?:\.\d+)?\b"
)

PERIOD_PATTERN = re.compile(
    r"\b("
    r"fy\s*\d{2,4}|"
    r"q[1-4]\s*(?:fy)?\s*\d{2,4}|"
    r"\d{4}|"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
    r"(?:uary|ruary|ch|il|e|y|ust|tember|ober|ember)?\s+\d{4}"
    r")\b",
    re.IGNORECASE
)

MAGNITUDE_PATTERN = re.compile(
    r"\b("
    r"thousand|million|billion|"
    r"mn|bn|"
    r"k|m|b"
    r")\b",
    re.IGNORECASE
)


def candidate_score(text: str) -> int:
    """
    Estimate whether a text chunk is likely to contain
    meaningful factual information.

    This is a lightweight pre-filter. It does not attempt
    to extract facts and does not contain document-specific
    rules.
    """

    if not text or not text.strip():
        return 0

    score = 0

    if NUMBER_PATTERN.search(text):
        score += 1

    if CURRENCY_PATTERN.search(text):
        score += 2

    if PERCENT_PATTERN.search(text):
        score += 2

    if PERIOD_PATTERN.search(text):
        score += 1

    if MAGNITUDE_PATTERN.search(text):
        score += 1

    # A chunk containing several numbers is more likely
    # to contain quantitative facts.
    number_count = len(NUMBER_PATTERN.findall(text))

    if number_count >= 3:
        score += 1

    if number_count >= 8:
        score += 1

    return score


def is_candidate_chunk(
    chunk: Dict,
    minimum_score: int = 2
) -> bool:
    """
    Return True when a chunk contains enough generic
    factual signals to justify further processing.
    """

    text = chunk.get("chunk_text", "")

    return candidate_score(text) >= minimum_score


def filter_candidate_chunks(
    chunks: List[Dict],
    minimum_score: int = 2
) -> List[Dict]:
    """
    Keep only chunks that are likely to contain
    meaningful factual information.

    The original chunk objects are preserved.
    """

    return [
        chunk
        for chunk in chunks
        if is_candidate_chunk(chunk, minimum_score)
    ]