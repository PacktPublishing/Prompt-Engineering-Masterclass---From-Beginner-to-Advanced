import json
from ai_toolbox.commands.review import ReviewResult, ReviewIssue


def test_reviewresult_to_json_and_markdown(tmp_path):
    issues = [
        ReviewIssue(
            id="1",
            severity="major",
            category="logic",
            description="Bug found",
            file="a.py",
            line=10,
            snippet="x",
        ),
    ]
    result = ReviewResult(
        summary="Summary here",
        issues=issues,
        suggestions=["Do X", "Do Y"],
    )

    # JSON
    result_json = result.to_json()
    parsed = json.loads(result_json)
    assert parsed["summary"] == "Summary here"
    assert isinstance(parsed["issues"], list)
    assert parsed["suggestions"] == ["Do X", "Do Y"]

    # Markdown
    result_markdown = result.to_markdown()
    assert "# Review Summary" in result_markdown
    assert "Bug found" in result_markdown
    assert "Do X" in result_markdown


def test_markdown_no_issues_or_suggestions():
    result = ReviewResult(
        summary="Empty", issues=[], suggestions=[]
    )
    result_markdown = result.to_markdown()
    assert "No issues found" in result_markdown
    assert "No suggestions" in result_markdown
