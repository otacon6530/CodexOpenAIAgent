
try:
    _PENDING_MESSAGES
except NameError:
    _PENDING_MESSAGES = []

def _pop_buffered_message(expected_type=None, expected_id=None):
    if not _PENDING_MESSAGES:
        return None
    if expected_type is None:
        return _PENDING_MESSAGES.pop(0)
    for index, message in enumerate(_PENDING_MESSAGES):
        if message.get("type") != expected_type:
            continue
        if expected_id is not None and message.get("id") != expected_id:
            continue
        return _PENDING_MESSAGES.pop(index)
    return None