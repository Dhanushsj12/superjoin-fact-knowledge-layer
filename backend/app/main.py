from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.pipeline import process_documents


app = FastAPI(
    title="Superjoin Fact Knowledge Layer",
    description="Extract and compare facts across PDF documents.",
    version="1.0.0",
)


# Allow the local frontend to communicate with the API.
# This is appropriate for the local prototype/demo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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