import re
from typing import Dict, Any


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.

    Examples:
        "Revenue From Services" -> "revenue from services"
        "  EBITDA   Margin "     -> "ebitda margin"
    """
    if not text:
        return ""

    text = str(text).lower().strip()

    # Keep characters that can carry semantic meaning.
    text = re.sub(r"[^a-z0-9%₹$€£.-]+", " ", text)

    # Remove extra spaces.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# NUMBER / MAGNITUDE HELPERS
# ============================================================

MAGNITUDE_MULTIPLIERS = {
    "k": 1_000,
    "thousand": 1_000,
    "m": 1_000_000,
    "mn": 1_000_000,
    "million": 1_000_000,
    "bn": 1_000_000_000,
    "billion": 1_000_000_000,
}


MAGNITUDE_PATTERN = (
    r"(?:k|thousand|m|mn|million|bn|billion)"
)


def _contains_magnitude(text: str) -> bool:
    """
    Check whether a value itself contains a magnitude.

    Examples:
        "384K" -> True
        "176 Mn" -> True
        "2.5 million" -> True
        "2076" -> False
    """
    if not text:
        return False

    text = str(text).strip().lower()

    return bool(
        re.search(
            rf"(?:\d+(?:\.\d+)?)\s*{MAGNITUDE_PATTERN}\b",
            text,
        )
    )


def _parse_number_with_optional_magnitude(text: str):
    """
    Parse a number that may have:
        - commas
        - decimal values
        - percentage
        - magnitude suffix

    Examples:
        "2,076"          -> (2076.0, None, False)
        "384K"           -> (384000.0, "k", False)
        "2.5 million"    -> (2500000.0, "million", False)
        "12.68%"         -> (12.68, None, True)
        "12.68 %"        -> (12.68, None, True)
    """
    if text is None:
        return None

    text = str(text).strip().lower()
    text = text.replace(",", "")

    # Percentage.
    percent_match = re.fullmatch(
        r"([-+]?\d+(?:\.\d+)?)\s*%",
        text,
    )

    if percent_match:
        return float(percent_match.group(1)), None, True

    # Number + optional magnitude.
    number_match = re.fullmatch(
        rf"([-+]?\d+(?:\.\d+)?)\s*({MAGNITUDE_PATTERN})?",
        text,
    )

    if not number_match:
        return None

    number = float(number_match.group(1))
    magnitude = number_match.group(2)

    if magnitude:
        number *= MAGNITUDE_MULTIPLIERS[magnitude]

    return number, magnitude, False


def normalize_number(value: Any) -> Any:
    """
    Convert a numeric value into a comparable numeric representation.

    Examples:
        2076
            -> 2076.0

        "2,076"
            -> 2076.0

        "384K"
            -> 384000.0

        "176 Mn"
            -> 176000000.0

        "2.5 million"
            -> 2500000.0

        "3.2 Bn"
            -> 3200000000.0

        "12.68%"
            -> 12.68
    """
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return float(value)

    parsed = _parse_number_with_optional_magnitude(value)

    if parsed is None:
        return value

    number, _, _ = parsed

    return number


# ============================================================
# MAGNITUDE EXTRACTION
# ============================================================

def extract_magnitude_from_text(text: str) -> float:
    """
    Detect a magnitude multiplier from text.

    This function is retained for compatibility with the existing
    pipeline, but normalization below uses a safer value-local
    approach rather than blindly searching the entire evidence.

    Examples:
        "176 Mn shipments" -> 1000000.0
        "384K tons"        -> 1000.0
        "2.5 million users" -> 1000000.0
        "100 employees"    -> 1.0
    """
    if not text:
        return 1.0

    text = str(text).lower()

    # Prefer a magnitude attached to a number.
    match = re.search(
        rf"\d+(?:\.\d+)?\s*({MAGNITUDE_PATTERN})\b",
        text,
    )

    if not match:
        return 1.0

    magnitude = match.group(1)

    return MAGNITUDE_MULTIPLIERS.get(magnitude, 1.0)


def _extract_number_mentions(text: str):
    """
    Find numerical mentions in evidence.

    The parser deliberately treats an unbroken number such as
    ``2500000`` as ONE number. This is important because a generic
    ``\d{1,3}`` alternative can otherwise split it into 250 / 000 / 0.
    """
    if not text:
        return []

    pattern = re.compile(
        rf"""
        (?P<currency>[₹$€£])?
        \s*
        (?P<number>
            [-+]?
            (?:
                \d{{1,3}}(?:,\d{{3}})+
                |
                \d+(?:\.\d+)?
            )
        )
        \s*
        (?:
            (?P<percent>%)
            |
            (?P<magnitude>
                k|thousand|m|mn|million|bn|billion
            )
        )?
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    mentions = []

    for match in pattern.finditer(str(text)):
        raw_number = match.group("number")
        if raw_number is None:
            continue

        number = float(raw_number.replace(",", ""))

        percent = match.group("percent")
        magnitude = match.group("magnitude")

        if percent:
            mentions.append(
                {
                    "start": match.start(),
                    "end": match.end(),
                    "number": number,
                    "magnitude": None,
                    "multiplier": 1.0,
                    "is_percent": True,
                    "currency": match.group("currency"),
                }
            )
            continue

        multiplier = (
            MAGNITUDE_MULTIPLIERS.get(magnitude.lower(), 1.0)
            if magnitude
            else 1.0
        )

        mentions.append(
            {
                "start": match.start(),
                "end": match.end(),
                "number": number,
                "magnitude": magnitude.lower() if magnitude else None,
                "multiplier": multiplier,
                "is_percent": False,
                "currency": match.group("currency"),
            }
        )

    return mentions


