import sys

sys.path.insert(0, "backend")

from app.extraction.fallback_extractor import extract_facts_fallback


def make_chunk(text):
    return {
        "chunk_id": 1,
        "page_number": 1,
        "source_document": "test.pdf",
        "chunk_text": text,
    }


# ---------------------------------------------------------------------------
# Existing fallback extraction tests
# ---------------------------------------------------------------------------

def test_reject_revenue_footnote_numbers():
    facts = extract_facts_fallback([
        make_chunk("Revenue from services(1,2)")
    ])

    assert not any(
        f["metric"] == "revenue"
        and f["value"] in {1, 2}
        for f in facts
    )


def test_extract_revenue_after_metric():
    facts = extract_facts_fallback([
        make_chunk("Revenue was ₹8,142 Cr in FY24.")
    ])

    revenue = [
        f for f in facts
        if f["metric"] == "revenue"
    ]

    assert revenue
    assert revenue[0]["value"] == 8142


def test_extract_revenue_with_magnitude():
    facts = extract_facts_fallback([
        make_chunk(
            "The company reported revenue of $1 billion."
        )
    ])

    revenue = [
        f for f in facts
        if f["metric"] == "revenue"
    ]

    assert revenue
    assert revenue[0]["value"] == 1
    assert revenue[0]["unit"] == "$ billion"


def test_do_not_extract_formula_reference_as_revenue():
    facts = extract_facts_fallback([
        make_chunk(
            "Total Scope 1 and Scope 2 GHG emissions/"
            "Revenue from operations"
        )
    ])

    assert not any(
        f["metric"] == "revenue"
        for f in facts
    )


def test_extract_capacity_value():
    facts = extract_facts_fallback([
        make_chunk(
            "The company has a Rated Automated Sort Capacity "
            "of 3.70 million shipments per day."
        )
    ])

    capacity = [
        f for f in facts
        if f["metric"] == "capacity"
    ]

    assert capacity
    assert capacity[0]["value"] == 3.70


def test_reject_section_reference():
    facts = extract_facts_fallback([
        make_chunk(
            "Revenue as described in Section 36."
        )
    ])

    assert not any(
        f["metric"] == "revenue"
        and f["value"] == 36
        for f in facts
    )


# ---------------------------------------------------------------------------
# Regression tests from six-PDF validation
# ---------------------------------------------------------------------------

def test_reject_fiscal_year_component():
    facts = extract_facts_fallback([
        make_chunk(
            "Investment announcements during 2024-25."
        )
    ])

    assert not any(
        f["value"] == 25
        for f in facts
    )


def test_reject_numbered_section_reference():
    facts = extract_facts_fallback([
        make_chunk(
            "2.1 Revenue Receipts"
        )
    ])

    assert not any(
        f["metric"] == "revenue"
        and f["value"] == 2.1
        for f in facts
    )


def test_reject_slash_footnote_reference():
    facts = extract_facts_fallback([
        make_chunk(
            "General government debt 4/"
        )
    ])

    assert not any(
        f["metric"] == "debt"
        for f in facts
    )


def test_reject_employee_footnote_reference():
    facts = extract_facts_fallback([
        make_chunk(
            "Compensation of employees 5/"
        )
    ])

    assert not any(
        f["metric"] == "employees"
        for f in facts
    )


def test_reject_foreign_investment_numbered_reference():
    facts = extract_facts_fallback([
        make_chunk(
            "1 Foreign Investment, Net (a+b)"
        )
    ])

    assert not any(
        f["metric"] == "investment"
        and f["value"] == 1
        for f in facts
    )


def test_reject_rupee_debt_service_reference():
    facts = extract_facts_fallback([
        make_chunk(
            "6 Rupee Debt Service"
        )
    ])

    assert not any(
        f["metric"] == "debt"
        and f["value"] == 6
        for f in facts
    )


def test_reject_percent_of_gdp_as_gdp_fact():
    facts = extract_facts_fallback([
        make_chunk(
            "The deficit was 3.3 percent of GDP."
        )
    ])

    assert not any(
        f["metric"] == "gdp"
        for f in facts
    )


def test_per_cent_is_percentage():
    facts = extract_facts_fallback([
        make_chunk(
            "Exports rose by 6.4 per cent."
        )
    ])

    exports = [
        f for f in facts
        if f["metric"] == "exports"
    ]

    assert exports
    assert exports[0]["value"] == 6.4
    assert exports[0]["unit"] == "%"


def test_reject_percent_tariff_as_exports():
    facts = extract_facts_fallback([
        make_chunk(
            "Subject to 50 percent tariffs on merchandise "
            "exports to the U.S."
        )
    ])

    assert not any(
        f["metric"] == "exports"
        and f["value"] == 50
        for f in facts
    )


def test_reject_capacity_share_percent():
    facts = extract_facts_fallback([
        make_chunk(
            "Increasing the share of installed electricity "
            "capacity from non-fossil-fuel sources to 50 percent."
        )
    ])

    assert not any(
        f["metric"] == "capacity"
        and f["value"] == 50
        for f in facts
    )


