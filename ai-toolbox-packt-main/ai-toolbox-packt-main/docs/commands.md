Commands

This document describes the primary commands implemented in the project and how they behave.

## hello

- Purpose: Generate a short, friendly greeting using an LLM.
- Location: `src/ai_toolbox/main.py` (function: `hello`).
- Behavior: Builds a concise prompt and calls `litellm.completion(..., stream=True)` to stream the generated text and print it to stdout. Handles authentication errors from `litellm` and prints a short error message if the call fails.

## commit

- Purpose: Generate a Conventional Commits-compliant commit message from staged changes and optionally create the commit.
- Location: `src/ai_toolbox/commands/commit.py` (function: `commit`).
- Behavior summary:
  - Reads the staged diff using `ai_toolbox.git_utils.get_diff(staged=True)` (GitPython-based adapter).
  - If no staged changes exist, prints an informative message and exits.
  - Formats the staged diff into a prompt that instructs the LLM to produce a Conventional Commits-style message (title + optional body, breaking change handling).
  - Calls `litellm.completion` to generate the message, shows it to the user in a framed block and asks the user to: Approve / Adjust / Abort.
  - On Approve: calls `ai_toolbox.git_utils.run_commit(message)` to create the commit.
  - On Adjust: collects user feedback, appends it to the conversation, and regenerates the message (simple feedback loop).

## review

- Purpose: Run a small review pipeline over a git diff that includes syntax checks, logic analysis, persona-based reviews (performance, maintainability, security), synthesis and a self-consistency pass.
- Location: `src/ai_toolbox/commands/review/cli.py` and review pipeline helpers in `src/ai_toolbox/commands/review/*`.
- Behavior summary:
  - Retrieves either staged (`--staged`, default) or uncommitted diffs from `ai_toolbox.git_utils.get_diff`.
  - Runs `run_review_pipeline(diff, model)` which performs several phases:
    - Syntax analysis (`analyze_syntax`) — small LLM pass to find syntax / style issues.
    - Logic analysis (`analyze_logic`) — an LLM pass that may request tool calls (via the Tool Registry) to inspect code or run linters.
    - Persona reviews — runs persona templates (performance, maintainability, security) and collects their outputs.
    - Synthesis — combines persona outputs and produces a refined report.
    - Self-consistency review — a final LLM pass to critique and refine the synthesized report.
  - Output: the command can print a markdown report (default) or JSON and can optionally write the output to a file via `--output-path`.

## Tooling integration

The review logic can call local developer tools via a small tool registry implemented in `src/ai_toolbox/tool_registry.py`. Example wrapped tools live in `src/ai_toolbox/tool_utils.py` and include:

- `run_pylint(path)` — runs `pylint` on a path and returns combined stdout/stderr.
- `run_security_scan(path)` — runs `bandit -r <path> -f json` and returns the raw output.

Those tools are registered in a global `TOOL_REGISTRY` so the LLM-driven logic can request tool calls and receive results.

## Notes & safety

- LLM-driven behaviors rely on `litellm`. Provide credentials via environment variables or a `.env` file.
- The `commit` command will run `git commit` when you approve a generated message — always verify the message before approval.
- Tools like `pylint` and `bandit` are invoked by subprocesses when requested; installing the `dev` extras (`pip install -e .[dev]`) provides them for local testing.
