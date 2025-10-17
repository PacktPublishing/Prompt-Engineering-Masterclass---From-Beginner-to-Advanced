"""Commit command for the AI toolbox CLI.

This module provides a `commit` click command which (eventually)
generates a commit message based on staged changes.
"""

import subprocess
import click
import logging
from typing import Any
from litellm import completion
from litellm.exceptions import AuthenticationError
from git import InvalidGitRepositoryError, GitCommandError

from .. import git_utils

# Set up module logger
logger = logging.getLogger(__name__)

COMMIT_MESSAGE_PROMPT_TEMPLATE = """You are an expert software developer tasked with generating a concise and informative commit message based on the provided git diff.

**Instructions:**
1. Follow the Conventional Commits specification (https://www.conventionalcommits.org/)
2. Use this format: `<type>[optional scope]: <description>`
3. Keep the first line (title) under 50 characters
4. Use imperative mood (e.g., "add", "fix", "update", not "added", "fixed", "updated")
5. Start with lowercase after the colon
6. Do not end the title with a period

**Common types:**
- feat: new feature
- fix: bug fix
- docs: documentation changes
- style: formatting, missing semicolons, etc.
- refactor: code change that neither fixes a bug nor adds a feature
- test: adding or modifying tests
- chore: maintenance tasks, dependencies, build process
- perf: performance improvements
- ci: continuous integration changes

**Output format:**
- First line: commit title following conventional commits
- Afterwards, a blank line followed by commit body with additional details
- Return only the commit message text, no extra formatting or explanations
- In case of a breaking change, please add BREAKING CHANGE: <description> in the commit body

**Git diff to analyze:**

<diff>
{diff}
</diff>

Generate an appropriate commit message based on the changes shown in the diff above."""


def get_staged_diff() -> str:
    """Retrieve the staged git diff for the current repository.

    Returns the unified diff string for files staged for commit. This is a
    thin wrapper around ``ai_toolbox.git_utils.get_diff(staged=True)`` and
    preserves the same exceptions from GitPython/Git.

    Returns:
        The staged unified diff as a string (may be empty).

    Raises:
        See ``ai_toolbox.git_utils``: InvalidGitRepositoryError, GitCommandError, FileNotFoundError
    """
    logger.debug(
        "Starting to retrieve staged git diff via git_utils"
    )
    try:
        diff_text = git_utils.get_diff(staged=True)
        diff_length = len(diff_text)
        logger.debug(
            f"Successfully retrieved git diff, length: {diff_length} characters"
        )

        if diff_length == 0:
            logger.info("No staged changes found in git diff")
        else:
            logger.info(
                f"Retrieved staged diff with {diff_length} characters"
            )

        return diff_text
    # TODO: Probably we can get rid of this exception handling
    except subprocess.CalledProcessError as e:
        logger.error(f"Git diff command failed: {e}")
        # Re-raise to preserve previous behavior
        raise
    except FileNotFoundError as e:
        logger.error(f"Git command not found: {e}")
        raise


