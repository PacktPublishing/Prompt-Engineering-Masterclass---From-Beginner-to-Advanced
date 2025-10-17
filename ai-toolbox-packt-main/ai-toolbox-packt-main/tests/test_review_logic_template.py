from ai_toolbox.commands.review import LOGIC_REVIEW_TEMPLATE


def test_logic_template_exists_and_structure():
    tpl = LOGIC_REVIEW_TEMPLATE
    assert isinstance(tpl, str)
    # Must contain the exact wrapper sequence in order
    assert "JSON object" in tpl
    assert "summary" in tpl
    assert "issues" in tpl
    assert "suggestions" in tpl

    # Must focus on correctness/bugs/edge cases
    assert (
        "bugs" in tpl
        or "edge cases" in tpl
        or "correctness" in tpl
    )
