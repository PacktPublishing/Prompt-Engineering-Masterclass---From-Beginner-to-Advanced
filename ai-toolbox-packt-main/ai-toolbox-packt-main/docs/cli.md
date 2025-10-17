## AI Toolbox CLI

The CLI entrypoint is implemented in `src/ai_toolbox/main.py` and uses Click to provide a command group and subcommands.

Global options (top-level)

- `--verbose`, `-v`: Enable verbose logging (sets Python logging to DEBUG).
- `--model`, `-m`: LLM model id passed to `litellm` calls. Defaults to `openai/gpt-4o-mini` in the code.

Top-level commands

- `hello` — Ask the configured LLM for a short, friendly greeting. Uses streaming completion via `litellm.completion(..., stream=True)` and prints chunks to stdout.
- `commit` — Generate a Conventional Commits compliant commit message from the staged diff. Presents an interactive flow where the user can approve, adjust (feedback loop to the LLM), or abort; if approved, the tool runs `git commit -m "<message>"`.
- `review` — Run a lightweight review pipeline over staged (default) or uncommitted diffs. The pipeline contains syntax and logic analyses, persona-based reviews and a synthesis/refinement stage. Output can be printed as markdown or JSON and optionally written to a file.

Examples

Run the module directly:

```bash
# show top-level help
python -m ai_toolbox.main --help

# greeting (uses configured model)
python -m ai_toolbox.main hello

# commit message generation (stage files first with `git add`)
python -m ai_toolbox.main commit

# run a review and print as markdown
python -m ai_toolbox.main review --staged --output markdown

# write review output to a file
python -m ai_toolbox.main review --output json --output-path review.json
```

Environment notes

- The CLI bootstraps environment variables from a `.env` file using `dotenv.load_dotenv()`; you can create a `.env` at the project root with your LLM credentials (or set env vars directly).
- `litellm` is used for model access; ensure your LLM provider is configured and available to `litellm`.
- `git` must be available in PATH for `commit` and `review` to retrieve diffs and run commits. Internally the code uses GitPython (`git.Repo`) to call git commands.

Safety & review

- The `commit` command runs `git commit` when you approve a generated message. Always review the generated message before approving.
- The `review` pipeline may call local developer tools via the tool registry (for example `pylint` and `bandit`). Those tools may not be installed by default; install them as needed (see contributing/dev setup).
