import json
from typing import List, Dict

from app.extraction.llm_client import generate_text
from app.reasoning.evidence_verifier import verify_evidence
from app.extraction.batch_processor import create_batches


def extract_facts_from_batches(
    chunks: List[Dict],
    batch_size: int = 10
) -> List[Dict]:
    """
    Extract facts from multiple candidate chunks in batches.

    Each chunk is assigned a temporary chunk_id so that facts
    returned by the LLM can be mapped back to the original
    document and page.

    This function is document-agnostic.
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
                "page_number": chunk.get(
                    "page_number"
                ),
                "source_document": chunk.get(
                    "source_document"
                ),
                "chunk_text": chunk.get(
                    "chunk_text",
                    ""
                ),
            })

        prompt_parts = [
            """
You are a generic fact extraction system.

Extract only meaningful factual statements from
the supplied document passages.

A meaningful fact should describe information that
could be useful for comparing knowledge across
documents.

Prioritize:
- financial metrics
- operational metrics
- business performance
- growth rates
- quantities
- prices
- economic indicators
- market statistics
- company or organizational performance
- meaningful qualitative statements

Do NOT extract:
- stock exchange filing codes
- stock symbols
- website addresses
- membership numbers
- digital signatures
- page numbers
- formatting information
- regulatory boilerplate
- navigation text
- contact information

For every fact return:

- chunk_id
- entity
- metric
- value
- unit
- period
- scope
- evidence

Rules:

1. Extract only information explicitly supported
   by the supplied text.

2. Do not invent values.

3. Do not calculate values.

4. Preserve the exact evidence text.

5. If a field is unavailable, return null.

6. Preserve explicit magnitude such as K, Mn,
   million, or billion.

7. Qualitative facts are allowed when meaningful.

8. Avoid duplicate facts from the same passage.

9. Return ONLY a JSON object with a single key
   called "facts".

10. The "facts" value must be a JSON array.

11. If no meaningful facts exist, return:
    {"facts": []}

The chunk_id MUST correspond to the supplied
chunk containing the evidence.
"""
        ]

        for item in numbered_chunks:

            prompt_parts.append(
                f"""
CHUNK_ID: {item["chunk_id"]}
PAGE_NUMBER: {item["page_number"]}
SOURCE_DOCUMENT: {item["source_document"]}

DOCUMENT TEXT:
{item["chunk_text"]}
"""
            )

        prompt = "\n".join(prompt_parts)

        try:

            output = generate_text(prompt)

            cleaned_output = output.strip()

            # Keep this as a defensive fallback even though
            # Groq JSON mode should normally return plain JSON.
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

            parsed = json.loads(
                cleaned_output
            )

            # Preferred Groq JSON format:
            #
            # {
            #     "facts": [...]
            # }
            if (
                isinstance(parsed, dict)
                and isinstance(parsed.get("facts"), list)
            ):

                extracted = parsed["facts"]

            # Backward compatibility for tests/mocks
            # that may still return a raw JSON array.
            elif isinstance(parsed, list):

                extracted = parsed

            else:

                print(
                    "LLM returned an unexpected JSON structure."
                )

                continue

            for fact in extracted:

                if not isinstance(
                    fact,
                    dict
                ):
                    continue

                chunk_id = fact.get(
                    "chunk_id"
                )

                if not isinstance(
                    chunk_id,
                    int
                ):
                    continue

                if (
                    chunk_id < 0
                    or chunk_id >= len(batch)
                ):
                    continue

                source_chunk = batch[
                    chunk_id
                ]

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

                evidence_verified = (
                    verify_evidence(
                        fact,
                        source_chunk.get(
                            "chunk_text",
                            ""
                        )
                    )
                )

                fact[
                    "evidence_verified"
                ] = evidence_verified

                if evidence_verified:
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

            print(
                f"LLM batch extraction failed: "
                f"{error}"
            )

    print(
        f"Batch extraction complete: "
        f"{len(facts)} verified facts."
    )

    return facts