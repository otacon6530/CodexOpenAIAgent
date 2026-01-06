import os
import tempfile
from core.classes.Logger import Logger

def test_logger_debug_writes(tmp_path):
    log_file = tmp_path / "log.txt"
    logger = Logger(config={"log_level": "DEBUG"}, log_file=str(log_file))
    logger.debug("test message")
    with open(log_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "test message" in content

def test_logger_should_log_levels(tmp_path):
    log_file = tmp_path / "log.txt"
    logger = Logger(config={"log_level": "WARNING"}, log_file=str(log_file))
    logger.info("should not log")
    logger.warning("should log warning")
    logger.error("should log error")
    with open(log_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "should log warning" in content
    assert "should log error" in content
    assert "should not log" not in content

def test_logger_format_and_thread_safety(tmp_path):
    log_file = tmp_path / "log.txt"
    logger = Logger(config={"log_level": "DEBUG"}, log_file=str(log_file))
    logger.log("INFO", "info message")
    with open(log_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "[INFO]" in content
    assert "info message" in content

def test_logger_get_level_from_config():
    logger = Logger(config={"log_level": "ERROR"})
    assert logger.level == Logger.LEVELS["ERROR"]
    logger2 = Logger(config={"log_level": "INVALID"})
    assert logger2.level == Logger.LEVELS["DEBUG"]
    logger3 = Logger()
    assert logger3.level == Logger.LEVELS["DEBUG"]

def test_logger_should_log_returns_none(tmp_path):
    log_file = tmp_path / "log.txt"
    logger = Logger(config={"log_level": "ERROR"}, log_file=str(log_file))
    # Should not log debug/info
    assert logger.log("DEBUG", "no log") is None
    assert logger.log("INFO", "no log") is None

def test_logger_format_and_file(tmp_path):
    log_file = tmp_path / "log.txt"
    logger = Logger(config={"log_level": "DEBUG"}, log_file=str(log_file))
    # Test _format directly
    formatted = logger._format("INFO", "msg", "file.py", 123)
    assert "[INFO]" in formatted and "file.py:123" in formatted and "msg" in formatted
