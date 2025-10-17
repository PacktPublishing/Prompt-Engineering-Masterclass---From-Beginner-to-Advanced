"""Small git utilities using GitPython.

This module provides a minimal adapter used by the CLI commands. It
keeps error shapes similar to the previous subprocess-based code so
tests and callers can remain simple.
"""

from typing import Optional
from git import Repo


def _get_staged_diff(path: Optional[str] = None) -> str:
    """Return the repository's staged diff as a unified diff string.

    Uses GitPython's ``Repo.git.diff('--staged')`` to obtain the textual
    diff for files that have been staged (i.e. `git add` was run).

    Args:
        path: Optional repository path. Defaults to the current working directory.

    Returns:
        A unified diff string (possibly empty if nothing is staged).

    Raises:
        git.InvalidGitRepositoryError / git.GitCommandError: if the path is not a Git repository
        FileNotFoundError: if the underlying git binary or environment is missing
    """
    repo_path = path or "."

    repo = Repo(repo_path)
    # Use the git command interface to get the same textual diff
    diff_text = repo.git.diff("--staged")
    return diff_text


def _get_uncommitted_diff(path: Optional[str] = None) -> str:
    """Return the repository's uncommitted (working tree) diff as a string.

    This mirrors a plain ``git diff`` (no ``--staged``) and returns the
    textual diff for files with unstaged changes.

    Args:
        path: Optional repository path. Defaults to the current working directory.

    Returns:
        A unified diff string of uncommitted changes (empty if none).
    """
    repo_path = path or "."

    repo = Repo(repo_path)
    diff_text = repo.git.diff()
    return diff_text


def get_diff(
    staged: bool = True, path: Optional[str] = None
) -> str:
    """Return either the staged or uncommitted diff for a repository.

    Args:
        staged: If True return the staged diff (``git diff --staged``).
        path: Optional repository path to operate on; defaults to current dir.

    Returns:
        The requested unified diff as a string.
    """
    if staged:
        return _get_staged_diff(path=path)
    return _get_uncommitted_diff(path=path)


def run_commit(message: str, path: Optional[str] = None) -> None:
    """Create a git commit in ``path`` with the provided commit message.

    Args:
        message: Commit message text to use for the new commit.
        path: Optional repository path. Defaults to current working directory.

    Raises:
        git.GitCommandError / subprocess.CalledProcessError: on failure to commit.

    Notes:
        This function uses GitPython's ``repo.git.commit(m=message)`` which
        mirrors the behavior of calling ``git commit -m ...``. It does not
        stage files — the caller is expected to have staged the intended changes.
    """
    repo_path = path or "."

    repo = Repo(repo_path)
    repo.git.commit(m=message)