def _find_matching_evidence_number(
    raw_value: Any,
    evidence: str,
):
    """
    Find the numerical mention in evidence that most likely
    corresponds to the extracted raw value.

    Important:
    We do NOT blindly use the first magnitude in the evidence.

    Example:

        raw value = 3.7
        evidence = "Rated Automated Sort Capacity of 3.70 million"

    returns the 3.70 million mention.

    If the extractor already returned:

        raw value = 3700000

    for the same evidence, we recognize that the value is
    already normalized and do not multiply it again.
    """
    if raw_value is None or not evidence:
        return None

    try:
        raw_number = float(
            str(raw_value)
            .replace(",", "")
            .replace("%", "")
            .strip()
        )
    except (TypeError, ValueError):
        return None

    mentions = _extract_number_mentions(evidence)

    if not mentions:
        return None

    best = None
    best_score = float("-inf")

    for mention in mentions:
        printed_value = mention["number"]
        normalized_value = (
            printed_value * mention["multiplier"]
        )

        # Exact match against the printed number.
        score = 0.0

        if abs(raw_number - printed_value) < 1e-9:
            score += 10

        # Match against the normalized number.
        if abs(raw_number - normalized_value) < 1e-6:
            score += 12

        # If raw value is tiny compared with normalized value,
        # it is likely the extractor returned the displayed
        # magnitude number (e.g. 3.7 from 3.7 million).
        if (
            mention["multiplier"] != 1.0
            and abs(raw_number - printed_value) < 1e-6
        ):
            score += 15

        # Percentage is a strong semantic signal.
        if mention["is_percent"]:
            score += 3

        if mention["currency"]:
            score += 1

        if score > best_score:
            best_score = score
            best = mention

    # Only accept a weak candidate if it actually resembles
    # the extracted value.
    if best is None:
        return None

    printed_value = best["number"]
    normalized_value = printed_value * best["multiplier"]

    if not (
        abs(raw_number - printed_value) < 1e-6
        or abs(raw_number - normalized_value) < 1e-6
    ):
        return None

    return best


# ============================================================
# UNIT INFERENCE
# ============================================================

def _infer_value_unit(
    fact: Dict[str, Any],
    evidence_mention,
) -> str:
    """
    Preserve the explicitly extracted unit when present.

    If the evidence clearly identifies a percentage but the
    extractor omitted the unit, infer 'percent'.

    Currency symbols are also preserved when the unit is absent.
    """
    existing_unit = normalize_text(fact.get("unit"))

    if existing_unit:
        return existing_unit

    if evidence_mention:
        if evidence_mention.get("is_percent"):
            return "percent"

        currency = evidence_mention.get("currency")

        if currency:
            return currency

    return ""


# ============================================================
# FACT NORMALIZATION
# ============================================================

def _normalize_explicit_unit(unit: Any) -> str:
    """Normalize common unit spellings without changing semantic meaning."""
    if unit is None:
        return ""

    value = str(unit).strip().lower()

    aliases = {
        "percentage": "percent",
        "%": "percent",
        "pct": "percent",
        "thousand": "thousand",
        "k": "k",
        "mn": "million",
        "m": "million",
        "million": "million",
        "bn": "billion",
        "b": "billion",
        "billion": "billion",
    }

    return aliases.get(value, value)


def _explicit_unit_multiplier(unit: Any) -> float:
    """Return the multiplier represented by an explicit magnitude unit."""
    normalized = _normalize_explicit_unit(unit)
    return {
        "k": 1_000.0,
        "thousand": 1_000.0,
        "million": 1_000_000.0,
        "billion": 1_000_000_000.0,
    }.get(normalized, 1.0)


def _value_already_contains_explicit_magnitude(value: Any) -> bool:
    """Whether the raw value text already contains its own magnitude."""
    if value is None:
        return False
    return _contains_magnitude(str(value))


