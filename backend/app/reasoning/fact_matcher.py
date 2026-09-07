from typing import Dict, Any


def facts_match(fact_a: Dict[str, Any], fact_b: Dict[str, Any]) -> bool:
    """
    Determine whether two facts refer to the same underlying
    metric/entity combination.

    This does NOT decide whether the facts agree or contradict.
    It only determines whether they are comparable.

    Example:
        Fact A:
            Delhivery Limited
            Revenue from Services
            Q4 FY24

        Fact B:
            Delhivery
            Revenue from services
            Q4 FY24

        Result:
            True
    """

    entity_a = fact_a.get("entity_key", "")
    entity_b = fact_b.get("entity_key", "")

    metric_a = fact_a.get("metric_key", "")
    metric_b = fact_b.get("metric_key", "")

    # Entity must match when both facts provide an entity.
    if entity_a and entity_b:
        if entity_a != entity_b:
            return False

    # Metric is the most important field for matching.
    if not metric_a or not metric_b:
        return False

    if metric_a != metric_b:
        return False

    return True


def get_match_reason(
    fact_a: Dict[str, Any],
    fact_b: Dict[str, Any]
) -> str:
    """
    Explain why two facts were considered comparable.
    """

    entity_a = fact_a.get("entity_key", "")
    entity_b = fact_b.get("entity_key", "")

    metric_a = fact_a.get("metric_key", "")
    metric_b = fact_b.get("metric_key", "")

    if metric_a != metric_b:
        return "Metrics are different."

    if entity_a and entity_b and entity_a != entity_b:
        return "Entities are different."

    if entity_a and entity_b:
        return "Entity and metric match."

    return "Metric matches; entity information is incomplete."


def compare_facts(
    fact_a: Dict[str, Any],
    fact_b: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare two normalized facts and return a structured
    matching result.

    This function intentionally does not determine
    corroboration or contradiction yet.
    """

    matched = facts_match(fact_a, fact_b)

    return {
        "matched": matched,
        "reason": get_match_reason(fact_a, fact_b),
        "fact_a": fact_a,
        "fact_b": fact_b,
    }