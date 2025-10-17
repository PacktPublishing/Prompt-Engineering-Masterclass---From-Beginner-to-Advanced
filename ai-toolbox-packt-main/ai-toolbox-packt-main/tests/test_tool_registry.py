import pytest

from ai_toolbox.tool_registry import ToolRegistry


def test_list_tools_contains_registered_items():
    r = ToolRegistry()
    assert isinstance(r.list_tools(), list)


def test_register_and_get_tool_programmatic():
    called = {}
    r = ToolRegistry()

    @r.register_tool()
    def dummy(path: str) -> str:
        called["path"] = path
        return "ok"

    assert "dummy" in r.list_tools()
    td = r.get_tool("dummy")
    assert td is not None
    assert td.func is dummy


def test_generate_tool_schema_and_call():
    r = ToolRegistry()

    @r.register_tool(name="f_tool", description="f desc")
    def f(a: str, b: int = 3) -> str:
        return f"{a}:{b}"

    schema = r.generate_tool_schema("f_tool")
    assert schema is not None

    func_schema = schema["function"]
    assert func_schema["name"] == "f_tool"

    params = func_schema["parameters"]
    assert params["type"] == "object"
    assert "a" in params["properties"]

    res = r.call_tool("f_tool", a="x", b=7)
    assert res == "x:7"


def test_call_tool_missing():
    r = ToolRegistry()
    with pytest.raises(KeyError):
        r.call_tool("nonexistent_tool")


def test_generate_all_tool_schemas():
    # Register a small tool and ensure it's present in the list
    r = ToolRegistry()

    @r.register_tool(name="alpha_tool", description="alpha")
    def alpha(x: str) -> str:
        return x

    schemas = r.generate_all_tool_schemas()
    assert isinstance(schemas, list)
    # find our tool
    names = [s["function"]["name"] for s in schemas]
    assert "alpha_tool" in names
