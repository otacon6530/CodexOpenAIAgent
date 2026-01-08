from core.functions._send import _send
from core.functions._wait_for_message import _wait_for_message


def _request_editor_query(query, payload=None, timeout=10):
    import uuid

    request_id = str(uuid.uuid4())
    message = {"type": "editor_query", "query": query, "id": request_id}
    if payload is not None:
        message["payload"] = payload

    _send(message)

    response = _wait_for_message("editor_query_response", request_id, timeout=timeout)
    if response is None:
        raise RuntimeError("No response from VS Code extension.")
    if response.get("error"):
        raise RuntimeError(response.get("error"))
    return response.get("result")