import re
from typing import Dict, Any


def tokenize(text: str) -> set[str]:
    """
    Convert text into normalized word tokens.

    This is intentionally generic and does not contain
    document-specific terminology.
    """

    if not text:
        return set()

    text = str(text).lower()

    text = re.sub(r"[^a-z0-9]+", " ", text)

    return {
        token
        for token in text.split()
        if token
    }


def text_similarity(text_a: str, text_b: str) -> float:
    """
    Calculate simple token-based similarity using Jaccard similarity.

    Returns a value between 0 and 1.
    """

    tokens_a = tokenize(text_a)
    tokens_b = tokenize(text_b)

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b

    return len(intersection) / len(union)


def entities_match(
    fact_a: Dict[str, Any],
    fact_b: Dict[str, Any]
) -> bool:
    """
    Determine whether two facts refer to compatible entities.

    If either entity is missing, matching is allowed to continue
    using the metric and context.
    """

    entity_a = fact_a.get("entity_key", "")
    entity_b = fact_b.get("entity_key", "")

    if not entity_a or not entity_b:
        return True

    if entity_a == entity_b:
        return True

    return text_similarity(entity_a, entity_b) >= 0.6


def metrics_match(
    fact_a: Dict[str, Any],
    fact_b: Dict[str, Any],
    threshold: float = 0.5
) -> bool:
    """
    Determine whether two facts describe a sufficiently similar metric.

    Exact matches are accepted immediately. Otherwise a generic
    token similarity score is used.
    """

    metric_a = fact_a.get("metric_key", "")
    metric_b = fact_b.get("metric_key", "")

    if not metric_a or not metric_b:
        return False

    if metric_a == metric_b:
        return True

    return text_similarity(metric_a, metric_b) >= threshold


def facts_match(
    fact_a: Dict[str, Any],
    fact_b: Dict[str, Any]
) -> bool:
    """
    Determine whether two facts refer to the same underlying
    metric/entity concept.

    This does NOT determine whether the values agree.
    """

    if not entities_match(fact_a, fact_b):
        return False

    if not metrics_match(fact_a, fact_b):
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

    if not metrics_match(fact_a, fact_b):
        return "Metrics are not sufficiently similar."

    if not entities_match(fact_a, fact_b):
        return "Entities are not sufficiently similar."

    if metric_a == metric_b and entity_a == entity_b:
        return "Entity and metric match exactly."

    if metric_a != metric_b:
        return "Metrics are semantically similar."

    if entity_a != entity_b:
        return "Entities are semantically similar."

    return "Facts are sufficiently similar to compare."


def compare_facts(
    fact_a: Dict[str, Any],
    fact_b: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare two normalized facts and return a structured
    matching result.
    """

    matched = facts_match(fact_a, fact_b)

    return {
        "matched": matched,
        "reason": get_match_reason(fact_a, fact_b),
        "fact_a": fact_a,
        "fact_b": fact_b,
    }