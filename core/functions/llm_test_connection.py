from core.classes.Logger import Logger
from core.functions._send import _send

def test_connection(llm):
    try:
        # Minimal prompt to test connection
        test_messages = [{"role": "system", "content": "ping"}]
        for _ in llm.client.stream_chat(test_messages):
            break  # Only need to check connection, not full response
    except Exception as e:
        Logger().error(f"LLM connection failed: {e}")
        _send({"type": "error", "content": f"LLM connection failed: {e}"})