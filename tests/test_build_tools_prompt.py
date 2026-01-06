from core.functions.build_tools_prompt import build_tools_prompt

def test_build_tools_prompt():
    tools = {"foo": {"description": "bar"}}
    prompt = build_tools_prompt(tools)
    assert "foo" in prompt
    assert "bar" in prompt

def test_build_tools_prompt_create_file():
    tools = {"create_file": {"description": "desc"}}
    result = build_tools_prompt(tools)
    assert "Example:" in result

def test_build_tools_prompt_empty():
    result = build_tools_prompt({})
    assert "Available tools:" in result
    assert "To call a tool" in result
