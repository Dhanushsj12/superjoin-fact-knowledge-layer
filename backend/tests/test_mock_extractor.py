from app.extraction.pdf_parser import extract_pdf_text
from app.extraction.chunker import create_chunks
from app.extraction.mock_fact_extractor import extract_mock_facts


pdf_path = (
    "../data/delhivery/"
    "03-delhivery-q4-fy24-earnings-presentation.pdf"
)

pages = extract_pdf_text(pdf_path)

chunks = create_chunks(
    pages,
    source_document="03-delhivery-q4-fy24-earnings-presentation.pdf"
)

facts = extract_mock_facts(chunks)

print(f"\nMock facts extracted: {len(facts)}")

for fact in facts:
    print("\nFACT")
    print(f"Entity: {fact['entity']}")
    print(f"Metric: {fact['metric']}")
    print(f"Value: {fact['value']}")
    print(f"Unit: {fact['unit']}")
    print(f"Period: {fact['period']}")
    print(f"Evidence: {fact['evidence']}")