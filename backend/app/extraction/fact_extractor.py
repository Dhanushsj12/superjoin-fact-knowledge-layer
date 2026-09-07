import json
from typing import List, Dict

from .llm_client import generate_text
from app.reasoning.evidence_verifier import verify_evidence


def extract_facts_from_chunks(chunks: List[Dict]) -> List[Dict]:
    """
    Extract meaningful structured facts from document chunks using Gemini.

    The extractor is intentionally generic and does not contain
    document-specific rules.
    """

    facts = []

    total_chunks = len(chunks)

    for index, chunk in enumerate(chunks, start=1):

        print(f"Processing chunk {index}/{total_chunks} "
              f"(page {chunk['page_number']})...")

        prompt = f"""
You are a fact extraction system for a generic knowledge layer.

Your task is to extract ONLY meaningful factual statements from
the provided document text.

A meaningful fact should describe information that could be useful
for comparing knowledge across documents.

Prioritize facts such as:
- financial metrics
- operational metrics
- business performance
- growth rates
- quantities
- prices
- economic indicators
- market statistics
- company or organizational performance
- dates that define the period of a reported fact
- meaningful qualitative statements about performance, position,
  events, or conditions

Do NOT extract document metadata or administrative information such as:
- stock exchange filing codes
- stock symbols
- website addresses
- membership numbers
- digital signatures
- page numbers
- document formatting
- regulatory boilerplate
- navigation text
- contact information

For each meaningful fact return:

- entity: The person, company, organization, product, country,
  industry, or other subject of the fact.
- metric: What is being measured or stated.
- value: Numerical value if available, otherwise null.
- unit: Unit such as %, INR, USD, million, tonnes, employees, etc.
- period: Time period such as FY2024, Q4 FY24, March 2024, etc.
- scope: Geographic, business, operational, or other scope if
  explicitly stated.
- evidence: Exact text from the document supporting the fact.

Rules:
1. Extract only information explicitly supported by the text.
2. Do not invent or calculate values.
3. Do not extract administrative/document metadata.
4. Preserve the exact evidence text from the source.
5. If a field is unavailable, return null.
6. A numerical fact should retain its magnitude when explicitly
   present in the evidence, such as K, Mn, million, or billion.
7. Qualitative facts are allowed when they are meaningful and
   potentially comparable across documents.
8. Avoid duplicate facts from the same passage.
9. Return ONLY a JSON array.
10. If there are no meaningful facts, return [].

Document text:

{chunk["chunk_text"]}
"""

        try:
            output = generate_text(prompt)

            cleaned_output = output.strip()

            if cleaned_output.startswith("```"):
                cleaned_output = cleaned_output.replace(
                    "```json", "", 1
                )
                cleaned_output = cleaned_output.replace(
                    "```", "", 1
                )
                cleaned_output = cleaned_output.strip()

            extracted = json.loads(cleaned_output)

            if not isinstance(extracted, list):
                print("Gemini returned something other than a JSON array.")
                continue

            for fact in extracted:

                if not isinstance(fact, dict):
                    continue

                fact["page_number"] = chunk["page_number"]
                fact["source_document"] = chunk.get("source_document")

                fact["evidence_verified"] = verify_evidence(
                    fact,
                    chunk["chunk_text"]
                )

                # Only retain facts whose evidence can actually
                # be found in the source document.
                if fact["evidence_verified"]:
                    facts.append(fact)

        except json.JSONDecodeError:
            print("Could not parse Gemini response as JSON.")
            continue

        except Exception as error:

            error_text = str(error)

            if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                print(
                    "Gemini quota exhausted. "
                    "Stopping extraction gracefully."
                )
                break

            print(f"Gemini extraction failed: {error}")

    print(
        f"Extraction complete: {len(facts)} verified facts "
        f"from {total_chunks} chunks."
    )

    return facts