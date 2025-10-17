from ai_toolbox.commands.review import SYNTAX_REVIEW_TEMPLATE


def test_syntax_template_exists_and_structure():
    tpl = SYNTAX_REVIEW_TEMPLATE
    assert isinstance(tpl, str)
    # Must contain the exact wrapper sequence in order
    assert "JSON object" in tpl
    assert "summary" in tpl
    assert "issues" in tpl
    assert "suggestions" in tpl
    # Must mention out-of-scope items
    assert (
        "ignore logical" in tpl
        or "Do NOT comment on program correctness" in tpl
    )
    # Must mention PEP 8 or style
    assert "PEP 8" in tpl or "style" in tpl
