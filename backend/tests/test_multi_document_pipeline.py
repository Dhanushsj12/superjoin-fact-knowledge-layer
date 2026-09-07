from app.pipeline import compare_facts_across_documents


def make_fact(
    source_document,
    entity,
    metric,
    value,
    unit,
    period,
    scope=None,
    evidence="sample evidence"
):
    return {
        "entity_key": entity.lower(),
        "metric_key": metric.lower(),
        "value": value,
        "unit_key": unit.lower() if unit else "",
        "period_key": period.lower() if period else "",
        "scope_key": scope.lower() if scope else "",
        "evidence": evidence,
        "page_number": 1,
        "source_document": source_document,
    }


def test_cross_document_corroboration():

    fact_a = make_fact(
        source_document="document_a.pdf",
        entity="Example Company",
        metric="Revenue",
        value=2076,
        unit="Cr",
        period="Q4 FY24",
        evidence="Revenue was 2,076 Cr"
    )

    fact_b = make_fact(
        source_document="document_b.pdf",
        entity="Example Company",
        metric="Revenue",
        value=2076,
        unit="Cr",
        period="Q4 FY24",
        evidence="Q4 FY24 revenue stood at 2076 Cr"
    )

    relationships = compare_facts_across_documents(
        [fact_a, fact_b]
    )

    assert len(relationships) == 1

    assert relationships[0]["relationship"] == "corroboration"


def test_cross_document_contradiction():

    fact_a = make_fact(
        source_document="document_a.pdf",
        entity="Example Company",
        metric="Revenue",
        value=2076,
        unit="Cr",
        period="Q4 FY24"
    )

    fact_b = make_fact(
        source_document="document_b.pdf",
        entity="Example Company",
        metric="Revenue",
        value=2200,
        unit="Cr",
        period="Q4 FY24"
    )

    relationships = compare_facts_across_documents(
        [fact_a, fact_b]
    )

    assert len(relationships) == 1

    assert relationships[0]["relationship"] == "contradiction"


def test_different_period_is_contextual_difference():

    fact_a = make_fact(
        source_document="document_a.pdf",
        entity="Example Company",
        metric="Revenue",
        value=2076,
        unit="Cr",
        period="Q4 FY24"
    )

    fact_b = make_fact(
        source_document="document_b.pdf",
        entity="Example Company",
        metric="Revenue",
        value=2300,
        unit="Cr",
        period="Q1 FY25"
    )

    relationships = compare_facts_across_documents(
        [fact_a, fact_b]
    )

    assert len(relationships) == 1

    assert relationships[0]["relationship"] == (
        "contextual_difference"
    )


def test_different_scope_is_contextual_difference():

    fact_a = make_fact(
        source_document="document_a.pdf",
        entity="Example Company",
        metric="Revenue",
        value=2076,
        unit="Cr",
        period="Q4 FY24",
        scope="India"
    )

    fact_b = make_fact(
        source_document="document_b.pdf",
        entity="Example Company",
        metric="Revenue",
        value=2076,
        unit="Cr",
        period="Q4 FY24",
        scope="Global"
    )

    relationships = compare_facts_across_documents(
        [fact_a, fact_b]
    )

    assert len(relationships) == 1

    assert relationships[0]["relationship"] == (
        "contextual_difference"
    )


def test_different_metrics_are_not_compared():

    fact_a = make_fact(
        source_document="document_a.pdf",
        entity="Example Company",
        metric="Revenue",
        value=2076,
        unit="Cr",
        period="Q4 FY24"
    )

    fact_b = make_fact(
        source_document="document_b.pdf",
        entity="Example Company",
        metric="Profit",
        value=2076,
        unit="Cr",
        period="Q4 FY24"
    )

    relationships = compare_facts_across_documents(
        [fact_a, fact_b]
    )

    assert len(relationships) == 0