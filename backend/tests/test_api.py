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