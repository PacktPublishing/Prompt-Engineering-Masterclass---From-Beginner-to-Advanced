from unittest.mock import Mock
from ai_toolbox.commands.review import (
    self_consistency_review,
    run_review_pipeline,
    ReviewResult,
)


def make_mock_response(text):
    mock_resp = Mock()
    mock_resp.choices = [Mock()]
    mock_resp.choices[0].message = Mock()
    mock_resp.choices[0].message.content = text
    mock_resp.choices[0].message.tool_calls = (
        None  # No tool calls
    )
    return mock_resp


def test_self_consistency_review_and_pipeline_integration(
    mocker,
):
    draft = ReviewResult(
        summary="Initial synthesis", issues=[], suggestions=[]
    )

    mock_completion = mocker.patch(
        "ai_toolbox.commands.review.helpers.completion"
    )

    # self_consistency_review should be called once with the synthesis
    mock_completion.return_value = make_mock_response(
        '{"summary": "Polished final review", "issues": [], "suggestions": []}'
    )

    polished = self_consistency_review(draft, model="fake-model")
    assert polished.summary == "Polished final review"

    # Now ensure pipeline returns final_review when model is provided
    mocker.patch(
        "ai_toolbox.commands.review.cli.get_diff",
        return_value="x" * 300,
    )

    # Sequence of completions for analyze_syntax, analyze_logic, personas(3), synthesis, self-consistency
    mock_completion.side_effect = [
        make_mock_response(
            '{"summary": "no issues", "issues": [], "suggestions": []}'
        ),
        make_mock_response(
            '{"summary": "logic", "issues": [], "suggestions": ["fix"]}'
        ),
        make_mock_response(
            '{"summary": "perf", "issues": [], "suggestions": []}'
        ),
        make_mock_response(
            '{"summary": "maint", "issues": [], "suggestions": []}'
        ),
        make_mock_response(
            '{"summary": "sec", "issues": [], "suggestions": []}'
        ),
        make_mock_response(
            '{"summary": "synth", "issues": [], "suggestions": []}'
        ),
        make_mock_response(
            '{"summary": "Polished final review", "issues": [], "suggestions": []}'
        ),
    ]

    result = run_review_pipeline(
        diff="x" * 300, model="fake-model"
    )
    # The result is a ReviewResult object, check its summary
    assert result.summary == "Polished final review"
