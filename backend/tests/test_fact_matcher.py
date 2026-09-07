from app.reasoning.fact_matcher import facts_match, compare_facts


fact_a = {
    "entity_key": "delhivery limited",
    "metric_key": "revenue from services",
    "value": 2076.0,
    "unit_key": "cr",
    "period_key": "q4 fy24",
    "scope_key": "india",
}


fact_b = {
    "entity_key": "delhivery limited",
    "metric_key": "revenue from services",
    "value": 2076.0,
    "unit_key": "cr",
    "period_key": "q4 fy24",
    "scope_key": "india",
}


fact_c = {
    "entity_key": "delhivery limited",
    "metric_key": "ebitda",
    "value": 46.0,
    "unit_key": "cr",
    "period_key": "q4 fy24",
    "scope_key": "india",
}


print("Same facts:", facts_match(fact_a, fact_b))
print("Different metrics:", facts_match(fact_a, fact_c))

result = compare_facts(fact_a, fact_b)

print("\nComparison result:")
print(result)