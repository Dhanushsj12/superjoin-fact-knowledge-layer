from pathlib import Path
from typing import List, Dict, Any

from app.extraction.pdf_parser import extract_pdf_text
from app.extraction.chunker import create_chunks
from app.extraction.candidate_detector import filter_candidate_chunks
from app.extraction.batch_fact_extractor import extract_facts_from_batches
from app.reasoning.fact_normalizer import normalize_fact
from app.reasoning.fact_deduplicator import deduplicate_facts
from app.reasoning.relationship_engine import classify_relationship


def process_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Process one PDF through the extraction pipeline.

    PDF
      -> text extraction
      -> chunking
      -> candidate detection
      -> fact extraction
      -> evidence verification
      -> normalization
      -> deduplication
    """

    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("The provided file must be a PDF.")

    pages = extract_pdf_text(str(path))

    chunks = create_chunks(
        pages,
        source_document=path.name
    )

    # Filter chunks before sending them to the LLM.
    # This reduces unnecessary API calls while keeping
    # the extraction logic document-agnostic.
    candidate_chunks = filter_candidate_chunks(chunks)

    print(
        f"Candidate filtering: {len(candidate_chunks)} "
        f"of {len(chunks)} chunks selected for fact extraction."
    )

    raw_facts = extract_facts_from_batches(
    candidate_chunks,
    batch_size=3
)

    normalized_facts = []

    for fact in raw_facts:
        normalized_fact = normalize_fact(fact)

        normalized_fact["evidence"] = fact.get("evidence")

        normalized_fact["evidence_verified"] = fact.get(
            "evidence_verified",
            False
        )

        normalized_fact["page_number"] = fact.get(
            "page_number"
        )

        normalized_fact["source_document"] = fact.get(
            "source_document"
        )

        normalized_facts.append(normalized_fact)

    deduplicated_facts = deduplicate_facts(
        normalized_facts
    )

    return deduplicated_facts


def compare_facts_across_documents(
    facts: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Compare facts originating from different source documents.

    Only facts from different documents are compared.
    """

    relationships = []

    for i in range(len(facts)):
        for j in range(i + 1, len(facts)):

            fact_a = facts[i]
            fact_b = facts[j]

            source_a = fact_a.get(
                "source_document",
                ""
            )

            source_b = fact_b.get(
                "source_document",
                ""
            )

            # Do not compare facts against themselves
            # or facts from the same document.
            if not source_a or not source_b:
                continue

            if source_a == source_b:
                continue

            result = classify_relationship(
                fact_a,
                fact_b
            )

            if result["relationship"] == "incomparable":
                continue

            relationships.append({
                "fact_a": {
                    "entity_key": fact_a.get(
                        "entity_key"
                    ),
                    "metric_key": fact_a.get(
                        "metric_key"
                    ),
                    "value": fact_a.get(
                        "value"
                    ),
                    "unit_key": fact_a.get(
                        "unit_key"
                    ),
                    "period_key": fact_a.get(
                        "period_key"
                    ),
                    "scope_key": fact_a.get(
                        "scope_key"
                    ),
                    "evidence": fact_a.get(
                        "evidence"
                    ),
                    "page_number": fact_a.get(
                        "page_number"
                    ),
                    "source_document": source_a,
                },

                "fact_b": {
                    "entity_key": fact_b.get(
                        "entity_key"
                    ),
                    "metric_key": fact_b.get(
                        "metric_key"
                    ),
                    "value": fact_b.get(
                        "value"
                    ),
                    "unit_key": fact_b.get(
                        "unit_key"
                    ),
                    "period_key": fact_b.get(
                        "period_key"
                    ),
                    "scope_key": fact_b.get(
                        "scope_key"
                    ),
                    "evidence": fact_b.get(
                        "evidence"
                    ),
                    "page_number": fact_b.get(
                        "page_number"
                    ),
                    "source_document": source_b,
                },

                "relationship": result[
                    "relationship"
                ],

                "reason": result[
                    "reason"
                ],

                "normalized_value_a": result.get(
                    "normalized_value_a"
                ),

                "normalized_value_b": result.get(
                    "normalized_value_b"
                ),
            })

    return relationships


def process_documents(
    pdf_paths: List[str]
) -> Dict[str, Any]:
    """
    Process multiple arbitrary PDF documents.

    The function is document-agnostic:
    no filenames, entities, metrics, or schemas
    are hard-coded here.
    """

    if not pdf_paths:
        raise ValueError(
            "At least one PDF is required."
        )

    all_facts = []

    processed_documents = []

    for pdf_path in pdf_paths:

        path = Path(pdf_path)

        if not path.exists():
            raise FileNotFoundError(
                f"PDF not found: {pdf_path}"
            )

        facts = process_pdf(
            str(path)
        )

        all_facts.extend(facts)

        processed_documents.append({
            "source_document": path.name,
            "fact_count": len(facts),
        })

    relationships = compare_facts_across_documents(
        all_facts
    )

    return {
        "documents": processed_documents,

        "facts": all_facts,

        "relationships": relationships,

        "summary": {
            "document_count": len(
                processed_documents
            ),

            "fact_count": len(
                all_facts
            ),

            "relationship_count": len(
                relationships
            ),
        }
    }