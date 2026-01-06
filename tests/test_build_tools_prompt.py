from core.functions.build_tools_prompt import build_tools_prompt

def test_build_tools_prompt():
    tools = {"foo": {"description": "bar"}}
    prompt = build_tools_prompt(tools)
    assert "foo" in prompt
    assert "bar" in prompt
