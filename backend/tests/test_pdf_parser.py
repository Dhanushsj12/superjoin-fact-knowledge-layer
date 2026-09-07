from pathlib import Path

from app.extraction.pdf_parser import extract_pdf_text
from app.extraction.chunker import create_chunks
from app.extraction.fact_extractor import extract_facts_from_chunks


# Project root
project_root = Path(__file__).resolve().parents[2]

# PDF location
pdf_path = (
    project_root
    / "data"
    / "delhivery"
    / "03-delhivery-q4-fy24-earnings-presentation.pdf"
)


# Step 1: Extract PDF pages
pages = extract_pdf_text(str(pdf_path))

print(f"Total pages extracted: {len(pages)}")


# Step 2: Create chunks
chunks = create_chunks(
    pages,
    chunk_size=1500,
    source_document=pdf_path.name
)

print(f"Total chunks created: {len(chunks)}")


# Step 3: Prepare fact candidates
facts = extract_facts_from_chunks(chunks)

print(f"Total fact candidates: {len(facts)}")


# Step 4: Show first 3 fact candidates
for fact in facts[:3]:

    print("\n==============================")

    print(f"Page: {fact['page_number']}")
    print(f"Entity: {fact['entity']}")
    print(f"Metric: {fact['metric']}")
    print(f"Value: {fact['value']}")
    print(f"Unit: {fact['unit']}")
    print(f"Period: {fact['period']}")
    print(f"Scope: {fact['scope']}")
    print(f"Source: {fact['source_document']}")

    print("\nEvidence:")
    print(fact["evidence"][:500])