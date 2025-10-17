import click
import logging
from textwrap import dedent
from typing import Any
from dotenv import load_dotenv
from litellm import completion
from litellm.exceptions import AuthenticationError

from .commands import commit
from .commands import review


load_dotenv()  # Load environment variables from .env file

# Configure logging
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure Python logging for the CLI.

    This sets a sensible default format and adjusts third-party logger
    verbosity to keep CLI output readable. When ``verbose`` is True the
    root logger is set to DEBUG; otherwise WARNING.

    Side effects:
    - calls ``logging.basicConfig`` with a fixed format and datefmt
    - adjusts levels for ``httpx``, ``openai`` and ``LiteLLM`` loggers

    Args:
        verbose: Enable DEBUG-level logging when True.
    """
    # Set the root logger level
    log_level = logging.DEBUG if verbose else logging.WARNING

    # Configure the root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,  # Override any existing configuration
    )

    # Set specific loggers for third-party libraries to avoid noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("LiteLLM").setLevel(
        logging.INFO if verbose else logging.WARNING
    )

    logger.debug(
        f"Logging configured with level: {logging.getLevelName(log_level)}"
    )


@click.group()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging (DEBUG level).",
)
@click.option(
    "--model",
    "-m",
    default="openai/gpt-4o-mini",
    help="LLM model to use for generation (default: openai/gpt-4o-mini).",
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool, model: str) -> None:
    """Top-level Click command group initializer.

    The function prepares the Click context object (``ctx.obj``) with
    runtime options consumed by subcommands and calls ``setup_logging``.

    Args:
        ctx: Click context (passed automatically by Click).
        verbose: If True enable DEBUG logging for the process.
        model: Default LLM model id used by commands (stored in ``ctx.obj['model']``).

    Effects:
        - populates ``ctx.obj['verbose']`` and ``ctx.obj['model']``
        - configures logging
    """
    # Ensure that ctx.obj exists and is a dict (Click context object)
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["model"] = model

    # Set up logging based on verbosity
    setup_logging(verbose=verbose)
    logger.info("AI Toolbox CLI started")
    logger.debug(f"Verbose mode: {verbose}")
    logger.debug(f"Using model: {model}")


@click.command()
@click.pass_context
def hello(ctx: click.Context) -> None:
    """Generate and print a short greeting using the configured LLM.

    This command constructs a simple prompt and streams the completion
    response from ``litellm.completion(..., stream=True)`` to stdout.

    Args:
        ctx: Click context; expects ``ctx.obj['model']`` to contain the model id.

    Behavior / errors:
        - On authentication errors raised by ``litellm`` the command prints a
          short message prompting the user to check credentials.
        - Other exceptions are logged and a brief error message is printed.
    """
    logger.info("Starting hello command")

    # Get model from context
    model = ctx.obj.get("model", "openai/gpt-4o-mini")
    logger.debug(f"Using model for hello command: {model}")

    prompt = dedent(
        """
        Generate a one-sentence, friendly and concise
        greeting message for the AI toolbox CLI user.
        """
    )

    logger.debug(f"Generated prompt: {prompt.strip()}")

    try:
        logger.debug(
            "Calling LLM completion API with streaming enabled"
        )
        response: Any = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        logger.debug(
            "Successfully received LLM response, processing stream"
        )
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                logger.debug(f"Received chunk: {repr(content)}")
                click.echo(content, nl=False)
        click.echo()
        logger.info("Hello command completed successfully")

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        click.echo(
            "Authentication failed. Please check your API key."
        )
    except Exception as e:
        logger.error(
            f"Unexpected error in hello command: {e}",
            exc_info=True,
        )
        click.echo(f"Error generating greeting: {e}")


cli.add_command(hello)
cli.add_command(commit)
cli.add_command(review)

if __name__ == "__main__":
    cli()
