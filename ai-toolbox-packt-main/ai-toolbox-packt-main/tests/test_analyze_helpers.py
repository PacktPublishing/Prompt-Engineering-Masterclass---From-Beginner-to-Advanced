import json

from ai_toolbox.commands.review import (
    analyze_syntax,
    analyze_logic,
)


class DummyMessage:
    def __init__(self, content, tool_calls=[]):
        self.content = content
        self.tool_calls = tool_calls


class DummyChoice:
    def __init__(self, message):
        self.message = message


class DummyResponse:
    def __init__(self, text):
        self.choices = [DummyChoice(DummyMessage(text))]


def test_analyze_syntax_calls_llm_and_returns_content(mocker):
    sample_diff = "+ def foo():\n+    return 1"
    mock_resp = DummyResponse(
        json.dumps(
            {
                "summary": "syntax analysis summary",
                "issues": [],
                "suggestions": ["none"],
            }
        )
    )

    m = mocker.patch(
        "ai_toolbox.commands.review.helpers.completion",
        return_value=mock_resp,
    )

    result = analyze_syntax(sample_diff, model="fake-model")

    assert result.summary == "syntax analysis summary"
    assert result.suggestions == ["none"]
    assert isinstance(result.issues, list)
    m.assert_called_once()


def test_analyze_logic_calls_llm_and_returns_content(mocker):
    sample_diff = "+ def bar():\n+    return x"
    mock_resp = DummyResponse(
        json.dumps(
            {
                "summary": "logic analysis summary",
                "issues": [],
                "suggestions": ["logic suggestions"],
            }
        )
    )

    m = mocker.patch(
        "ai_toolbox.commands.review.helpers.completion",
        return_value=mock_resp,
    )

    result = analyze_logic(sample_diff, model="fake-model")

    assert result.summary == "logic analysis summary"
    assert result.suggestions == ["logic suggestions"]
    assert isinstance(result.issues, list)
    m.assert_called_once()


def test_analyze_helpers_skip_when_no_model():
    sample_diff = "+ def ok():\n+    pass"
    syntax_result = analyze_syntax(sample_diff)
    assert syntax_result.summary == "No model provided - skipping review"
    assert syntax_result.issues == []
    assert syntax_result.suggestions == []
    
    logic_result = analyze_logic(sample_diff)
    assert logic_result.summary == "No model provided - skipping review"
    assert logic_result.issues == []
    assert logic_result.suggestions == []
