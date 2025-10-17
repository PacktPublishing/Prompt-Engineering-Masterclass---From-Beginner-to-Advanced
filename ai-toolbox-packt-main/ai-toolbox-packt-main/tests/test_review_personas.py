from ai_toolbox.commands.review import (
    PERFORMANCE_REVIEW_TEMPLATE,
    MAINTAINABILITY_REVIEW_TEMPLATE,
    SECURITY_REVIEW_TEMPLATE,
)


def test_persona_templates_exist_and_have_structure():
    templates = [
        PERFORMANCE_REVIEW_TEMPLATE,
        MAINTAINABILITY_REVIEW_TEMPLATE,
        SECURITY_REVIEW_TEMPLATE,
    ]

    for tpl in templates:
        assert isinstance(tpl, str)
        assert "JSON object" in tpl
        assert "summary" in tpl
        assert "issues" in tpl
        assert "suggestions" in tpl
        # ensure they contain persona-specific keywords
    assert "performance" in PERFORMANCE_REVIEW_TEMPLATE.lower()
    assert (
        "maintainab" in MAINTAINABILITY_REVIEW_TEMPLATE.lower()
    )
    assert "security" in SECURITY_REVIEW_TEMPLATE.lower()
