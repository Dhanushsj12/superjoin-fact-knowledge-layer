from typing import Dict, Any

from app.reasoning.fact_matcher import facts_match
from app.reasoning.fact_normalizer import normalize_number


def normalize_value(value: Any) -> Any:
    """
    Convert a fact value into a comparable numeric representation
    when possible.
    """
    if value is None:
        return None

    return normalize_number(value)


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

    Matching determines whether two facts are comparable.
    Relationship reasoning then determines how the comparable
    facts relate to each other.
    """

    # ---------------------------------------------------------
    # 1. Determine whether the facts are comparable
    # ---------------------------------------------------------

    if not facts_match(fact_a, fact_b):
        return {
            "relationship": "incomparable",
            "reason": "The facts do not refer to the same underlying entity and metric."
        }

    # ---------------------------------------------------------
    # 2. Compare reporting period
    # ---------------------------------------------------------

    period_a = fact_a.get("period_key", "")
    period_b = fact_b.get("period_key", "")

    if period_a and period_b and period_a != period_b:
        return {
            "relationship": "contextual_difference",
            "reason": "The facts refer to different time periods."
        }

    # ---------------------------------------------------------
    # 3. Compare scope
    # ---------------------------------------------------------

    scope_a = fact_a.get("scope_key", "")
    scope_b = fact_b.get("scope_key", "")

    if scope_a and scope_b and scope_a != scope_b:
        return {
            "relationship": "contextual_difference",
            "reason": "The facts refer to different scopes."
        }

    # ---------------------------------------------------------
    # 4. Check whether values are available
    # ---------------------------------------------------------

    value_a = normalize_value(fact_a.get("value"))
    value_b = normalize_value(fact_b.get("value"))

    if value_a is None or value_b is None:
        return {
            "relationship": "uncertain",
            "reason": (
                "The facts appear comparable, but one or both "
                "facts do not contain a comparable value."
            )
        }

    # ---------------------------------------------------------
    # 5. Compare units
    # ---------------------------------------------------------

    unit_a = fact_a.get("unit_key", "")
    unit_b = fact_b.get("unit_key", "")

    if unit_a and unit_b and unit_a != unit_b:

        equivalent_units = {
            "thousand": "k",
            "k": "k",

            "m": "m",
            "mn": "m",
            "million": "m",

            "bn": "bn",
            "billion": "bn",

            "percent": "%",
            "percentage": "%",
            "%": "%",
        }

        normalized_unit_a = equivalent_units.get(unit_a, unit_a)
        normalized_unit_b = equivalent_units.get(unit_b, unit_b)

        if normalized_unit_a != normalized_unit_b:
            return {
                "relationship": "contextual_difference",
                "reason": "The facts use different units."
            }

    # ---------------------------------------------------------
    # 6. Compare normalized values
    # ---------------------------------------------------------

    if value_a == value_b:
        return {
            "relationship": "corroboration",
            "reason": (
                "Both facts report the same normalized value "
                "for the same context."
            ),
            "normalized_value_a": value_a,
            "normalized_value_b": value_b,
        }

    # ---------------------------------------------------------
    # 7. Same context but different values
    # ---------------------------------------------------------

    return {
        "relationship": "contradiction",
        "reason": (
            "The facts report different normalized values "
            "for the same context."
        ),
        "normalized_value_a": value_a,
        "normalized_value_b": value_b,
    }