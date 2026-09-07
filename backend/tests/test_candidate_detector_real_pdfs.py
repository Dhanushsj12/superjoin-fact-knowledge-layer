from pathlib import Path

from app.extraction.pdf_parser import extract_pdf_text
from app.extraction.chunker import create_chunks
from app.extraction.candidate_detector import filter_candidate_chunks


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data" / "delhivery"


def test_candidate_filtering_on_delhivery_pdfs():
    pdf_files = list(DATA_DIR.glob("*.pdf"))

    assert pdf_files, "No Delhivery PDFs found."

    total_chunks = 0
    total_candidates = 0

    for pdf_path in pdf_files:
        pages = extract_pdf_text(str(pdf_path))

        chunks = create_chunks(
            pages,
            source_document=pdf_path.name
        )

        candidates = filter_candidate_chunks(chunks)

        total_chunks += len(chunks)
        total_candidates += len(candidates)

        print(
            f"\n{pdf_path.name}"
            f"\n  Total chunks: {len(chunks)}"
            f"\n  Candidate chunks: {len(candidates)}"
        )

    print(
        f"\nTOTAL"
        f"\n  Total chunks: {total_chunks}"
        f"\n  Candidate chunks: {total_candidates}"
    )

    assert total_chunks > 0
    assert total_candidates > 0
    assert total_candidates <= total_chunks