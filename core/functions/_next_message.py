import json
from core.classes.Logger import Logger
from core.functions._pop_buffered_message import _pop_buffered_message
from core.functions._read_raw_message import _read_raw_message

logger = Logger()

def _next_message():
    logger.info("_next_message: checking for buffered message...")
    buffered = _pop_buffered_message()
    if buffered is not None:
        logger.info(f"RECEIVE (buffered): {json.dumps(buffered)}")
        return buffered
    logger.info("_next_message: no buffered message, calling _read_raw_message()")
    return _read_raw_message()