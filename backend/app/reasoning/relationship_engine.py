from typing import Dict, Any

from app.reasoning.fact_matcher import facts_match
from app.reasoning.fact_normalizer import normalize_number


# Units that represent the same type of magnitude
# and can therefore be compared after numeric normalization.
MAGNITUDE_UNITS = {
    "k",
    "thousand",
    "m",
    "mn",
    "million",
    "bn",
    "billion",
}


UNIT_ALIASES = {
    "k": "k",
    "thousand": "k",

    "m": "m",
    "mn": "m",
    "million": "m",

    "bn": "bn",
    "billion": "bn",

    "percent": "%",
    "percentage": "%",
    "%": "%",
}


def normalize_unit(unit: Any) -> str:
    """
    Convert equivalent unit names into a canonical representation.
    """

    if unit is None:
        return ""

    unit = str(unit).strip().lower()

    return UNIT_ALIASES.get(unit, unit)


def normalize_value(value: Any) -> Any:
    """
    Normalize a value using the shared fact normalizer.

    Magnitudes such as million/billion are already handled by
    normalize_number().
    """

    if value is None:
        return None

    return normalize_number(value)


def units_are_compatible(
    unit_a: Any,
    unit_b: Any
) -> bool:
    """
    Determine whether two units can reasonably be compared.

    Examples:

        million vs billion -> compatible
        million vs million -> compatible
        % vs percentage -> compatible
        Cr vs Tons -> incompatible
    """

    normalized_a = normalize_unit(unit_a)
    normalized_b = normalize_unit(unit_b)

    # If either unit is missing, do not reject the comparison.
    if not normalized_a or not normalized_b:
        return True

    # Exactly the same canonical unit.
    if normalized_a == normalized_b:
        return True

    # Different magnitude representations are compatible.
    if (
        normalized_a in MAGNITUDE_UNITS
        and normalized_b in MAGNITUDE_UNITS
    ):
        return True

    return False


def classify_relationship(
    fact_a: Dict[str, Any],
    fact_b: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Classify the relationship between two normalized facts.

    Possible relationships:

        - corroboration
        - contradiction
        - contextual_difference
        - incomparable
        - uncertain
    """

    # ---------------------------------------------------------
    # 1. Determine whether the facts describe the same concept.
    # ---------------------------------------------------------

    if not facts_match(fact_a, fact_b):
        return {
            "relationship": "incomparable",
            "reason": (
                "The facts do not refer to the same underlying "
                "entity and metric."
            )
        }

    # ---------------------------------------------------------
    # 2. Compare time periods.
    # ---------------------------------------------------------

    period_a = fact_a.get("period_key", "")
    period_b = fact_b.get("period_key", "")

    if period_a and period_b and period_a != period_b:
        return {
            "relationship": "contextual_difference",
            "reason": "The facts refer to different time periods."
        }

    # ---------------------------------------------------------
    # 3. Compare scope.
    # ---------------------------------------------------------

    scope_a = fact_a.get("scope_key", "")
    scope_b = fact_b.get("scope_key", "")

    if scope_a and scope_b and scope_a != scope_b:
        return {
            "relationship": "contextual_difference",
            "reason": "The facts refer to different scopes."
        }

    # ---------------------------------------------------------
    # 4. Values are required for numerical comparison.
    # ---------------------------------------------------------

    value_a = fact_a.get("value")
    value_b = fact_b.get("value")

    if value_a is None or value_b is None:
        return {
            "relationship": "uncertain",
            "reason": (
                "The facts appear comparable, but one or both "
                "facts do not contain a comparable value."
            )
        }

    # ---------------------------------------------------------
    # 5. Check unit compatibility.
    # ---------------------------------------------------------

    unit_a = fact_a.get("unit_key", "")
    unit_b = fact_b.get("unit_key", "")

    if not units_are_compatible(unit_a, unit_b):
        return {
            "relationship": "contextual_difference",
            "reason": "The facts use different units."
        }

    # ---------------------------------------------------------
    # 6. Normalize values.
    #
    # IMPORTANT:
    # normalize_fact() already converts values such as:
    #
    #     1 billion   -> 1,000,000,000
    #     1000 million -> 1,000,000,000
    #
    # Therefore we must NOT multiply by the unit again here.
    # ---------------------------------------------------------

    normalized_value_a = normalize_value(value_a)
    normalized_value_b = normalize_value(value_b)

    # ---------------------------------------------------------
    # 7. Compare normalized values.
    # ---------------------------------------------------------

    if normalized_value_a == normalized_value_b:
        return {
            "relationship": "corroboration",
            "reason": (
                "Both facts report the same normalized value "
                "for the same context."
            ),
            "normalized_value_a": normalized_value_a,
            "normalized_value_b": normalized_value_b,
        }

    # ---------------------------------------------------------
    # 8. Same concept/context, different value.
    # ---------------------------------------------------------

    return {
        "relationship": "contradiction",
        "reason": (
            "The facts report different normalized values "
            "for the same context."
        ),
        "normalized_value_a": normalized_value_a,
        "normalized_value_b": normalized_value_b,
    }