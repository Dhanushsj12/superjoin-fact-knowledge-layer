from app.reasoning.fact_normalizer import normalize_fact


def test_normalize_dollar_billion():
    fact = {
        "metric": "direct spend",
        "value": 216,
        "unit": "$ billion",
        "evidence": "The Indian logistics sector had a direct spend of US$216 billion in Fiscal 2020",
        "page_number": 3,
        "source_document": "test.pdf",
    }

    result = normalize_fact(fact)

    assert result["value"] == 216_000_000_000
    assert result["unit"] == "$"


def test_normalize_plain_million():
    fact = {
        "metric": "capacity",
        "value": 3.70,
        "unit": "million",
        "evidence": "Rated Automated Sort Capacity of 3.70 million",
        "page_number": 43,
        "source_document": "test.pdf",
    }

    result = normalize_fact(fact)

    assert result["value"] == 3_700_000
    assert result["unit"] == ""


def test_normalize_million_orders():
    fact = {
        "metric": "volume",
        "value": 148.49,
        "unit": "million orders",
        "evidence": "Our shipment volume grew from 148.49 million orders in Fiscal 2019",
        "page_number": 46,
        "source_document": "test.pdf",
    }

    result = normalize_fact(fact)

    assert result["value"] == 148_490_000
    assert result["unit"] == "orders"


def test_normalize_million_tonnes():
    fact = {
        "metric": "volume",
        "value": 4.8,
        "unit": "million tonnes",
        "evidence": "4.8 Mn Tons PTL freight tonnage since inception",
        "page_number": 6,
        "source_document": "test.pdf",
    }

    result = normalize_fact(fact)

    assert result["value"] == 4_800_000
    assert result["unit"] == "tonnes"


def test_normalize_mw():
    fact = {
        "metric": "capacity",
        "value": 8,
        "unit": "MW",
        "evidence": "total sanctioned capacity of 8 MW",
        "page_number": 1,
        "source_document": "test.pdf",
    }

    result = normalize_fact(fact)

    assert result["value"] == 8
    assert result["unit"] == "mw"


def test_normalize_rupees_million():
    fact = {
        "metric": "revenue",
        "value": 81415.38,
        "unit": "₹ million",
        "evidence": "Revenues from customers increased to ₹81,415.38 million",
        "page_number": 10,
        "source_document": "test.pdf",
    }

    result = normalize_fact(fact)

    assert result["value"] == 81_415_380_000
    assert result["unit"] == "₹"