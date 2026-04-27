from bdis.domain.normalization import DocumentNormalizer
from bdis.adapters.sanitizer_adapter import RegexPIISanitizer

def test_normalizer_float_casting():
    normalizer = DocumentNormalizer()
    raw = {"amount": "$1,200.50"}
    normalized = normalizer.normalize(raw)
    assert normalized["amount"] == 1200.5

def test_normalizer_status_mapping():
    normalizer = DocumentNormalizer()
    assert normalizer.normalize({"status": "SETTLED"})["status"] == "paid"
    assert normalizer.normalize({"status": "OVERDUE"})["status"] == "unpaid"
    assert normalizer.normalize({"status": "Unknown"})["status"] == "unknown"

def test_normalizer_date_normalization():
    from datetime import date
    normalizer = DocumentNormalizer()
    # ISO remains same
    assert normalizer.normalize({"due_date": "2024-01-01"})["due_date"] == date(2024, 1, 1)
    # Slash format
    assert normalizer.normalize({"due_date": "12/31/2023"})["due_date"] == date(2023, 12, 31)
    # Month name format
    assert normalizer.normalize({"due_date": "October 23, 2026"})["due_date"] == date(2026, 10, 23)
    # Short month name format
    assert normalizer.normalize({"due_date": "23 Oct 2026"})["due_date"] == date(2026, 10, 23)

def test_sanitizer_redaction():
    sanitizer = RegexPIISanitizer()
    text = "Contact me at 555-123-4567 or email test@example.com. My card is 1234-5678-9012-3456."
    sanitized = sanitizer.sanitize(text)
    
    assert "[REDACTED_PHONE]" in sanitized
    assert "[REDACTED_EMAIL]" in sanitized
    assert "[REDACTED_CREDIT_CARD]" in sanitized
    assert "555-123-4567" not in sanitized
    assert "test@example.com" not in sanitized
    assert "1234-5678-9012-3456" not in sanitized
