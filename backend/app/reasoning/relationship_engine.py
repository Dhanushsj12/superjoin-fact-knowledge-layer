from typing import Dict, Any

from app.reasoning.fact_normalizer import normalize_number


def normalize_value_and_unit(
    value: Any,
    unit: Any
) -> Any:
    """
    Convert a fact's value into a comparable numeric representation.

    Examples:
        384 + K       -> 384000
        384000 + None -> 384000
        "2.5 million" -> 2500000

    The unit is currently used as context. Magnitude expressions
    inside the value are handled by normalize_number().
    """

    if value is None:
        return None

    return normalize_number(value)


def classify_relationship(
    fact_a: Dict[str, Any],
    fact_b: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Classify the relationship between two facts.

    Possible relationships:
    - corroboration
    - contradiction
    - contextual_difference
    - incomparable
    """

    # ---------------------------------------------------------
    # 1. Check entity
    # ---------------------------------------------------------

    entity_a = fact_a.get("entity_key", "")
    entity_b = fact_b.get("entity_key", "")

    if entity_a and entity_b and entity_a != entity_b:
        return {
            "relationship": "incomparable",
            "reason": "The entities are different."
        }

    # ---------------------------------------------------------
    # 2. Check metric
    # ---------------------------------------------------------

    metric_a = fact_a.get("metric_key", "")
    metric_b = fact_b.get("metric_key", "")

    if not metric_a or not metric_b:
        return {
            "relationship": "incomparable",
            "reason": "One or both facts are missing a metric."
        }

    if metric_a != metric_b:
        return {
            "relationship": "incomparable",
            "reason": "The metrics are different."
        }

    # ---------------------------------------------------------
    # 3. Check period
    # ---------------------------------------------------------

    period_a = fact_a.get("period_key")
    period_b = fact_b.get("period_key")

    if period_a and period_b and period_a != period_b:
        return {
            "relationship": "contextual_difference",
            "reason": "The facts refer to different time periods."
        }

    # ---------------------------------------------------------
    # 4. Check scope
    # ---------------------------------------------------------

    scope_a = fact_a.get("scope_key")
    scope_b = fact_b.get("scope_key")

    if scope_a and scope_b and scope_a != scope_b:
        return {
            "relationship": "contextual_difference",
            "reason": "The facts refer to different scopes."
        }

    # ---------------------------------------------------------
    # 5. Normalize values
    # ---------------------------------------------------------

    value_a = normalize_value_and_unit(
        fact_a.get("value"),
        fact_a.get("unit_key")
    )

    value_b = normalize_value_and_unit(
        fact_b.get("value"),
        fact_b.get("unit_key")
    )

    if value_a is None or value_b is None:
        return {
            "relationship": "incomparable",
            "reason": "One or both facts do not contain a comparable value."
        }

    # ---------------------------------------------------------
    # 6. Check units
    # ---------------------------------------------------------

    unit_a = fact_a.get("unit_key", "")
    unit_b = fact_b.get("unit_key", "")

    # If units are explicitly different and cannot be reconciled
    # through the numeric normalization above, treat them as
    # contextual differences.
    if unit_a and unit_b and unit_a != unit_b:

        # Some units are simply different textual representations.
        equivalent_units = {
            "k": "k",
            "thousand": "k",
            "m": "m",
            "mn": "m",
            "million": "m",
            "bn": "bn",
            "billion": "bn",
        }

        normalized_unit_a = equivalent_units.get(unit_a, unit_a)
        normalized_unit_b = equivalent_units.get(unit_b, unit_b)

        if normalized_unit_a != normalized_unit_b:
            return {
                "relationship": "contextual_difference",
                "reason": "The facts use different units."
            }

    # ---------------------------------------------------------
    # 7. Compare normalized values
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
    # 8. Same context, different normalized values
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