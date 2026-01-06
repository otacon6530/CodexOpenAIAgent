from core.functions.build_os_message import build_os_message

def test_build_os_message():
    msg = build_os_message()
    assert isinstance(msg, str)
    assert "environment" in msg
