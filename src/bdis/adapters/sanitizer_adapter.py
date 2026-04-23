import re
from bdis.ports.sanitizer import ISanitizer

class RegexPIISanitizer(ISanitizer):
    """
    Regex-based implementation of the Sanitizer port.
    """
    def __init__(self):
        self.patterns = {
            "credit_card": re.compile(r'\b(?:\d[ -]*?){13,16}\b'),
            "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "phone": re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
        }

    def sanitize(self, text: str) -> str:
        if not text:
            return text
        
        sanitized = text
        for pii_type, pattern in self.patterns.items():
            sanitized = pattern.sub(f"[REDACTED_{pii_type.upper()}]", sanitized)
            
        return sanitized
