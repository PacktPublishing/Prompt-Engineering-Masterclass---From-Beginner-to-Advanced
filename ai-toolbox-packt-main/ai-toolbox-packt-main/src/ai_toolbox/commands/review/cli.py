import click
import logging
from ...git_utils import get_diff
from .helpers import run_review_pipeline

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--staged/--uncommitted",
    default=True,
    help="Choose to review staged changes (default) or uncommitted changes.",
)
@click.option(
    "--output",
    type=click.Choice(
        ["markdown", "json"], case_sensitive=False
    ),
    default="markdown",
    help="Choose output format: markdown (default) or json.",
)
@click.option(
    "--output-path",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Optional path to write the output to (file will be overwritten).",
)
@click.pass_context
def review(
    ctx: click.Context,
    staged: bool,
    output: str,
    output_path: str,
) -> None:
    """Run the repository review pipeline and print or write the result.

    The command collects a git diff (staged or uncommitted) and runs the
    higher-level ``run_review_pipeline`` helper which coordinates syntax,
    logic, persona and synthesis phases. The output is returned as a
    ``ReviewResult`` and can be printed as markdown (default) or JSON.

    Args:
        ctx: Click context, expects ``ctx.obj['model']`` for LLM model id.
        staged: If True review staged changes (default); otherwise review uncommitted changes.
        output: Output format: "markdown" or "json".
        output_path: Optional file path to write output; if not provided output is printed to stdout.
    """
    mode = "staged" if staged else "uncommitted"
    logger.info(f"Running review command in mode: {mode}")

    # Retrieve diff from git and run the lightweight pipeline
    click.echo("🔎 Retrieving git diff...")
    diff = get_diff(staged=staged)

    # Get model from context (mirror commit.py behavior)
    model = ctx.obj.get("model", "openai/gpt-4o-mini")
    logger.debug(f"Using model for review command: {model}")
    click.echo(f"🤖 Using model: {model}")

    click.echo(
        "🚦 Starting review pipeline (this may take a while)..."
    )
    result = run_review_pipeline(diff=diff, model=model)

    # Prepare formatted output
    out_format = output or "markdown"
    out_path = output_path

    if out_format.lower() == "json":
        formatted = result.to_json()
    else:
        formatted = result.to_markdown()

    if out_path:
        try:
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(formatted)
            click.echo(f"Wrote review output to: {out_path}")
        except Exception as e:
            logger.exception(
                "Failed to write review output to file: %s", e
            )
            click.echo(f"Failed to write to {out_path}: {e}")
    else:
        click.echo(formatted)
