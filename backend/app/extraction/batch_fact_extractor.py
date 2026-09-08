import json
from typing import List, Dict

from .llm_client import generate_text
from .fallback_extractor import extract_facts_fallback
from app.reasoning.evidence_verifier import verify_evidence
from app.extraction.batch_processor import create_batches


def _prepare_chunks(
    chunks: List[Dict]
) -> List[Dict]:
    """
    Ensure every chunk has a stable global chunk_id.

    Existing chunk_id values are preserved when valid.
    Otherwise, IDs are assigned using the original
    position in the input list.
    """

    prepared = []

    for index, chunk in enumerate(chunks):

        item = dict(chunk)

        chunk_id = item.get("chunk_id")

        if not isinstance(chunk_id, int):
            chunk_id = index

        item["chunk_id"] = chunk_id

        prepared.append(item)

    return prepared


def _verify_and_enrich_fact(
    fact: Dict,
    chunks_by_id: Dict[int, Dict]
) -> Dict | None:
    """
    Validate an extracted fact and attach trusted
    source metadata from the original chunk.
    """

    if not isinstance(fact, dict):
        return None

    chunk_id = fact.get("chunk_id")

    if not isinstance(chunk_id, int):
        return None

    source_chunk = chunks_by_id.get(chunk_id)

    if source_chunk is None:
        return None

    evidence = fact.get("evidence")

    if not isinstance(evidence, str):
        return None

    evidence_verified = verify_evidence(
        fact,
        source_chunk.get("chunk_text", "")
    )

    if not evidence_verified:
        return None

    enriched_fact = dict(fact)

    # Source metadata comes from our pipeline,
    # not from the LLM.
    enriched_fact["page_number"] = (
        source_chunk.get("page_number")
    )

    enriched_fact["source_document"] = (
        source_chunk.get("source_document")
    )

    enriched_fact["evidence_verified"] = True

    return enriched_fact


def _run_fallback(
    chunks: List[Dict]
) -> List[Dict]:
    """
    Run deterministic extraction when the LLM
    is unavailable or has reached its quota.
    """

    if not chunks:
        return []

    print(
        f"Running deterministic fallback on "
        f"{len(chunks)} chunks..."
    )

    fallback_facts = extract_facts_fallback(
        chunks
    )

    chunks_by_id = {
        chunk["chunk_id"]: chunk
        for chunk in chunks
    }

    verified_facts = []

    for fact in fallback_facts:

        verified = _verify_and_enrich_fact(
            fact,
            chunks_by_id
        )

        if verified:
            verified_facts.append(verified)

    print(
        f"Fallback extraction complete: "
        f"{len(verified_facts)} verified facts."
    )

    return verified_facts


def extract_facts_from_batches(
    chunks: List[Dict],
    batch_size: int = 3
) -> List[Dict]:
    """
    Extract meaningful structured facts from document
    chunks using an LLM when available, with a
    deterministic fallback when the LLM fails.

    The extractor is generic and document-agnostic.
    """

    if not chunks:
        return []

    prepared_chunks = _prepare_chunks(
        chunks
    )

    batches = create_batches(
        prepared_chunks,
        batch_size=batch_size
    )

    facts = []

    total_batches = len(batches)

    llm_available = True

    for batch_index, batch in enumerate(
        batches,
        start=1
    ):

        print(
            f"Processing batch {batch_index}/"
            f"{total_batches} "
            f"({len(batch)} chunks)..."
        )

        # ---------------------------------------------------------
        # If the LLM has already failed or hit its quota,
        # use deterministic fallback for the remaining batches.
        # ---------------------------------------------------------

        if not llm_available:

            fallback_facts = _run_fallback(
                batch
            )

            facts.extend(
                fallback_facts
            )

            continue

        # ---------------------------------------------------------
        # Build the LLM prompt using stable global chunk IDs.
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

If no meaningful facts are present, return exactly:

{
  "facts": []
}

Do not return markdown.
Do not return explanations.
Do not return additional keys.
"""

        for item in batch:

            prompt += f"""

CHUNK_ID: {item["chunk_id"]}

PAGE_NUMBER: {item["page_number"]}

SOURCE_DOCUMENT: {item["source_document"]}

DOCUMENT TEXT:
{item["chunk_text"]}

"""

        # ---------------------------------------------------------
        # LLM extraction
        # ---------------------------------------------------------

        try:

            output = generate_text(
                prompt
            )

            cleaned_output = output.strip()

            if cleaned_output.startswith("```"):

                if cleaned_output.startswith(
                    "```json"
                ):
                    cleaned_output = (
                        cleaned_output[
                            len("```json"):
                        ]
                    )

                else:
                    cleaned_output = (
                        cleaned_output[
                            len("```"):
                        ]
                    )

                if cleaned_output.endswith(
                    "```"
                ):
                    cleaned_output = (
                        cleaned_output[
                            :-len("```"):
                        ]
                    )

                cleaned_output = (
                    cleaned_output.strip()
                )

            parsed = json.loads(
                cleaned_output
            )

            if (
                isinstance(parsed, dict)
                and isinstance(
                    parsed.get("facts"),
                    list
                )
            ):

                extracted = parsed["facts"]

            elif isinstance(parsed, list):

                extracted = parsed

            else:

                print(
                    "LLM returned an unexpected "
                    "JSON structure."
                )

                # Treat invalid LLM output as a
                # failure for this batch.
                fallback_facts = _run_fallback(
                    batch
                )

                facts.extend(
                    fallback_facts
                )

                continue

            chunks_by_id = {
                chunk["chunk_id"]: chunk
                for chunk in batch
            }

            for fact in extracted:

                verified = (
                    _verify_and_enrich_fact(
                        fact,
                        chunks_by_id
                    )
                )

                if verified:
                    facts.append(
                        verified
                    )

        except json.JSONDecodeError:

            print(
                "Could not parse LLM response "
                "as JSON."
            )

            fallback_facts = _run_fallback(
                batch
            )

            facts.extend(
                fallback_facts
            )

        except Exception as error:

            error_text = str(error)

            print(
                f"LLM batch extraction failed: "
                f"{error}"
            )

            # -----------------------------------------------------
            # Rate limit / quota exhaustion.
            # Stop using the LLM for the remainder
            # of this extraction run.
            # -----------------------------------------------------

            if (
                "429" in error_text
                or "RESOURCE_EXHAUSTED"
                in error_text
                or "rate_limit"
                in error_text.lower()
                or "quota" in error_text.lower()
            ):

                print(
                    "LLM quota/rate limit reached. "
                    "Switching to deterministic "
                    "fallback for remaining batches."
                )

                llm_available = False

            # -----------------------------------------------------
            # Fallback immediately for the failed batch.
            # -----------------------------------------------------

            fallback_facts = _run_fallback(
                batch
            )

            facts.extend(
                fallback_facts
            )

    print(
        f"Batch extraction complete: "
        f"{len(facts)} verified facts."
    )

    return facts