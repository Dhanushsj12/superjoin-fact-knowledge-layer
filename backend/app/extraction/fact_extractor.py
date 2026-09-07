import json
from typing import List, Dict

from .llm_client import client


def extract_facts_from_chunks(chunks: List[Dict]) -> List[Dict]:
    """
    Extract structured facts from PDF chunks using an LLM.

    Each fact keeps the original evidence and page number
    so that the result can always be traced back to the PDF.
    """

    facts = []

    for chunk in chunks:
        prompt = f"""
You are extracting factual information from a document.

Extract only meaningful numerical or semantic facts from the text below.

For each fact return:
- entity
- metric
- value
- unit
- period
- scope
- evidence

Rules:
1. Do not invent information.
2. If a field is not available, use null.
3. Evidence must be copied exactly from the provided text.
4. Extract only facts that are actually supported by the text.
5. Return a JSON array.
6. Ignore navigation text, page numbers, headings, and decorative text.

Document text:
{chunk["chunk_text"]}
"""

        response = client.responses.create(
            model="gpt-5-mini",
            input=prompt,
        )

        output = response.output_text

        try:
            extracted = json.loads(output)
        except json.JSONDecodeError:
            print("Could not parse LLM response as JSON.")
            print("LLM response:")
            print(output)
            continue

        for fact in extracted:
            fact["page_number"] = chunk["page_number"]
            fact["source_document"] = chunk.get("source_document")

            facts.append(fact)

    return facts