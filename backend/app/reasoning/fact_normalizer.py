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

    text = str(text).lower().strip()

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
        2076            -> 2076.0
        "2,076"         -> 2076.0
        "384K"          -> 384000.0
        "176 Mn"        -> 176000000.0
        "2.5 million"   -> 2500000.0
        "3.2 Bn"        -> 3200000000.0
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


def extract_magnitude_from_text(text: str) -> float:
    """
    Detect a magnitude multiplier from text.

    Examples:
        "176 Mn shipments" -> 1000000.0
        "384K tons"        -> 1000.0
        "2.5 million users" -> 1000000.0
        "100 employees"    -> 1.0
    """

    if not text:
        return 1.0

    text = str(text).lower()

    magnitude_pattern = re.search(
        r"\b(k|thousand|m|mn|million|bn|billion)\b",
        text
    )

    if not magnitude_pattern:
        # Also support forms such as 384K
        compact_pattern = re.search(
            r"\d\s*(k|m|mn|bn)\b",
            text
        )

        if not compact_pattern:
            return 1.0

        magnitude = compact_pattern.group(1)
    else:
        magnitude = magnitude_pattern.group(1)

    multipliers = {
        "k": 1_000,
        "thousand": 1_000,
        "m": 1_000_000,
        "mn": 1_000_000,
        "million": 1_000_000,
        "bn": 1_000_000_000,
        "billion": 1_000_000_000,
    }

    return multipliers.get(magnitude, 1.0)


def normalize_fact(fact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a raw extracted fact into a normalized representation.

    The original fact is not modified.

    If the extracted numeric value does not contain a magnitude
    but the evidence contains one, the magnitude from the evidence
    is applied.

    Example:

        value:
            176

        unit:
            shipments

        evidence:
            "176 Mn shipments"

        normalized value:
            176000000
    """

    raw_value = fact.get("value")
    evidence = fact.get("evidence", "")

    normalized_value = normalize_number(raw_value)

    # ---------------------------------------------------------
    # Recover magnitude from evidence when necessary
    # ---------------------------------------------------------

    if (
        normalized_value is not None
        and isinstance(normalized_value, (int, float))
        and evidence
    ):
        evidence_multiplier = extract_magnitude_from_text(evidence)

        # Only apply the evidence multiplier when the raw
        # numeric value itself did not already contain one.
        raw_value_text = str(raw_value).lower()

        value_has_magnitude = bool(
            re.search(
                r"(k|thousand|m|mn|million|bn|billion)",
                raw_value_text
            )
        )

        if evidence_multiplier != 1.0 and not value_has_magnitude:
            normalized_value *= evidence_multiplier

    normalized_fact = {
        "entity_key": normalize_text(fact.get("entity")),
        "metric_key": normalize_text(fact.get("metric")),
        "value": normalized_value,
        "unit_key": normalize_text(fact.get("unit")),
        "period_key": normalize_text(fact.get("period")),
        "scope_key": normalize_text(fact.get("scope")),
    }

    return normalized_fact