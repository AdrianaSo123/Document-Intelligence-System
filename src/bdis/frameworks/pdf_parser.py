import pdfplumber
import io

def parse_pdf(file_bytes: bytes) -> str:
    """
    Extracts native text from a PDF. 
    (Sprint 3 implementation using pdfplumber)
    """
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text
