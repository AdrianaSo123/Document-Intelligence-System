import logging
import json
from datetime import datetime

class JsonFormatter(logging.Formatter):
    """
    Standardizes log output to JSON for production observability (ELK/Datadog).
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName
        }
        
        # Include extra attributes if provided
        if hasattr(record, "trace_id"):
            log_record["trace_id"] = record.trace_id
        if hasattr(record, "document_id"):
            log_record["document_id"] = record.document_id
            
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def setup_json_logging(level=logging.INFO):
    """Configures the root logger to use JSON formatting."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    
    root = logging.getLogger()
    root.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for h in root.handlers[:]:
        root.removeHandler(h)
        
    root.addHandler(handler)
