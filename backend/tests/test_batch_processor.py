import pytest

from app.extraction.batch_processor import create_batches


def test_create_batches_groups_chunks():
    chunks = [
        {"page_number": 1, "chunk_text": "A", "source_document": "a.pdf"},
        {"page_number": 2, "chunk_text": "B", "source_document": "a.pdf"},
        {"page_number": 3, "chunk_text": "C", "source_document": "a.pdf"},
        {"page_number": 4, "chunk_text": "D", "source_document": "a.pdf"},
        {"page_number": 5, "chunk_text": "E", "source_document": "a.pdf"},
    ]

    batches = create_batches(chunks, batch_size=2)

    assert len(batches) == 3
    assert len(batches[0]) == 2
    assert len(batches[1]) == 2
    assert len(batches[2]) == 1


def test_create_batches_preserves_all_chunks():
    chunks = [
        {"page_number": i, "chunk_text": f"chunk-{i}"}
        for i in range(1, 11)
    ]

    batches = create_batches(chunks, batch_size=3)

    flattened = [
        chunk
        for batch in batches
        for chunk in batch
    ]

    assert flattened == chunks
    assert len(flattened) == len(chunks)


def test_create_batches_preserves_metadata():
    chunks = [
        {
            "page_number": 10,
            "chunk_text": "Revenue was reported.",
            "source_document": "report-a.pdf",
        },
        {
            "page_number": 25,
            "chunk_text": "Growth increased.",
            "source_document": "report-b.pdf",
        },
    ]

    batches = create_batches(
        chunks,
        batch_size=10
    )

    assert batches[0][0]["page_number"] == 10
    assert batches[0][0]["source_document"] == "report-a.pdf"

    assert batches[0][1]["page_number"] == 25
    assert batches[0][1]["source_document"] == "report-b.pdf"


def test_empty_chunks_return_empty_batches():
    assert create_batches([], batch_size=10) == []


def test_invalid_batch_size_raises_error():
    chunks = [
        {"page_number": 1, "chunk_text": "test"}
    ]

    with pytest.raises(ValueError):
        create_batches(chunks, batch_size=0)

    with pytest.raises(ValueError):
        create_batches(chunks, batch_size=-1)


def test_batch_size_larger_than_input():
    chunks = [
        {"page_number": 1, "chunk_text": "A"},
        {"page_number": 2, "chunk_text": "B"},
    ]

    batches = create_batches(
        chunks,
        batch_size=10
    )

    assert len(batches) == 1
    assert len(batches[0]) == 2