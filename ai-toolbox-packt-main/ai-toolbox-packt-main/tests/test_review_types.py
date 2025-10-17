import json
import pytest
from typing import cast

from ai_toolbox.commands.review import (
    ReviewRequest,
    ReviewIssue,
    ReviewResult,
)


def test_review_request_valid_mode():
    req = ReviewRequest(diff="diff-text", mode="staged")
    assert req.diff == "diff-text"
    assert req.mode == "staged"


def test_review_request_invalid_mode():
    # Construct with a valid mode, then mutate to an invalid value and
    # call __post_init__ to trigger validation without static-type issues.
    req = ReviewRequest(diff="x", mode="staged")
    req.mode = "invalid"  # type: ignore[attr-defined]
    with pytest.raises(ValueError):
        req.__post_init__()


def test_review_issue_to_dict_and_review_result_to_dict():
    issue = ReviewIssue(
        id="ISSUE-1",
        severity="minor",
        category="style",
        description="Use f-strings",
        file="foo.py",
        line=10,
        snippet="- old\n+ new",
    )

    issue_dict = issue.to_dict()
    assert issue_dict["id"] == "ISSUE-1"
    assert issue_dict["severity"] == "minor"

    result = ReviewResult(
        summary="Found issues",
        issues=[issue],
        suggestions=["Refactor this function"],
    )

    result_dict = result.to_dict()
    assert result_dict["summary"] == "Found issues"
    assert isinstance(result_dict["issues"], list)
    assert result_dict["issues"][0]["id"] == "ISSUE-1"
    # Ensure JSON serialization works for result dict
    json.dumps(result_dict)
