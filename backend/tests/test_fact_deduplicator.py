from app.reasoning.fact_deduplicator import (
    build_fact_identity,
    deduplicate_facts,
)


def test_same_fact_in_same_document_is_deduplicated():

    facts = [
        {
            "entity_key": "acme",
            "metric_key": "revenue",
            "value": 1000.0,
            "unit_key": "cr",
            "period_key": "fy2025",
            "scope_key": "",
            "evidence": "Revenue was 1,000 Cr",
            "page_number": 5,
            "source_document": "report_a.pdf",
        },
        {
            "entity_key": "acme",
            "metric_key": "revenue",
            "value": 1000.0,
            "unit_key": "cr",
            "period_key": "fy2025",
            "scope_key": "",
            "evidence": "Revenue was 1,000 Cr",
            "page_number": 9,
            "source_document": "report_a.pdf",
        },
    ]

    result = deduplicate_facts(facts)

    assert len(result) == 1
    assert len(result[0]["evidence_occurrences"]) == 2


def test_same_fact_across_documents_is_preserved():

    facts = [
        {
            "entity_key": "acme",
            "metric_key": "revenue",
            "value": 1000.0,
            "unit_key": "cr",
            "period_key": "fy2025",
            "scope_key": "",
            "evidence": "Revenue was 1,000 Cr",
            "page_number": 5,
            "source_document": "report_a.pdf",
        },
        {
            "entity_key": "acme",
            "metric_key": "revenue",
            "value": 1000.0,
            "unit_key": "cr",
            "period_key": "fy2025",
            "scope_key": "",
            "evidence": "Revenue amounted to 1,000 Cr",
            "page_number": 12,
            "source_document": "report_b.pdf",
        },
    ]

    result = deduplicate_facts(facts)

    assert len(result) == 2


def test_different_facts_are_not_deduplicated():

    facts = [
        {
            "entity_key": "acme",
            "metric_key": "revenue",
            "value": 1000.0,
            "unit_key": "cr",
            "period_key": "fy2025",
            "scope_key": "",
            "evidence": "Revenue was 1,000 Cr",
            "page_number": 5,
            "source_document": "report_a.pdf",
        },
        {
            "entity_key": "acme",
            "metric_key": "profit",
            "value": 100.0,
            "unit_key": "cr",
            "period_key": "fy2025",
            "scope_key": "",
            "evidence": "Profit was 100 Cr",
            "page_number": 6,
            "source_document": "report_a.pdf",
        },
    ]

    result = deduplicate_facts(facts)

    assert len(result) == 2


def test_fact_identity_is_deterministic():

    fact = {
        "entity_key": "acme",
        "metric_key": "revenue",
        "value": 1000.0,
        "unit_key": "cr",
        "period_key": "fy2025",
        "scope_key": "",
    }

    assert build_fact_identity(fact) == build_fact_identity(fact)