from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "running"


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "healthy"
    }


def test_ingest_rejects_non_pdf():
    response = client.post(
        "/api/ingest",
        files={
            "files": (
                "document.txt",
                b"This is not a PDF.",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400

    assert "Only PDF files are supported" in (
        response.json()["detail"]
    )


def test_ingest_requires_file():
    response = client.post("/api/ingest")

    assert response.status_code == 422


def test_ingest_accepts_pdf_without_calling_gemini(
    monkeypatch
):
    """
    Test the API upload flow without making a Gemini request.
    """

    fake_result = {
        "documents": [
            {
                "source_document": "sample.pdf",
                "fact_count": 1
            }
        ],
        "facts": [
            {
                "entity_key": "example company",
                "metric_key": "revenue",
                "value": 100,
                "unit_key": "cr",
                "period_key": "fy2024",
                "scope_key": "",
                "evidence": "Revenue was 100 Cr",
                "page_number": 1,
                "source_document": "sample.pdf"
            }
        ],
        "relationships": [],
        "summary": {
            "document_count": 1,
            "fact_count": 1,
            "relationship_count": 0
        }
    }

    def fake_process_documents(pdf_paths):
        assert len(pdf_paths) == 1
        assert pdf_paths[0].endswith(".pdf")

        return fake_result

    monkeypatch.setattr(
        "app.main.process_documents",
        fake_process_documents
    )

    response = client.post(
        "/api/ingest",
        files={
            "files": (
                "sample.pdf",
                b"%PDF-1.4 fake pdf content",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["summary"]["document_count"] == 1
    assert data["summary"]["fact_count"] == 1

    assert data["facts"][0]["metric_key"] == "revenue"
    assert data["facts"][0]["value"] == 100


def test_ingest_accepts_multiple_pdfs_without_calling_gemini(
    monkeypatch
):
    """
    Test uploading multiple PDFs through the API
    without making Gemini requests.
    """

    fake_result = {
        "documents": [
            {
                "source_document": "document_a.pdf",
                "fact_count": 1
            },
            {
                "source_document": "document_b.pdf",
                "fact_count": 1
            }
        ],
        "facts": [
            {
                "entity_key": "example company",
                "metric_key": "revenue",
                "value": 100,
                "unit_key": "cr",
                "period_key": "fy2024",
                "scope_key": "",
                "evidence": "Revenue was 100 Cr",
                "page_number": 1,
                "source_document": "document_a.pdf"
            },
            {
                "entity_key": "example company",
                "metric_key": "revenue",
                "value": 100,
                "unit_key": "cr",
                "period_key": "fy2024",
                "scope_key": "",
                "evidence": "Revenue stood at 100 Cr",
                "page_number": 2,
                "source_document": "document_b.pdf"
            }
        ],
        "relationships": [
            {
                "relationship": "corroboration"
            }
        ],
        "summary": {
            "document_count": 2,
            "fact_count": 2,
            "relationship_count": 1
        }
    }

    def fake_process_documents(pdf_paths):
        assert len(pdf_paths) == 2

        assert pdf_paths[0].endswith(".pdf")
        assert pdf_paths[1].endswith(".pdf")

        return fake_result

    monkeypatch.setattr(
        "app.main.process_documents",
        fake_process_documents
    )

    response = client.post(
        "/api/ingest",
        files=[
            (
                "files",
                (
                    "document_a.pdf",
                    b"%PDF-1.4 fake pdf A",
                    "application/pdf"
                )
            ),
            (
                "files",
                (
                    "document_b.pdf",
                    b"%PDF-1.4 fake pdf B",
                    "application/pdf"
                )
            )
        ]
    )

    assert response.status_code == 200

    data = response.json()

    assert data["summary"]["document_count"] == 2
    assert data["summary"]["fact_count"] == 2
    assert data["summary"]["relationship_count"] == 1

    assert len(data["documents"]) == 2
    assert len(data["facts"]) == 2
    assert len(data["relationships"]) == 1

    assert data["relationships"][0]["relationship"] == (
        "corroboration"
    )