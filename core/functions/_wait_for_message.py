import time
import json

# Import or define logger
try:
    from core.classes.Logger import Logger
    logger = Logger()
except ImportError:
    import logging
    logger = logging.getLogger("core")

from core.functions._pop_buffered_message import _pop_buffered_message
from core.functions._read_raw_message import _read_raw_message

# Ensure _PENDING_MESSAGES exists as a global list
try:
    _PENDING_MESSAGES
except NameError:
    _PENDING_MESSAGES = []

def _wait_for_message(expected_type, expected_id=None, timeout=None):
    if expected_type is None:
        raise ValueError("expected_type is required")

    deadline = time.time() + timeout if timeout else None

    buffered = _pop_buffered_message(expected_type, expected_id)
    if buffered is not None:
        logger.info(f"RECEIVE (wait/buffered): {json.dumps(buffered)}")
        return buffered

    while True:
        if deadline is not None and time.time() > deadline:
            return None
        message = _read_raw_message()
        if message is None:
            return None
        if message.get("type") == expected_type and (expected_id is None or message.get("id") == expected_id):
            return message
        _PENDING_MESSAGES.append(message)