"""Utility wrappers around external developer tools (pylint, bandit).

These wrappers intentionally return the raw stdout/stderr as a string so the
calling code or AI can decide how to interpret the output.
"""

import subprocess
from .tool_registry import ToolRegistry


TOOL_REGISTRY = ToolRegistry()


def _sanitize_path(path: str) -> str:
    """Validate and normalize a filesystem path for tool invocation.

    The tool wrappers in this module expect a non-empty string path. For
    convenience, common shorthand paths such as ".", "/" and "~" are
    normalized to the project "src" directory so linters/scan tools run
    against the package code by default.

    Args:
        path: Path string provided by the caller.

    Returns:
        A trimmed, normalized path string suitable for subprocess invocation.

    Raises:
        ValueError: If the path is empty or not a string.
    """
    if not isinstance(path, str) or not path.strip():
        raise ValueError("path must be a non-empty string")

    if path.strip() in [".", "/", "~"]:
        path = "src"

    return path.strip()


@TOOL_REGISTRY.register_tool()
def run_pylint(path: str) -> str:
    """Run ``pylint`` on ``path`` and return combined stdout/stderr.

    This wrapper executes ``pylint <path>`` via ``subprocess.run`` and
    returns the combined stdout/stderr text. The function intentionally
    does not raise when the ``pylint`` executable is missing; instead it
    returns a descriptive error string to make the wrapper safe for use
    inside LLM-driven tool flows.

    Args:
        path: Filesystem path to analyze (will be sanitized by ``_sanitize_path``).

    Returns:
        Raw output from pylint (stdout+stderr) or an error placeholder string
        like "<error: pylint not installed>" if the executable is not found.
    """
    sanitized_path = _sanitize_path(path)

    cmd = ["pylint", sanitized_path]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return out
    except FileNotFoundError:
        return "<error: pylint not installed>"
    except Exception as e:  # pragma: no cover - defensive
        return f"<error: {e}>"


@TOOL_REGISTRY.register_tool()
def run_security_scan(path: str) -> str:
    """Run ``bandit -r <path> -f json`` and return raw output.

    The function returns the combined stdout/stderr of the executed bandit
    command. If ``bandit`` is not installed the function returns a
    placeholder string (rather than raising) to allow safe use from LLM
    tool flows.

    Args:
        path: Filesystem path to scan; will be sanitized by ``_sanitize_path``.

    Returns:
        The bandit output (JSON text) or an error placeholder string.
    """
    sanitized_path = _sanitize_path(path)

    cmd = ["bandit", "-r", sanitized_path, "-f", "json"]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return out
    except FileNotFoundError:
        return "<error: bandit not installed>"
    except Exception as e:  # pragma: no cover - defensive
        return f"<error: {e}>"
