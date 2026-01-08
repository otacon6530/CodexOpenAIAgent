import sys
import json
from core.classes.Logger import Logger
logger = Logger()

def _send(payload):
    try:
        debug_message = json.dumps(payload)
    except Exception:
        debug_message = str(payload)
    logger.info(f"SEND: {debug_message}")
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()