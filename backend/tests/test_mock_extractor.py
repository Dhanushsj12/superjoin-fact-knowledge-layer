from pathlib import Path

from app.extraction.pdf_parser import extract_pdf_text
from app.extraction.chunker import create_chunks
from app.extraction.mock_fact_extractor import extract_mock_facts


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PDF_PATH = (
    PROJECT_ROOT
    / "data"
    / "delhivery"
    / "03-delhivery-q4-fy24-earnings-presentation.pdf"
)


# ---------------------------------------------------------------------------
# Main test
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("MOCK FACT EXTRACTION TEST")
    print("=" * 70)

    # Check that the PDF exists before processing.
    if not PDF_PATH.exists():
        raise FileNotFoundError(
            f"PDF not found:\n{PDF_PATH}"
        )

    print(f"\nPDF: {PDF_PATH.name}")

    # -----------------------------------------------------------------------
    # Step 1: Extract PDF text
    # -----------------------------------------------------------------------

    pages = extract_pdf_text(PDF_PATH)

    print(f"Pages extracted: {len(pages)}")

    # -----------------------------------------------------------------------
    # Step 2: Create chunks
    # -----------------------------------------------------------------------

    chunks = create_chunks(
        pages,
        source_document=PDF_PATH.name,
    )

    print(f"Chunks created: {len(chunks)}")

    # -----------------------------------------------------------------------
    # Step 3: Extract mock facts
    # -----------------------------------------------------------------------

    facts = extract_mock_facts(chunks)

    print(f"Mock facts extracted: {len(facts)}")

    # -----------------------------------------------------------------------
    # Step 4: Display extracted facts
    # -----------------------------------------------------------------------

    if not facts:
        print("\nNo mock facts were extracted.")
        return

    print("\n" + "=" * 70)
    print("EXTRACTED FACTS")
    print("=" * 70)

    for index, fact in enumerate(facts, start=1):

        print(f"\nFACT {index}")
        print("-" * 50)

        print(f"Entity:       {fact.get('entity')}")
        print(f"Metric:       {fact.get('metric')}")
        print(f"Value:        {fact.get('value')}")
        print(f"Unit:         {fact.get('unit')}")
        print(f"Period:       {fact.get('period')}")
        print(f"Scope:        {fact.get('scope')}")

        print(f"Page:         {fact.get('page_number')}")
        print(f"Source:       {fact.get('source_document')}")

        print(f"Evidence:     {fact.get('evidence')}")

    # -----------------------------------------------------------------------
    # Step 5: Summary
    # -----------------------------------------------------------------------

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(f"PDF:           {PDF_PATH.name}")
    print(f"Pages:         {len(pages)}")
    print(f"Chunks:        {len(chunks)}")
    print(f"Mock facts:    {len(facts)}")

    print("\nMock extraction test completed successfully.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()