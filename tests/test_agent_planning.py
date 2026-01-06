import pytest
from core.functions import agent_planning

def test_summarize_plan():
    plan = {"steps": ["step1", "step2"]}
    assert "step1" in agent_planning.summarize_plan(plan)
    assert "step2" in agent_planning.summarize_plan(plan)
    assert agent_planning.summarize_plan("") == "No plan generated."

def test_summarize_tool_use():
    calls = [{"name": "foo", "args": {"bar": 1}, "result": "baz"}]
    summary = agent_planning.summarize_tool_use(calls)
    assert "Tool: foo" in summary
    assert "Args" in summary
    assert "Result" in summary
