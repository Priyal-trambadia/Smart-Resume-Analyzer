import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_file) -> str:
    """
    Extract all text from an uploaded PDF file.
    pdf_file: a file-like object (from st.file_uploader)
    Returns: plain text string
    """
    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        pages_text = []
        for page in doc:
            pages_text.append(page.get_text())
        doc.close()
        full_text = "\n".join(pages_text).strip()
        return full_text if full_text else "Could not extract text. Try a text-based PDF."
    except Exception as e:
        return f"Error reading PDF: {str(e)}"
