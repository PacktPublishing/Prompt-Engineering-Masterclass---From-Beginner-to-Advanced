import json
from click.testing import CliRunner
from unittest.mock import Mock

from ai_toolbox.commands import review


def make_mock_response(text):
    mock_resp = Mock()
    mock_resp.choices = [Mock()]
    mock_resp.choices[0].message = Mock()
    mock_resp.choices[0].message.content = text
    mock_resp.choices[0].message.tool_calls = None
    return mock_resp


def test_review_cli_outputs_markdown(mocker):
    sample_diff = "x" * 50
    mocker.patch(
        "ai_toolbox.commands.review.cli.get_diff",
        return_value=sample_diff,
    )
    mock_completion = mocker.patch(
        "ai_toolbox.commands.review.helpers.completion"
    )

    # Make LLM return a JSON structured content for parsing
    mock_completion.return_value = make_mock_response(
        json.dumps(
            {"summary": "S", "issues": [], "suggestions": []}
        )
    )

    runner = CliRunner()
    result = runner.invoke(
        review, ["--staged"], obj={}
    )  # default markdown
    assert result.exit_code == 0
    assert "# Review Summary" in result.output


def test_review_cli_outputs_json_to_file(mocker, tmp_path):
    sample_diff = "y" * 10
    mocker.patch(
        "ai_toolbox.commands.review.cli.get_diff",
        return_value=sample_diff,
    )
    mock_completion = mocker.patch(
        "ai_toolbox.commands.review.helpers.completion"
    )
    mock_completion.return_value = make_mock_response(
        json.dumps(
            {"summary": "J", "issues": [], "suggestions": []}
        )
    )

    out_file = tmp_path / "out.json"

    runner = CliRunner()
    result = runner.invoke(
        review,
        [
            "--staged",
            "--output",
            "json",
            "--output-path",
            str(out_file),
        ],
        obj={},
    )
    assert result.exit_code == 0
    # ensure file was written
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    parsed = json.loads(content)
    assert parsed["summary"] == "J"
