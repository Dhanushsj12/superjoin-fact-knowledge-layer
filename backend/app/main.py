from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.pipeline import process_documents


app = FastAPI(
    title="Superjoin Fact Knowledge Layer",
    description="Extract and compare facts across PDF documents.",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "Superjoin Fact Knowledge Layer API",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/api/ingest")
async def ingest_documents(
    files: List[UploadFile] = File(...)
):
    """
    Upload one or more PDF documents and process them
    through the fact knowledge layer.
    """

    if not files:
        raise HTTPException(
            status_code=400,
            detail="At least one PDF file is required."
        )

    for uploaded_file in files:
        filename = uploaded_file.filename or ""

        if not filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"Only PDF files are supported: {filename}"
            )

    try:
        with TemporaryDirectory() as temp_dir:

            pdf_paths = []

            for uploaded_file in files:

                filename = Path(
                    uploaded_file.filename
                ).name

                file_path = Path(temp_dir) / filename

                content = await uploaded_file.read()

                if not content:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Uploaded file is empty: {filename}"
                    )

                file_path.write_bytes(content)

                pdf_paths.append(str(file_path))

            result = process_documents(pdf_paths)

            return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(exc)}"
        )