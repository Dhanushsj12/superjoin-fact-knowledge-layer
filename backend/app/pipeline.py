from pathlib import Path
from typing import List, Dict, Any

from app.extraction.pdf_parser import extract_pdf_text
from app.extraction.chunker import create_chunks
from app.extraction.fact_extractor import extract_facts_from_chunks
from app.reasoning.fact_normalizer import normalize_fact
from app.reasoning.fact_deduplicator import deduplicate_facts

def process_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Process one PDF through the complete extraction pipeline.

    Flow:
        PDF
        -> text extraction
        -> chunking
        -> Gemini fact extraction
        -> evidence verification
        -> fact normalization
    """

    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # ---------------------------------------------------------
    # 1. Extract PDF text
    # ---------------------------------------------------------

    pages = extract_pdf_text(str(path))

    # ---------------------------------------------------------
    # 2. Create chunks
    # ---------------------------------------------------------

    chunks = create_chunks(
        pages,
        source_document=path.name
    )

    # ---------------------------------------------------------
    # 3. Extract facts using Gemini
    # ---------------------------------------------------------

    raw_facts = extract_facts_from_chunks(chunks)

    # ---------------------------------------------------------
    # 4. Normalize extracted facts
    # ---------------------------------------------------------

    normalized_facts = []

    for fact in raw_facts:
        normalized_fact = normalize_fact(fact)

        # Keep source/evidence information for traceability.
        normalized_fact["evidence"] = fact.get("evidence")
        normalized_fact["evidence_verified"] = fact.get(
            "evidence_verified",
            False
        )
        normalized_fact["page_number"] = fact.get("page_number")
        normalized_fact["source_document"] = fact.get(
            "source_document"
        )

        normalized_facts.append(normalized_fact)

    deduplicated_facts = deduplicate_facts(normalized_facts)

    return deduplicated_facts