def test_reject_bps_as_revenue():
    facts = extract_facts_fallback([
        make_chunk(
            "Revenue increased by 781 bps."
        )
    ])

    assert not any(
        f["metric"] == "revenue"
        and f["value"] == 781
        for f in facts
    )


def test_reject_bps_as_profit():
    facts = extract_facts_fallback([
        make_chunk(
            "Profit improved by 1048 bps."
        )
    ])

    assert not any(
        f["metric"] == "profit"
        and f["value"] == 1048
        for f in facts
    )


def test_do_not_call_growth_market_share():
    facts = extract_facts_fallback([
        make_chunk(
            "PTL: 30%+ YoY growth with significant "
            "improvement in profitability and market share"
        )
    ])

    assert not any(
        f["metric"] == "market share"
        and f["value"] == 30
        for f in facts
    )


def test_extract_yoy_growth_percentage():
    facts = extract_facts_fallback([
        make_chunk(
            "Revenue grew by 30% YoY."
        )
    ])

    growth = [
        f for f in facts
        if f["metric"] == "growth"
    ]

    assert growth
    assert growth[0]["value"] == 30
    assert growth[0]["unit"] == "%"


def test_reject_investment_date_fragment():
    facts = extract_facts_fallback([
        make_chunk(
            "Mar '24 on deposits and investments."
        )
    ])

    assert not any(
        f["metric"] == "investment"
        and f["value"] == 24
        for f in facts
    )


def test_reject_esop_number_as_employee_count():
    facts = extract_facts_fallback([
        make_chunk(
            "Employees receiving ESOP grants: 22,220,370."
        )
    ])

    assert not any(
        f["metric"] == "employees"
        and f["value"] == 22220370
        for f in facts
    )


def test_reject_top_customers_number():
    facts = extract_facts_fallback([
        make_chunk(
            "The company served its top 100 customers."
        )
    ])

    assert not any(
        f["metric"] == "customers"
        and f["value"] == 100
        for f in facts
    )


def test_reject_revenue_from_contracts_with_customers():
    facts = extract_facts_fallback([
        make_chunk(
            "Revenue from contracts with customers was "
            "₹26,438.66 million."
        )
    ])

    assert not any(
        f["metric"] == "customers"
        and f["value"] == 26438.66
        for f in facts
    )


def test_reject_injury_rate_as_employee_count():
    facts = extract_facts_fallback([
        make_chunk(
            "Injury rate was 0.2 per thousand employees."
        )
    ])

    assert not any(
        f["metric"] == "employees"
        and f["value"] == 0.2
        for f in facts
    )


def test_reject_ifrs_loss_reference():
    facts = extract_facts_fallback([
        make_chunk(
            "losses, although timing for IFRS-9 recognition "
            "may vary."
        )
    ])

    assert not any(
        f["metric"] == "loss"
        for f in facts
    )


def test_reject_production_process_reference():
    facts = extract_facts_fallback([
        make_chunk(
            "The production process uses recycled materials."
        )
    ])

    assert not any(
        f["metric"] == "production"
        for f in facts
    )


def test_reject_production_function_reference():
    facts = extract_facts_fallback([
        make_chunk(
            "The analysis uses production functions at the "
            "industry level."
        )
    ])

    assert not any(
        f["metric"] == "production"
        for f in facts
    )


def test_reject_page_reference():
    facts = extract_facts_fallback([
        make_chunk(
            "Debt Sustainability Assessment ... 56"
        )
    ])

    assert not any(
        f["metric"] == "debt"
        and f["value"] == 56
        for f in facts
    )


def test_reject_paragraph_reference():
    facts = extract_facts_fallback([
        make_chunk(
            "See paragraph 23 for the detailed discussion."
        )
    ])

    assert not any(
        f["value"] == 23
        for f in facts
    )


def test_reject_percent_of_gdp_fiscal_anchor():
    facts = extract_facts_fallback([
        make_chunk(
            "The fiscal anchor is 4.4 percent of GDP."
        )
    ])

    assert not any(
        f["metric"] == "gdp"
        and f["value"] == 4.4
        for f in facts
    )


def test_reject_installed_capacity_share():
    facts = extract_facts_fallback([
        make_chunk(
            "The share of installed electricity capacity "
            "from non-fossil-fuel sources reached 50 percent."
        )
    ])

    assert not any(
        f["metric"] == "capacity"
        and f["value"] == 50
        for f in facts
    )


# ---------------------------------------------------------------------------
# Evidence integrity tests
# ---------------------------------------------------------------------------

def test_fact_contains_source_information():
    facts = extract_facts_fallback([
        make_chunk(
            "Revenue was ₹8,142 Cr in FY24."
        )
    ])

    revenue = [
        f for f in facts
        if f["metric"] == "revenue"
    ]

    assert revenue

    fact = revenue[0]

    assert fact["chunk_id"] == 1
    assert fact["page_number"] == 1
    assert fact["source_document"] == "test.pdf"
    assert fact["evidence"]


def test_evidence_contains_original_statement():
    statement = "Revenue was ₹8,142 Cr in FY24."

    facts = extract_facts_fallback([
        make_chunk(statement)
    ])

    revenue = [
        f for f in facts
        if f["metric"] == "revenue"
    ]

    assert revenue
    assert statement in revenue[0]["evidence"]