from pathlib import Path

from app.pipeline import process_pdf


project_root = Path(__file__).resolve().parents[2]

pdf_path = (
    project_root
    / "data"
    / "delhivery"
    / "03-delhivery-q4-fy24-earnings-presentation.pdf"
)


facts = process_pdf(str(pdf_path))

print(f"\nTotal normalized facts: {len(facts)}")

print("\nFirst 10 facts:\n")

for index, fact in enumerate(facts[:10], start=1):
    print(f"FACT {index}")
    print(f"Entity: {fact['entity_key']}")
    print(f"Metric: {fact['metric_key']}")
    print(f"Value: {fact['value']}")
    print(f"Unit: {fact['unit_key']}")
    print(f"Period: {fact['period_key']}")
    print(f"Scope: {fact['scope_key']}")
    print(f"Page: {fact['page_number']}")
    print(f"Evidence verified: {fact['evidence_verified']}")
    print(f"Evidence: {fact['evidence']}")
    print("-" * 60)