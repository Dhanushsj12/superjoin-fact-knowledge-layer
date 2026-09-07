import json
from typing import List, Dict

from .llm_client import generate_text


def extract_facts_from_chunks(chunks: List[Dict]) -> List[Dict]:
    """
    Extract structured facts from PDF chunks using Gemini.

    Each fact keeps the original evidence, page number,
    and source document for traceability.
    """

    facts = []

    for chunk in chunks:
        prompt = f"""
You are extracting factual information from a document.

Extract only meaningful numerical or semantic facts from the text below.

For each fact return these fields:

- entity: The person, company, organization, product, country, etc.
- metric: What is being measured or stated.
- value: Numerical value if available, otherwise null.
- unit: Unit such as %, INR, USD, million, tonnes, employees, etc.
- period: Time period such as FY2024, Q4 FY24, March 2024, etc.
- scope: Geographic, business, operational, or other scope if explicitly stated.
- evidence: Exact text from the document supporting the fact.

Rules:
1. Do not invent information.
2. Only extract facts actually supported by the provided text.
3. If a field is not available, use null.
4. Evidence MUST be copied exactly from the provided text.
5. Extract meaningful facts, not navigation text or decorative headings.
6. Do not calculate or infer values that are not explicitly supported.
7. Return ONLY a JSON array.
8. If there are no meaningful facts, return [].

Document text:
{chunk["chunk_text"]}
"""

        try:
            output = generate_text(prompt)

            # Gemini may wrap JSON inside Markdown code fences.
            cleaned_output = output.strip()

            if cleaned_output.startswith("```"):
                cleaned_output = cleaned_output.replace("```json", "", 1)
                cleaned_output = cleaned_output.replace("```", "", 1)
                cleaned_output = cleaned_output.strip()

            extracted = json.loads(cleaned_output)

            if not isinstance(extracted, list):
                print("Gemini returned something other than a JSON array.")
                continue

            for fact in extracted:
                fact["page_number"] = chunk["page_number"]
                fact["source_document"] = chunk.get("source_document")

                facts.append(fact)

        except json.JSONDecodeError:
            print("Could not parse Gemini response as JSON.")
            print("Gemini response:")
            print(output)

        except Exception as error:
            print(f"Gemini extraction failed: {error}")

    return facts