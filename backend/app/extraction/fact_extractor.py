import json
from typing import List, Dict

from .llm_client import generate_text
from app.reasoning.evidence_verifier import verify_evidence


def extract_facts_from_chunks(chunks: List[Dict]) -> List[Dict]:
    """
    Extract meaningful structured facts from document chunks
    using the configured LLM.

    The extractor is intentionally generic and does not contain
    document-specific rules.
    """

    facts = []

    total_chunks = len(chunks)

    for index, chunk in enumerate(chunks, start=1):

        print(
            f"Processing chunk {index}/{total_chunks} "
            f"(page {chunk['page_number']})..."
        )

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

- chunk_id: The identifier of the supplied document chunk.
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
2. Do not invent values.
3. Do not calculate values.
4. Do not extract administrative/document metadata.
5. Preserve the exact evidence text from the source.
6. If a field is unavailable, return null.
7. Preserve explicit magnitude such as K, Mn, million,
   or billion.
8. Qualitative facts are allowed when meaningful and
   potentially comparable across documents.
9. Avoid duplicate facts from the same passage.

10. Return ONLY valid JSON.
11. The JSON root MUST be an object.
12. The JSON object MUST contain exactly one key: "facts".
13. "facts" MUST contain an array of fact objects.
14. Each fact object MUST contain exactly these keys:
    "chunk_id",
    "entity",
    "metric",
    "value",
    "unit",
    "period",
    "scope",
    "evidence"
15. Use null when a field is unavailable.
16. Do not include markdown.
17. Do not include explanations outside the JSON object.
18. Do not use trailing commas.
19. If no meaningful facts exist, return:
    {{"facts": []}}

Example valid response:

{{
  "facts": [
    {{
      "chunk_id": 0,
      "entity": "Example Company",
      "metric": "Revenue",
      "value": 100,
      "unit": "million USD",
      "period": "FY2025",
      "scope": null,
      "evidence": "Example Company reported revenue of 100 million USD in FY2025."
    }}
  ]
}}

The chunk_id MUST correspond to the supplied document chunk.

Document chunk ID:
0

Document text:

{chunk["chunk_text"]}
"""

        try:

            output = generate_text(prompt)

            cleaned_output = output.strip()

            # Defensive handling in case an LLM still returns
            # a markdown code block.
            if cleaned_output.startswith("```"):

                cleaned_output = cleaned_output.replace(
                    "```json",
                    "",
                    1
                )

                cleaned_output = cleaned_output.replace(
                    "```",
                    "",
                    1
                )

                cleaned_output = cleaned_output.strip()

            parsed = json.loads(cleaned_output)

            # Preferred format:
            #
            # {
            #     "facts": [...]
            # }
            if (
                isinstance(parsed, dict)
                and isinstance(parsed.get("facts"), list)
            ):

                extracted = parsed["facts"]

            # Backward compatibility for older tests/mocks
            # returning a raw JSON array.
            elif isinstance(parsed, list):

                extracted = parsed

            else:

                print(
                    "LLM returned an unexpected JSON structure."
                )

                continue

            for fact in extracted:

                if not isinstance(fact, dict):
                    continue

                # Since this function processes one chunk at a time,
                # the chunk ID should be 0.
                chunk_id = fact.get("chunk_id")

                if chunk_id is not None and chunk_id != 0:
                    continue

                fact["page_number"] = chunk["page_number"]

                fact["source_document"] = (
                    chunk.get("source_document")
                )

                fact["evidence_verified"] = verify_evidence(
                    fact,
                    chunk["chunk_text"]
                )

                # Only retain facts whose evidence can actually
                # be found in the source document.
                if fact["evidence_verified"]:
                    facts.append(fact)

        except json.JSONDecodeError:

            print(
                "Could not parse LLM response as JSON."
            )

            continue

        except Exception as error:

            error_text = str(error)

            if (
                "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
                or "rate_limit" in error_text.lower()
            ):

                print(
                    "LLM rate limit reached. "
                    "Stopping extraction gracefully."
                )

                break

            print(
                f"LLM extraction failed: {error}"
            )

    print(
        f"Extraction complete: {len(facts)} verified facts "
        f"from {total_chunks} chunks."
    )

    return facts