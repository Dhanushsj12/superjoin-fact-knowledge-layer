import json
from pathlib import Path

from app import pipeline
from app.extraction.pdf_parser import extract_pdf_text
from app.extraction.chunker import create_chunks
from app.extraction.candidate_detector import filter_candidate_chunks


def test_batched_pipeline_maps_real_pdf_evidence(
    monkeypatch
):
    """
    Verify the complete batched pipeline using a real PDF
    while replacing the external LLM with a deterministic
    response.

    This test verifies:
    - PDF parsing
    - chunking
    - candidate detection
    - batching
    - chunk mapping
    - evidence verification
    - normalization
    - deduplication
    """

    pdf_files = list(
        (
            Path(__file__).resolve().parents[2]
            / "data"
            / "delhivery"
        ).glob("*.pdf")
    )

    assert pdf_files, "No Delhivery PDF found."

    pdf_path = pdf_files[0]

    # Build the same chunks used by the real pipeline.
    pages = extract_pdf_text(str(pdf_path))

    chunks = create_chunks(
        pages,
        source_document=pdf_path.name
    )

    candidate_chunks = filter_candidate_chunks(
        chunks
    )

    assert candidate_chunks, (
        "No candidate chunks found in the test PDF."
    )

    # Use the first real candidate chunk.
    test_chunk = candidate_chunks[0]

    chunk_id = 0

    # Use a short piece of the ACTUAL source text
    # as evidence.
    evidence = test_chunk["chunk_text"][:80].strip()

    assert evidence

    def fake_generate_text(prompt):
        """
        Return valid deterministic JSON.

        The evidence comes directly from the real PDF
        chunk, so the production evidence verifier can
        validate it normally.
        """

        fact = [
            {
                "chunk_id": chunk_id,
                "entity": "Test Entity",
                "metric": "Test Metric",
                "value": 123,
                "unit": "units",
                "period": "Test Period",
                "scope": None,
                "evidence": evidence
            }
        ]

        return json.dumps(fact)

    monkeypatch.setattr(
        "app.extraction.batch_fact_extractor.generate_text",
        fake_generate_text
    )

    result = pipeline.process_documents(
        [str(pdf_path)]
    )

    # --------------------------------------------------
    # Document-level checks
    # --------------------------------------------------

    assert result["summary"]["document_count"] == 1

    assert len(result["documents"]) == 1

    assert (
        result["documents"][0]["source_document"]
        == pdf_path.name
    )

    # --------------------------------------------------
    # Fact-level checks
    # --------------------------------------------------

    assert result["summary"]["fact_count"] > 0

    fact = result["facts"][0]

    assert fact["source_document"] == pdf_path.name

    assert fact["page_number"] == test_chunk["page_number"]

    assert fact["evidence"] == evidence

    assert fact["evidence_verified"] is True

    assert fact["metric_key"] == "test metric"

    assert fact["entity_key"] == "test entity"

    assert fact["value"] == 123

    assert fact["unit_key"] == "units"

    assert fact["period_key"] == "test period"

    # --------------------------------------------------
    # Relationship check
    # --------------------------------------------------

    # Only one document is being processed, therefore
    # there cannot be a cross-document relationship.
    assert result["summary"]["relationship_count"] == 0