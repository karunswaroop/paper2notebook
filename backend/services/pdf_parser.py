import fitz  # PyMuPDF

MAX_PAGES = 200


def extract_text_from_pdf(pdf_bytes: bytes) -> dict:
    """Extract text from a PDF file, returning structured page-by-page content."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    page_count = doc.page_count
    if page_count > MAX_PAGES:
        doc.close()
        raise ValueError(
            f"PDF has {page_count} pages, which exceeds maximum of {MAX_PAGES}."
        )

    pages = []
    full_text_parts = []

    for i, page in enumerate(doc):
        text = page.get_text()
        pages.append({
            "page_number": i + 1,
            "text": text,
        })
        full_text_parts.append(text)

    doc.close()

    return {
        "pages": pages,
        "full_text": "\n\n".join(full_text_parts),
        "total_pages": len(pages),
    }
