import os
import threading
from datetime import datetime
import inspect

class Logger:
    LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}

    def __init__(self, config=None, log_file="log.txt"):
        self.log_file = log_file
        self.lock = threading.Lock()
        self.level = self._get_level_from_config(config)

    def _get_level_from_config(self, config):
        if config is not None:
            level = config.get("log_level", "DEBUG").upper()
            return self.LEVELS.get(level, 10)
        return 10  # Default to DEBUG

    def _should_log(self, level):
        return self.LEVELS[level] >= self.level

    def _format(self, level, msg, file, line):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"[{now}] [{level}] [{file}:{line}] {msg}\n"

    def log(self, level, msg):
        if not self._should_log(level):
            return
        frame = inspect.currentframe().f_back.f_back
        file = os.path.basename(frame.f_code.co_filename)
        line = frame.f_lineno
        entry = self._format(level, msg, file, line)
        with self.lock:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(entry)

    def debug(self, msg):
        self.log("DEBUG", msg)

    def info(self, msg):
        self.log("INFO", msg)

    def warning(self, msg):
        self.log("WARNING", msg)

    def error(self, msg):
        self.log("ERROR", msg)
