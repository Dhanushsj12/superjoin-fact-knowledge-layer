from app.extraction.candidate_detector import (
    candidate_score,
    is_candidate_chunk,
    filter_candidate_chunks,
)


def test_numeric_chunk_is_candidate():
    chunk = {
        "page_number": 1,
        "chunk_text": "Revenue increased to ₹2,076 crore in FY2024.",
    }

    assert is_candidate_chunk(chunk)


def test_percent_chunk_is_candidate():
    chunk = {
        "page_number": 2,
        "chunk_text": "Growth increased by 18.5% during FY2024.",
    }

    assert is_candidate_chunk(chunk)


def test_plain_text_is_not_candidate():
    chunk = {
        "page_number": 3,
        "chunk_text": "This section describes the company's history.",
    }

    assert not is_candidate_chunk(chunk)


def test_filter_preserves_candidate_chunks():
    chunks = [
        {
            "page_number": 1,
            "chunk_text": "Revenue was ₹2,076 crore in FY2024.",
        },
        {
            "page_number": 2,
            "chunk_text": "This section contains general background information.",
        },
        {
            "page_number": 3,
            "chunk_text": "Growth was 15% compared with 2023.",
        },
    ]

    result = filter_candidate_chunks(chunks)

    assert len(result) == 2
    assert result[0]["page_number"] == 1
    assert result[1]["page_number"] == 3


def test_score_is_non_negative():
    assert candidate_score("") == 0
    assert candidate_score("plain text") >= 0