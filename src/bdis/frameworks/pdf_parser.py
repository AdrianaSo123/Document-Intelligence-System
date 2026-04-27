import pdfplumber
import io
import logging
import shutil

logger = logging.getLogger(__name__)

def check_ocr_dependencies():
    """Verifies that tesseract and poppler are available on the system path."""
    tesseract_exists = shutil.which("tesseract") is not None
    poppler_exists = shutil.which("pdftoppm") is not None # part of poppler-utils
    
    if not tesseract_exists:
        logger.warning("[OCR] Tesseract binary not found. OCR extraction will fail.")
    if not poppler_exists:
        logger.warning("[OCR] Poppler (pdftoppm) binary not found. PDF-to-Image conversion will fail.")
    
    return tesseract_exists and poppler_exists

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
        logger.info("[PDF] No native text found. Triggering OCR fallback...")
        
        if not check_ocr_dependencies():
            logger.error("[OCR] Cannot run OCR: System dependencies missing.")
            return "[ERROR: OCR DEPENDENCIES MISSING]"

        from pdf2image import convert_from_bytes
        import pytesseract
        
        images = convert_from_bytes(file_bytes)
        for img in images:
            text += pytesseract.image_to_string(img) + "\n"
            
    return text
