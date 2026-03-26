import logging
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
import nbformat

logger = logging.getLogger(__name__)

from backend.services.pdf_parser import extract_text_from_pdf
from backend.services.llm_service import generate_notebook_content
from backend.services.notebook_builder import build_notebook

router = APIRouter()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/api/generate")
async def generate_notebook(
    file: UploadFile = File(...),
    api_key: str = Form(...),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    if not api_key or not api_key.strip():
        raise HTTPException(status_code=400, detail="API key is required.")

    # 1. Read PDF bytes with size limit
    pdf_bytes = await file.read()

    if len(pdf_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds maximum of 50MB.",
        )

    # 2. Extract text
    try:
        extracted = extract_text_from_pdf(pdf_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to parse PDF. Please upload a valid PDF file.")

    if not extracted["full_text"].strip():
        raise HTTPException(status_code=400, detail="Could not extract text from PDF. The file may be image-based.")

    # 3. Generate notebook content via LLM
    try:
        cells = generate_notebook_content(extracted["full_text"], api_key)
    except Exception as e:
        detail = str(e)
        if "auth" in detail.lower() or "api key" in detail.lower():
            raise HTTPException(status_code=401, detail="Invalid API key.")
        logger.error("LLM generation failed: %s", detail)
        raise HTTPException(status_code=502, detail="LLM generation failed. Please try again.")

    # 4. Build notebook
    title = extracted["full_text"][:100].split("\n")[0].strip() or "Research Paper"
    nb = build_notebook(cells, title)

    return {"notebook": nbformat.from_dict(nb)}
