import json
from typing import List, Dict

from .llm_client import generate_text
from app.reasoning.evidence_verifier import verify_evidence
from app.extraction.batch_processor import create_batches


def extract_facts_from_batches(
    chunks: List[Dict],
    batch_size: int = 10
) -> List[Dict]:
    """
    Extract meaningful structured facts from document chunks
    in batches using the configured LLM.

    The extractor is generic and document-agnostic.
    """

    batches = create_batches(
        chunks,
        batch_size=batch_size
    )

    facts = []
    total_batches = len(batches)

    for batch_index, batch in enumerate(
        batches,
        start=1
    ):

        print(
            f"Processing batch {batch_index}/"
            f"{total_batches} "
            f"({len(batch)} chunks)..."
        )

        numbered_chunks = []

        for chunk_index, chunk in enumerate(batch):

            numbered_chunks.append({
                "chunk_id": chunk_index,
                "page_number": chunk.get("page_number"),
                "source_document": chunk.get(
                    "source_document"
                ),
                "chunk_text": chunk.get(
                    "chunk_text",
                    ""
                ),
            })

        # ---------------------------------------------------------
        # Generic fact extraction prompt
        # ---------------------------------------------------------

        prompt = """
Extract meaningful facts from the document passages below.

A fact is information that can potentially be compared with
facts from other documents.

Examples of useful facts:
- financial metrics
- operational metrics
- business performance
- growth rates
- quantities
- prices
- economic indicators
- market statistics
- company performance
- meaningful qualitative statements

Ignore:
- filing codes
- stock symbols
- URLs
- membership numbers
- digital signatures
- page numbers
- formatting information
- navigation text
- contact information
- generic regulatory boilerplate

For every fact provide exactly these fields:

chunk_id
entity
metric
value
unit
period
scope
evidence

Rules:

- Use only information explicitly present in the supplied text.
- Never invent information.
- Never calculate values.
- Preserve explicit units and magnitudes.
- Preserve the exact evidence wording from the document.
- Use null when a field is not available.
- Qualitative facts are allowed when meaningful.
- Avoid duplicate facts from the same passage.
- chunk_id must identify the passage containing the evidence.

Return ONLY valid JSON.

The JSON must have exactly one top-level key called "facts".

The value of "facts" must be an array.

Each array item must contain only these fields:

chunk_id
entity
metric
value
unit
period
scope
evidence

Example:

{
  "facts": [
    {
      "chunk_id": 0,
      "entity": "Example Company",
      "metric": "Revenue",
      "value": 100,
      "unit": "million USD",
      "period": "FY2025",
      "scope": null,
      "evidence": "Example Company reported revenue of 100 million USD in FY2025."
    }
  ]
}

If no meaningful facts are present, return exactly:

{
  "facts": []
}

Do not return markdown.
Do not return explanations.
Do not return additional keys.
"""


        # ---------------------------------------------------------
        # Add document passages
        # ---------------------------------------------------------

        for item in numbered_chunks:

            prompt += f"""

CHUNK_ID: {item["chunk_id"]}

PAGE_NUMBER: {item["page_number"]}

SOURCE_DOCUMENT: {item["source_document"]}

DOCUMENT TEXT:
{item["chunk_text"]}

"""


        # ---------------------------------------------------------
        # Call LLM
        # ---------------------------------------------------------

        try:

            output = generate_text(prompt)

            cleaned_output = output.strip()


            # -----------------------------------------------------
            # Defensive markdown removal
            # -----------------------------------------------------

            if cleaned_output.startswith("```"):

                if cleaned_output.startswith("```json"):
                    cleaned_output = cleaned_output[
                        len("```json"):
                    ]

                elif cleaned_output.startswith("```"):
                    cleaned_output = cleaned_output[
                        len("```"):
                    ]

                if cleaned_output.endswith("```"):
                    cleaned_output = cleaned_output[
                        :-len("```")
                    ]

                cleaned_output = cleaned_output.strip()


            # -----------------------------------------------------
            # Parse JSON
            # -----------------------------------------------------

            parsed = json.loads(cleaned_output)


            # -----------------------------------------------------
            # Expected structure:
            #
            # {
            #     "facts": [...]
            # }
            # -----------------------------------------------------

            if (
                isinstance(parsed, dict)
                and isinstance(
                    parsed.get("facts"),
                    list
                )
            ):

                extracted = parsed["facts"]


            # -----------------------------------------------------
            # Backward compatibility with older tests/mocks
            # -----------------------------------------------------

            elif isinstance(parsed, list):

                extracted = parsed


            else:

                print(
                    "LLM returned an unexpected JSON structure."
                )

                continue


            # -----------------------------------------------------
            # Validate and enrich extracted facts
            # -----------------------------------------------------

            for fact in extracted:

                if not isinstance(fact, dict):
                    continue


                chunk_id = fact.get("chunk_id")


                # chunk_id must be an integer
                if not isinstance(chunk_id, int):
                    continue


                # chunk_id must point to an actual batch item
                if (
                    chunk_id < 0
                    or chunk_id >= len(batch)
                ):
                    continue


                source_chunk = batch[chunk_id]


                # -------------------------------------------------
                # Add source metadata from our pipeline.
                #
                # These are NOT generated by the LLM.
                # -------------------------------------------------

                fact["page_number"] = (
                    source_chunk.get(
                        "page_number"
                    )
                )

                fact["source_document"] = (
                    source_chunk.get(
                        "source_document"
                    )
                )


                # -------------------------------------------------
                # Verify that the evidence actually exists
                # in the original source chunk.
                # -------------------------------------------------

                evidence_verified = verify_evidence(
                    fact,
                    source_chunk.get(
                        "chunk_text",
                        ""
                    )
                )

                fact["evidence_verified"] = (
                    evidence_verified
                )


                # -------------------------------------------------
                # Only retain grounded facts.
                # -------------------------------------------------

                if evidence_verified:

                    facts.append(fact)


        # ---------------------------------------------------------
        # Error handling
        # ---------------------------------------------------------

        except json.JSONDecodeError:

            print(
                "Could not parse LLM response as JSON."
            )

            continue


        except Exception as error:

            error_text = str(error)


            # -----------------------------------------------------
            # Rate-limit handling
            # -----------------------------------------------------

            if (
                "429" in error_text
                or "RESOURCE_EXHAUSTED"
                in error_text
                or "rate_limit"
                in error_text.lower()
            ):

                print(
                    "LLM rate limit reached. "
                    "Stopping batch extraction gracefully."
                )

                break


            # -----------------------------------------------------
            # General LLM failure
            # -----------------------------------------------------

            print(
                f"LLM batch extraction failed: "
                f"{error}"
            )


    # -------------------------------------------------------------
    # Final result
    # -------------------------------------------------------------

    print(
        f"Batch extraction complete: "
        f"{len(facts)} verified facts."
    )

    return facts