import logging
import json
import contextvars
from datetime import datetime

# Async-local ContextVar to trace request execution lifecycles
request_id_context = contextvars.ContextVar("request_id", default=None)

class JSONFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs log records as single-line JSON strings.
    Contains timestamp, log level, logger name, message, request_id, and exception traceback if present.
    """
    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "request_id": request_id_context.get(),
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)
