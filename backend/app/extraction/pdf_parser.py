from pathlib import Path
from typing import List, Dict

import pymupdf


def extract_pdf_text(pdf_path: str) -> List[Dict]:
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("The provided file must be a PDF.")

    document = pymupdf.open(pdf_path)

    pages = []

    for page_index, page in enumerate(document):
        text = page.get_text("text").strip()

        pages.append({
            "page_number": page_index + 1,
            "text": text
        })

    document.close()

    return pages