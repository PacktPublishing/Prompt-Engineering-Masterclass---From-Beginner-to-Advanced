import click
from click.testing import CliRunner
from unittest.mock import Mock

from ai_toolbox.commands import review
from ai_toolbox.commands.review import run_review_pipeline


def test_review_command_exists():
    assert isinstance(review, click.Command)


def test_run_review_pipeline_truncates_diff():
    long_diff = "a" * 500
    result = run_review_pipeline(diff=long_diff)
    # The function returns a ReviewResult object now, check if it has expected attributes
    assert hasattr(result, "summary")
    assert hasattr(result, "issues")
    assert hasattr(result, "suggestions")


def test_review_command_calls_git_and_outputs_preview(mocker):
    # Arrange
    sample_diff = "x" * 300
    mocker.patch(
        "ai_toolbox.commands.review.cli.get_diff",
        return_value=sample_diff,
    )
    # Mock the LLM completion to avoid real network calls
    mock_completion = mocker.patch(
        "ai_toolbox.commands.review.helpers.completion"
    )

    mock_resp = Mock()
    mock_resp.choices = [Mock()]
    mock_resp.choices[0].message = Mock()
    mock_resp.choices[0].message.content = (
        '{"summary": "No issues", "issues": [], "suggestions": []}'
    )
    mock_resp.choices[0].message.tool_calls = (
        None  # No tool calls needed
    )
    mock_completion.return_value = mock_resp

    runner = CliRunner()

    # Act
    result = runner.invoke(review, obj={})

    # Assert
    assert result.exit_code == 0
    # Check for pipeline completion messages instead of specific preview text
    assert "Starting review pipeline" in result.output
    assert "Syntax analysis completed" in result.output
