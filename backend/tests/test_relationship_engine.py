from app.reasoning.fact_normalizer import normalize_fact
from app.reasoning.relationship_engine import classify_relationship


def test_corroboration():
    fact_a = {
        "entity_key": "delhivery limited",
        "metric_key": "revenue from services",
        "value": 2076,
        "unit_key": "cr",
        "period_key": "q4 fy24",
        "scope_key": "india",
    }

    fact_b = {
        "entity_key": "delhivery limited",
        "metric_key": "revenue from services",
        "value": 2076,
        "unit_key": "cr",
        "period_key": "q4 fy24",
        "scope_key": "india",
    }

    result = classify_relationship(fact_a, fact_b)

    assert result["relationship"] == "corroboration"


def test_contradiction():
    fact_a = {
        "entity_key": "delhivery limited",
        "metric_key": "revenue from services",
        "value": 2076,
        "unit_key": "cr",
        "period_key": "q4 fy24",
        "scope_key": "india",
    }

    fact_b = {
        "entity_key": "delhivery limited",
        "metric_key": "revenue from services",
        "value": 2200,
        "unit_key": "cr",
        "period_key": "q4 fy24",
        "scope_key": "india",
    }

    result = classify_relationship(fact_a, fact_b)

    assert result["relationship"] == "contradiction"


def test_different_period_is_contextual_difference():
    fact_a = {
        "entity_key": "delhivery limited",
        "metric_key": "revenue from services",
        "value": 2076,
        "unit_key": "cr",
        "period_key": "q4 fy24",
        "scope_key": "india",
    }

    fact_b = {
        "entity_key": "delhivery limited",
        "metric_key": "revenue from services",
        "value": 2300,
        "unit_key": "cr",
        "period_key": "q1 fy25",
        "scope_key": "india",
    }

    result = classify_relationship(fact_a, fact_b)

    assert result["relationship"] == "contextual_difference"


def test_different_scope_is_contextual_difference():
    fact_a = {
        "entity_key": "delhivery limited",
        "metric_key": "revenue from services",
        "value": 2076,
        "unit_key": "cr",
        "period_key": "q4 fy24",
        "scope_key": "india",
    }

    fact_b = {
        "entity_key": "delhivery limited",
        "metric_key": "revenue from services",
        "value": 2500,
        "unit_key": "cr",
        "period_key": "q4 fy24",
        "scope_key": "global",
    }

    result = classify_relationship(fact_a, fact_b)

    assert result["relationship"] == "contextual_difference"


def test_different_metric_is_incomparable():
    fact_a = {
        "entity_key": "company a",
        "metric_key": "revenue",
        "value": 1000,
        "unit_key": "cr",
        "period_key": "2025",
        "scope_key": "india",
    }

    fact_b = {
        "entity_key": "company a",
        "metric_key": "ebitda",
        "value": 1000,
        "unit_key": "cr",
        "period_key": "2025",
        "scope_key": "india",
    }

    result = classify_relationship(fact_a, fact_b)

    assert result["relationship"] == "incomparable"


def test_different_entity_is_incomparable():
    fact_a = {
        "entity_key": "company a",
        "metric_key": "revenue",
        "value": 1000,
        "unit_key": "cr",
        "period_key": "2025",
        "scope_key": "india",
    }

    fact_b = {
        "entity_key": "company b",
        "metric_key": "revenue",
        "value": 1000,
        "unit_key": "cr",
        "period_key": "2025",
        "scope_key": "india",
    }

    result = classify_relationship(fact_a, fact_b)

    assert result["relationship"] == "incomparable"


def test_missing_value_is_uncertain():
    fact_a = {
        "entity_key": "company a",
        "metric_key": "revenue",
        "value": None,
        "unit_key": "cr",
        "period_key": "2025",
        "scope_key": "india",
    }

    fact_b = {
        "entity_key": "company a",
        "metric_key": "revenue",
        "value": 1000,
        "unit_key": "cr",
        "period_key": "2025",
        "scope_key": "india",
    }

    result = classify_relationship(fact_a, fact_b)

    assert result["relationship"] == "uncertain"


def test_magnitude_reconciliation():
    raw_fact_a = {
        "entity": "company a",
        "metric": "freight tonnage",
        "value": 384,
        "unit": "tons",
        "period": "q4 fy24",
        "scope": "india",
        "evidence": "384K tons",
    }

    raw_fact_b = {
        "entity": "company a",
        "metric": "freight tonnage",
        "value": 384000,
        "unit": "tons",
        "period": "q4 fy24",
        "scope": "india",
        "evidence": "384000 tons",
    }

    fact_a = normalize_fact(raw_fact_a)
    fact_b = normalize_fact(raw_fact_b)

    result = classify_relationship(fact_a, fact_b)

    assert result["relationship"] == "corroboration"
    assert result["normalized_value_a"] == 384000.0
    assert result["normalized_value_b"] == 384000.0