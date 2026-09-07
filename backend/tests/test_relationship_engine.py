from app.reasoning.fact_normalizer import normalize_fact
from app.reasoning.relationship_engine import classify_relationship


def print_case(number, title, fact_a, fact_b):
    result = classify_relationship(fact_a, fact_b)

    print(f"CASE {number} - {title}")
    print(result)
    print()


# ---------------------------------------------------------
# CASE 1: CORROBORATION
# ---------------------------------------------------------

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

print_case(1, "CORROBORATION", fact_a, fact_b)


# ---------------------------------------------------------
# CASE 2: CONTRADICTION
# ---------------------------------------------------------

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

print_case(2, "CONTRADICTION", fact_a, fact_b)


# ---------------------------------------------------------
# CASE 3: DIFFERENT PERIOD
# ---------------------------------------------------------

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

print_case(3, "DIFFERENT PERIOD", fact_a, fact_b)


# ---------------------------------------------------------
# CASE 4: DIFFERENT SCOPE
# ---------------------------------------------------------

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

print_case(4, "DIFFERENT SCOPE", fact_a, fact_b)


# ---------------------------------------------------------
# CASE 5: SAME VALUE, DIFFERENT UNIT WORDING
# ---------------------------------------------------------

fact_a = {
    "entity_key": "company a",
    "metric_key": "employees",
    "value": 2.5,
    "unit_key": "million",
    "period_key": "2025",
    "scope_key": "global",
}

fact_b = {
    "entity_key": "company a",
    "metric_key": "employees",
    "value": 2500000,
    "unit_key": "employees",
    "period_key": "2025",
    "scope_key": "global",
}

print_case(5, "UNIT DIFFERENCE", fact_a, fact_b)


# ---------------------------------------------------------
# CASE 6: DIFFERENT METRIC
# ---------------------------------------------------------

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

print_case(6, "DIFFERENT METRIC", fact_a, fact_b)


# ---------------------------------------------------------
# CASE 7: DIFFERENT ENTITY
# ---------------------------------------------------------

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

print_case(7, "DIFFERENT ENTITY", fact_a, fact_b)
# ---------------------------------------------------------
# CASE 8: SAME VALUE, DIFFERENT MAGNITUDE REPRESENTATION
# 384K tons vs 384000 tons
# ---------------------------------------------------------

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

print_case(
    8,
    "MAGNITUDE RECONCILIATION",
    fact_a,
    fact_b
)