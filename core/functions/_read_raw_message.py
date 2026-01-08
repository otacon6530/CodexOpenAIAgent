

import sys
import json
from core.functions._send import _send
from core.classes.Logger import Logger
logger = Logger()


def _read_raw_message():
    logger.info("_read_raw_message: waiting for input on stdin...")
    while True:
        line = sys.stdin.readline()
        logger.info(f"_read_raw_message: read line: {repr(line)}")
        if not line:
            logger.info("_read_raw_message: EOF on stdin, returning None")
            return None
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            logger.info(f"RECEIVE: {json.dumps(msg)}")
            return msg
        except json.JSONDecodeError:
            logger.info(f"_read_raw_message: Invalid JSON input: {line}")
            _send({"type": "error", "content": "Invalid JSON input."})