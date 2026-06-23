import logging
import json
import sys
from ai_project.utils.logging import JSONFormatter

def test_json_formatter_standard():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_path.py",
        lineno=10,
        msg="Test message with %s",
        args=("arg1",),
        exc_info=None
    )
    result = formatter.format(record)
    data = json.loads(result)
    
    assert "timestamp" in data
    assert data["level"] == "INFO"
    assert data["logger"] == "test_logger"
    assert data["message"] == "Test message with arg1"
    assert "exception" not in data

def test_json_formatter_with_exception():
    formatter = JSONFormatter()
    try:
        raise ValueError("Something went wrong")
    except ValueError:
        exc_info = sys.exc_info()
        
    record = logging.LogRecord(
        name="error_logger",
        level=logging.ERROR,
        pathname="test_path.py",
        lineno=20,
        msg="An error occurred",
        args=(),
        exc_info=exc_info
    )
    result = formatter.format(record)
    data = json.loads(result)
    
    assert "timestamp" in data
    assert data["level"] == "ERROR"
    assert data["logger"] == "error_logger"
    assert data["message"] == "An error occurred"
    assert "exception" in data
    assert "ValueError: Something went wrong" in data["exception"]
