## Contributing & development

This page contains concrete steps to set up a local development environment, run tests, and package the project.

Local development setup

1. Create and activate a virtual environment (macOS / zsh):

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install editable package with dev extras (installs pytest, pylint, bandit):

```bash
python -m pip install -e .[dev]
```

3. Provide LLM credentials

- The CLI bootstraps environment variables by calling `dotenv.load_dotenv()`. Create a `.env` file in the project root or set environment variables directly. `litellm` will read whichever variables it needs for authentication. For example your `.env` may contain provider-specific keys; consult your `litellm` provider docs.

Optional tools

- To exercise the `tool_utils` wrappers install `pylint` and `bandit` (already included in dev extras). These are used by the tool registry if the LLM requests them.

Running tests

Run the full test suite with:

```bash
pytest -q
```

The tests are located in the `tests/` directory and cover the CLI, git utilities, tool registry and review helpers.

Linting / security scanning

- Run pylint:

```bash
pylint src/ai_toolbox
```

- Run bandit (security scan):

```bash
bandit -r src/ai_toolbox
```

Packaging

Build a wheel using the pyproject configuration:

```bash
python -m build
```

Then publish using your preferred workflow (for example Twine to publish to PyPI).

Developer notes

- The CLI entry point is `ai_toolbox.main:cli` and a console script `ai-toolbox` is defined in `pyproject.toml`.
- The code prefers `litellm` for model calls and wraps errors like authentication failures to provide helpful CLI messages.
- The review pipeline is intentionally modular: `analyze_syntax`, `analyze_logic`, persona review functions and the tool registry can be changed independently; add tests when modifying their public behavior.
