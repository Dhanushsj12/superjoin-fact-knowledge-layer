from typing import List, Dict, Any, Tuple


def build_fact_identity(fact: Dict[str, Any]) -> Tuple:
    """
    Build a generic identity for a normalized fact.

    Facts with the same identity represent the same underlying
    fact within the same document.
    """

    return (
        fact.get("entity_key", ""),
        fact.get("metric_key", ""),
        fact.get("value"),
        fact.get("unit_key", ""),
        fact.get("period_key", ""),
        fact.get("scope_key", ""),
    )


def deduplicate_facts(facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate occurrences of the same fact within the
    same source document.

    Facts appearing in different documents are NOT removed,
    because those repetitions may represent corroboration.
    """

    unique_facts = {}
    
    for fact in facts:

        source_document = fact.get("source_document", "")
        identity = build_fact_identity(fact)

        key = (source_document, identity)

        if key not in unique_facts:
            fact_copy = dict(fact)

            fact_copy["evidence_occurrences"] = [
                {
                    "page_number": fact.get("page_number"),
                    "evidence": fact.get("evidence"),
                }
            ]

            unique_facts[key] = fact_copy

        else:
            existing = unique_facts[key]

            occurrence = {
                "page_number": fact.get("page_number"),
                "evidence": fact.get("evidence"),
            }

            if occurrence not in existing["evidence_occurrences"]:
                existing["evidence_occurrences"].append(occurrence)

    return list(unique_facts.values())