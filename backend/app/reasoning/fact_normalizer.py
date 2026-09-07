import re
from typing import Dict, Any


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.

    Examples:
        "Revenue From Services" -> "revenue from services"
        "  EBITDA   Margin "    -> "ebitda margin"
    """

    if not text:
        return ""

    text = text.lower().strip()

    # Replace punctuation with spaces
    text = re.sub(r"[^a-z0-9%₹$€£.-]+", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_number(value: Any) -> Any:
    """
    Convert numeric values and common magnitude expressions
    into a comparable numeric representation.

    Examples:
        2076           -> 2076.0
        "2,076"        -> 2076.0
        "384K"         -> 384000.0
        "176 Mn"       -> 176000000.0
        "2.5 million"  -> 2500000.0
        "3.2 Bn"       -> 3200000000.0
    """

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().lower()

    # Remove thousands separators
    text = text.replace(",", "")

    # Match number + optional magnitude
    match = re.fullmatch(
        r"([-+]?\d*\.?\d+)\s*"
        r"(k|thousand|m|mn|million|bn|billion)?",
        text
    )

    if not match:
        return value

    number = float(match.group(1))
    magnitude = match.group(2)

    multipliers = {
        "k": 1_000,
        "thousand": 1_000,
        "m": 1_000_000,
        "mn": 1_000_000,
        "million": 1_000_000,
        "bn": 1_000_000_000,
        "billion": 1_000_000_000,
    }

    if magnitude:
        number *= multipliers[magnitude]

    return number


def normalize_fact(fact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a raw extracted fact into a normalized representation.

    The original fact is not modified.
    """

    normalized_fact = {
        "entity_key": normalize_text(fact.get("entity")),
        "metric_key": normalize_text(fact.get("metric")),
        "value": normalize_number(fact.get("value")),
        "unit_key": normalize_text(fact.get("unit")),
        "period_key": normalize_text(fact.get("period")),
        "scope_key": normalize_text(fact.get("scope")),
    }

    return normalized_fact