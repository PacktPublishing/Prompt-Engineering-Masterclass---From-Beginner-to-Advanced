from __future__ import annotations

"""A minimal, extensible registry for external developer tools.

Design goals:
- Lean: single small module, easy API (register, list, get schema, call).
- Extensible: supports decorator or programmatic registration.
- Useful for LLM tool schemas: can emit a JSON-schema-like parameters object.

The registry will try to auto-register functions found in `ai_toolbox.tool_utils`
if that module is importable.
"""

from dataclasses import dataclass
import inspect
import typing as t


P = t.ParamSpec("P")
R = t.TypeVar("R")


@dataclass
class ToolDescriptor:
    name: str
    func: t.Callable
    description: str
    params_schema: dict


def _pytype_to_json_type(py: type) -> str:
    """Map a Python builtin type to a JSON-schema style type name.

    The function returns a best-effort mapping used when generating a
    parameters schema for registered tools. Unknown types default to
    "string" for safety.
    """
    mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }
    
    return mapping.get(py, "string")


def _build_params_schema(func: t.Callable) -> dict:
    """Build a simple JSON-like parameters schema from a Python callable.

    The generated schema contains property names, simple types and
    default values when available. Var positional/keyword parameters are
    ignored for schema simplicity.

    Args:
        func: Callable to inspect.

    Returns:
        A dict representing a JSON-schema-like object with `properties`
        and optionally `required` keys.
    """
    sig = inspect.signature(func)
    props: dict[str, dict] = {}
    required: list[str] = []
    for name, p in sig.parameters.items():
        # Skip VAR_POSITIONAL and VAR_KEYWORD for schema simplicity
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        ann = (
            p.annotation
            if p.annotation is not inspect._empty
            else str
        )
        json_type = _pytype_to_json_type(
            ann if isinstance(ann, type) else str
        )
        prop: dict = {"type": json_type}
        if p.default is inspect._empty:
            required.append(name)
        else:
            # expose default for convenience
            prop["default"] = p.default
        props[name] = prop

    schema = {
        "type": "object",
        "properties": props,
    }
    if required:
        schema["required"] = required
    return schema


class ToolRegistry:
    """An instance-based registry for tools.

    Use an instance when you want isolation (e.g. tests). A module-level
    `default_registry` is provided for convenience/backward-compat.
    """

    def __init__(self) -> None:
        self._registry: dict[str, ToolDescriptor] = {}

    def register_tool(
        self,
        name: str | None = None,
        description: str | None = None,
        params_schema: dict | None = None,
    ):
        """Decorator / programmatic registration bound to this registry instance."""

        def decorator(
            func: t.Callable[P, R],
        ) -> t.Callable[P, R]:
            tool_name = name or func.__name__
            desc = description or (func.__doc__ or "").strip()
            schema = params_schema or _build_params_schema(func)
            self._registry[tool_name] = ToolDescriptor(
                name=tool_name,
                func=func,
                description=desc,
                params_schema=schema,
            )
            return func

        return decorator

    def list_tools(self) -> list[str]:
        return list(self._registry.keys())

    def get_tool(self, name: str) -> ToolDescriptor | None:
        return self._registry.get(name)

    def generate_tool_schema(self, name: str) -> dict | None:
        td = self.get_tool(name)
        if not td:
            return None
        return {
            "type": "function",
            "function": {
                "name": td.name,
                "description": td.description,
                "parameters": td.params_schema,
            },
        }

    def generate_all_tool_schemas(self) -> list[dict]:
        schemas: list[dict] = []
        for name in self.list_tools():
            s = self.generate_tool_schema(name)
            if s is not None:
                schemas.append(s)
        return schemas

    def call_tool(self, name: str, /, **kwargs):
        td = self.get_tool(name)
        if not td:
            raise KeyError(f"tool not found: {name}")
        return td.func(**kwargs)
