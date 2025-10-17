import json
from unittest.mock import Mock
from ai_toolbox.commands.review import (
    run_reviews_with_personas,
    synthesize_perspectives,
    self_consistency_review,
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


def test_run_reviews_with_personas_and_synthesis(mocker):
    diff = "diff --git a/file.py b/file.py\n+print('hi')\n"

    # Mock persona completions
    perf_resp = make_mock_response(
        json.dumps(
            {
                "summary": "perf",
                "issues": [],
                "suggestions": ["opt"],
            }
        )
    )
    maint_resp = make_mock_response(
        json.dumps(
            {
                "summary": "maint",
                "issues": [],
                "suggestions": ["refactor"],
            }
        )
    )
    sec_resp = make_mock_response(
        json.dumps(
            {
                "summary": "sec",
                "issues": [],
                "suggestions": ["fix"],
            }
        )
    )

    mock_completion = mocker.patch(
        "ai_toolbox.commands.review.helpers.completion"
    )
    # persona calls: performance, maintainability, security, then synthesis, then self-consistency
    synth_resp = make_mock_response(
        json.dumps(
            {
                "summary": "synth",
                "issues": [],
                "suggestions": ["plan"],
            }
        )
    )
    refined_resp = make_mock_response(
        json.dumps(
            {
                "summary": "refined",
                "issues": [],
                "suggestions": ["final-plan"],
            }
        )
    )

    mock_completion.side_effect = [
        perf_resp,
        maint_resp,
        sec_resp,
        synth_resp,
        refined_resp,
    ]

    reviews = run_reviews_with_personas(
        diff,
        model="fake-model",
        personas_dict={
            "performance": "performance",
            "maintainability": "maintainability",
            "security": "security",
        },
    )
    assert "performance" in reviews
    assert "maintainability" in reviews
    assert "security" in reviews

    synthesis = synthesize_perspectives(
        reviews, model="fake-model"
    )
    assert synthesis.summary == "synth"
    assert synthesis.issues == []
    assert synthesis.suggestions == ["plan"]

    refined = self_consistency_review(
        synthesis, model="fake-model"
    )
    assert refined.summary == "refined"
    assert refined.issues == []
    assert refined.suggestions == ["final-plan"]

    # Ensure completion was called 5 times
    assert mock_completion.call_count == 5


def test_pipeline_skips_llm_when_no_model():
    diff = "diff"
    reviews = run_reviews_with_personas(
        diff,
        model=None,
        personas_dict={
            "performance": "performance",
            "maintainability": "maintainability",
            "security": "security",
        },
    )
    assert (
        reviews["performance"].summary
        == "No model provided - skipping review"
    )
    assert (
        reviews["maintainability"].summary
        == "No model provided - skipping review"
    )
    assert (
        reviews["security"].summary
        == "No model provided - skipping review"
    )

    synthesis = synthesize_perspectives(reviews, model=None)
    assert (
        synthesis.summary
        == "No model provided - skipping review"
    )

    test_synthesis = ReviewResult(
        summary="some synthesis", issues=[], suggestions=[]
    )
    refined = self_consistency_review(test_synthesis, model=None)
    assert (
        refined.summary == "No model provided - skipping review"
    )
