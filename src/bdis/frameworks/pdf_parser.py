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
                
    if not text.strip():
        # High Severity Resolution: Silent failure OCR trigger
        from pdf2image import convert_from_bytes
        import pytesseract
        
        images = convert_from_bytes(file_bytes)
        for img in images:
            text += pytesseract.image_to_string(img) + "\n"
            
    return text