def _apply_explicit_unit(
    raw_value: Any,
    normalized_value: Any,
    unit: Any,
    evidence_mention,
):
    """
    Apply a magnitude supplied explicitly in fact['unit'].

    This fixes cases such as:
        value=1, unit='billion' -> 1,000,000,000
        value=1000, unit='million' -> 1,000,000,000

    It deliberately avoids multiplying values that already contain a
    magnitude, e.g. "1 billion", and values that are already expanded
    according to the evidence, e.g. 3,700,000 for "3.7 million".
    """
    if normalized_value is None:
        return normalized_value

    if not isinstance(normalized_value, (int, float)):
        return normalized_value

    unit_multiplier = _explicit_unit_multiplier(unit)
    if unit_multiplier == 1.0:
        return normalized_value

    # Percentages are never scaled by a magnitude unit.
    if _normalize_explicit_unit(unit) == "percent":
        return normalized_value

    # A string such as "3.7 million" has already been parsed by
    # normalize_number(), so applying the unit again would double-scale it.
    if _value_already_contains_explicit_magnitude(raw_value):
        return float(normalized_value)

    # If evidence identifies the value as a percentage, keep percentage
    # points unchanged even if an erroneous unit was supplied.
    if evidence_mention and evidence_mention.get("is_percent"):
        return float(normalized_value)

    # If the evidence contains the same value with a magnitude and the
    # current value is already the expanded representation, leave it alone.
    if evidence_mention:
        printed_value = evidence_mention["number"]
        evidence_multiplier = evidence_mention["multiplier"]
        evidence_normalized = printed_value * evidence_multiplier

        if abs(float(normalized_value) - evidence_normalized) < 1e-6:
            return float(normalized_value)

        # If the evidence itself prints the absolute/base value, do not
        # multiply it again just because the extractor supplied a magnitude
        # unit separately.
        #
        # Example:
        #   2.5 + million       -> 2,500,000
        #   2,500,000 + million -> 2,500,000
        if (
            evidence_multiplier == 1.0
            and abs(float(normalized_value) - printed_value) < 1e-6
            and abs(float(normalized_value)) >= unit_multiplier
        ):
            return float(normalized_value)

        # If the extracted value is the displayed number and evidence carries
        # a magnitude, apply that evidence magnitude once.
        if abs(float(normalized_value) - printed_value) < 1e-6:
            if evidence_multiplier != 1.0:
                return float(normalized_value) * evidence_multiplier
            return float(normalized_value) * unit_multiplier

    # Otherwise trust the explicitly extracted unit. This is important for
    # facts where the unit is stored separately from the evidence text.
    return float(normalized_value) * unit_multiplier


def normalize_fact(fact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a raw extracted fact into a normalized representation.

    The original fact is not modified.

    Safeguards:
    1. Magnitudes are applied only once.
    2. Explicit fact units such as million/billion are respected.
    3. Already-normalized values are not multiplied again.
    4. Percentages remain percentage points.
    5. Evidence is used to avoid attaching an unrelated magnitude.
    6. Entity/metric/period/scope are normalized for comparison.
    """
    raw_value = fact.get("value")
    evidence = fact.get("evidence", "")
    raw_unit = fact.get("unit")

    normalized_value = normalize_number(raw_value)

    evidence_mention = None

    # First match the extracted value to a numerical mention in its evidence.
    if (
        normalized_value is not None
        and isinstance(normalized_value, (int, float))
        and evidence
    ):
        evidence_mention = _find_matching_evidence_number(
            raw_value,
            evidence,
        )

        if evidence_mention:
            printed_value = evidence_mention["number"]
            multiplier = evidence_mention["multiplier"]

            # Percentages remain percentage points.
            if evidence_mention["is_percent"]:
                normalized_value = printed_value

            # If the raw value is the displayed number and evidence carries
            # the magnitude, normalize it once.
            elif (
                multiplier != 1.0
                and abs(float(normalized_value) - printed_value) < 1e-6
            ):
                normalized_value = printed_value * multiplier

            # If raw value is already expanded, preserve it.
            elif (
                multiplier != 1.0
                and abs(
                    float(normalized_value) - (printed_value * multiplier)
                ) < 1e-6
            ):
                normalized_value = float(normalized_value)

    # Then apply a magnitude explicitly supplied in fact['unit'].
    # This is what makes 1 billion and 1000 million normalize to the same
    # base value.
    normalized_value = _apply_explicit_unit(
        raw_value=raw_value,
        normalized_value=normalized_value,
        unit=raw_unit,
        evidence_mention=evidence_mention,
    )

    # Infer/normalize the unit after value normalization.
    unit_key = _infer_value_unit(
        fact,
        evidence_mention,
    )

    # Canonicalize common magnitude spellings so comparisons are stable.
    unit_key = _normalize_explicit_unit(unit_key)

    return {
        "entity_key": normalize_text(fact.get("entity")),
        "metric_key": normalize_text(fact.get("metric")),
        "value": normalized_value,
        "unit_key": unit_key,
        "period_key": normalize_text(fact.get("period")),
        "scope_key": normalize_text(fact.get("scope")),
    }