@click.command()
@click.pass_context
def commit(ctx: click.Context) -> None:
    """Interactive commit message generator using an LLM.

    Flow summary:
    1. Retrieves staged diff via ``get_staged_diff``.
    2. If no staged changes exist, informs the user and exits.
    3. Formats a Conventional Commits prompt and calls the LLM to generate
       a commit message.
    4. Presents the generated message and lets the user Approve, Adjust or Abort.
       - Approve: runs ``ai_toolbox.git_utils.run_commit`` with the generated message.
       - Adjust: prompts the user for feedback, appends it to the LLM conversation and regenerates.
       - Abort: exits without committing.

    Args:
        ctx: Click context - expects ``ctx.obj['model']`` to contain the LLM model id.

    Errors & side effects:
        - May raise/catch GitPython exceptions when reading diffs or committing.
        - When approved, this command creates a git commit in the repository.
        - AuthenticationError from LLMs is handled and reported to the user.
    """
    logger.info("Starting commit command")

    # Get model from context
    model = ctx.obj.get("model", "openai/gpt-4o-mini")
    logger.debug(f"Using model for commit command: {model}")

    try:
        logger.debug("Retrieving staged changes from git")
        staged_diff = get_staged_diff()

        if not staged_diff.strip():
            logger.warning(
                "No staged changes found - aborting commit generation"
            )
            click.echo(
                "No staged changes found. Please stage some changes before generating a commit message."
            )
            return

        logger.info(
            "Staged changes found, preparing commit message generation"
        )
        logger.debug(
            "Formatting commit prompt template with diff"
        )
        commit_prompt = COMMIT_MESSAGE_PROMPT_TEMPLATE.format(
            diff=staged_diff
        )

        # Log prompt length for debugging
        prompt_length = len(commit_prompt)
        logger.debug(
            f"Generated commit prompt with {prompt_length} characters"
        )

        # Prepare the LLM messages history; we'll append assistant/user turns on adjust
        messages = [{"role": "user", "content": commit_prompt}]
        logger.debug(
            f"Initialized conversation with {len(messages)} message(s)"
        )

        # Inform the user we're generating the commit message
        click.echo(
            "🤖 Generating commit message, please hold..."
        )

        try:
            iteration_count = 0
            while True:
                iteration_count += 1
                logger.debug(
                    f"Starting commit generation iteration {iteration_count}"
                )

                # Call the LLM to generate the commit message
                logger.debug(
                    f"Calling LLM completion with {len(messages)} messages using model {model}"
                )
                response: Any = completion(
                    model=model,
                    messages=messages,
                )
                logger.debug(
                    "Successfully received LLM response"
                )

                # Extract generated content (assumes non-streaming response)
                generated_message = (
                    response.choices[0].message.content or ""
                ).strip()

                logger.info(
                    f"Generated commit message: {repr(generated_message)}"
                )
                logger.debug(
                    f"Message length: {len(generated_message)} characters"
                )

                # Display generated message inside a clear formatted block
                click.echo(
                    "\n----- Generated commit message -----"
                )
                click.echo(generated_message)
                click.echo("----- End commit message -----\n")

                # Offer numeric choices to the user (default: Approve)
                click.echo(
                    "Choose one of the following actions:\n"
                )
                click.echo("1) Approve (default)")
                click.echo("2) Adjust")
                click.echo("3) Abort")

                logger.debug(
                    "Prompting user for action selection"
                )
                selection = click.prompt(
                    "Choose an action",
                    type=click.IntRange(1, 3),
                    default=1,
                    show_default=True,
                )
                choice = {1: "approve", 2: "adjust", 3: "abort"}[
                    selection
                ]
                logger.info(f"User selected action: {choice}")

                if choice.lower() == "approve":
                    logger.info(
                        "User approved commit message, proceeding with git commit"
                    )
                    try:
                        logger.debug(
                            f"Executing git commit via git_utils with message: {repr(generated_message)}"
                        )
                        git_utils.run_commit(generated_message)
                        logger.info(
                            "Git commit executed successfully"
                        )
                        click.echo(
                            "✅ Commit created successfully."
                        )
                    except subprocess.CalledProcessError as e:
                        logger.error(
                            f"Git commit failed with return code {e.returncode}: {e.stderr}"
                        )
                        click.echo(
                            f"Error committing changes: {e.stderr}",
                            err=True,
                        )
                    return

                if choice.lower() == "abort":
                    logger.info("User aborted commit generation")
                    click.echo("Aborted...")
                    return

                # If user chose Adjust, collect feedback and loop
                if choice.lower() == "adjust":
                    logger.info(
                        "User requested adjustment to commit message"
                    )
                    # Save the assistant's last message and ask the user for adjustment
                    messages.append(
                        {
                            "role": "assistant",
                            "content": generated_message,
                        }
                    )
                    logger.debug(
                        "Added assistant message to conversation history"
                    )

                    adjustment = click.prompt(
                        "Describe the changes you'd like to make to the commit message",
                    )
                    logger.info(
                        f"User provided adjustment feedback: {repr(adjustment)}"
                    )

                    # Append the user's adjustment request to the conversation
                    messages.append(
                        {"role": "user", "content": adjustment}
                    )
                    logger.debug(
                        f"Added user adjustment to conversation history. Total messages: {len(messages)}"
                    )

                    # Inform about generation and continue loop to regenerate
                    click.echo(
                        "🤖 Regenerating commit message with your feedback..."
                    )
                    continue

        except AuthenticationError as e:
            logger.error(f"LLM authentication failed: {e}")
            click.echo(
                "Authentication failed. Please check your API key.",
                err=True,
            )
        except Exception as e:
            logger.error(
                f"Error during LLM interaction: {e}",
                exc_info=True,
            )
            click.echo(
                f"Error generating commit message: {e}", err=True
            )

    except (
        subprocess.CalledProcessError,
        InvalidGitRepositoryError,
        GitCommandError,
    ) as e:
        # Handle both subprocess-based errors and GitPython exceptions
        logger.error(f"Git command error: {e}")
        click.echo(f"Error running git command: {e}", err=True)
    except FileNotFoundError as e:
        logger.error(f"Git not found error: {e}")
        click.echo(f"Error: {e}", err=True)
