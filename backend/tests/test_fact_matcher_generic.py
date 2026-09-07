from app.reasoning.fact_matcher import (
    tokenize,
    text_similarity,
    facts_match,
)


def make_fact(
    entity,
    metric,
    value=1000,
    unit="cr",
    period="fy2025",
):
    return {
        "entity_key": entity,
        "metric_key": metric,
        "value": value,
        "unit_key": unit,
        "period_key": period,
        "scope_key": "",
    }


def test_exact_match():

    fact_a = make_fact(
        "acme corporation",
        "revenue"
    )

    fact_b = make_fact(
        "acme corporation",
        "revenue"
    )

    assert facts_match(fact_a, fact_b)


def test_metric_wording_variation():

    fact_a = make_fact(
        "acme corporation",
        "revenue from services"
    )

    fact_b = make_fact(
        "acme corporation",
        "services revenue"
    )

    assert facts_match(fact_a, fact_b)


def test_different_metrics_do_not_match():

    fact_a = make_fact(
        "acme corporation",
        "revenue"
    )

    fact_b = make_fact(
        "acme corporation",
        "employee count"
    )

    assert not facts_match(fact_a, fact_b)


def test_different_entities_do_not_match():

    fact_a = make_fact(
        "acme corporation",
        "revenue"
    )

    fact_b = make_fact(
        "beta corporation",
        "revenue"
    )

    assert not facts_match(fact_a, fact_b)


def test_missing_entity_can_still_match():

    fact_a = make_fact(
        "",
        "revenue"
    )

    fact_b = make_fact(
        "acme corporation",
        "revenue"
    )

    assert facts_match(fact_a, fact_b)


def test_tokenization_is_generic():

    tokens = tokenize("Revenue from Services")

    assert tokens == {
        "revenue",
        "from",
        "services",
    }


def test_similarity_is_between_zero_and_one():

    score = text_similarity(
        "revenue from services",
        "services revenue"
    )

    assert 0 <= score <= 1
    assert score > 0