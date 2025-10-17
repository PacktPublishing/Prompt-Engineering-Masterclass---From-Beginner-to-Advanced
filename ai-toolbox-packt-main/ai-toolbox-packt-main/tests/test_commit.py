"""Tests for the commit command module."""

import subprocess
import pytest
from click.testing import CliRunner
from unittest.mock import Mock
from litellm.exceptions import AuthenticationError

from ai_toolbox.commands.commit import (
    commit,
    get_staged_diff,
    COMMIT_MESSAGE_PROMPT_TEMPLATE,
)


class TestGetStagedDiff:
    """Test cases for the get_staged_diff function."""

    def test_get_staged_diff_success(self, mocker):
        """Test successful retrieval of staged diff."""
        # Arrange
        expected_diff = (
            "diff --git a/file.txt b/file.txt\n+new line\n"
        )
        mock_get = mocker.patch("ai_toolbox.git_utils.get_diff")
        mock_get.return_value = expected_diff

        # Act
        result = get_staged_diff()

        # Assert
        assert result == expected_diff
        mock_get.assert_called_once()

    def test_get_staged_diff_empty(self, mocker):
        """Test retrieval when no staged changes exist."""
        # Arrange
        mock_get = mocker.patch("ai_toolbox.git_utils.get_diff")
        mock_get.return_value = ""

        # Act
        result = get_staged_diff()

        # Assert
        assert result == ""
        mock_get.assert_called_once()

    def test_get_staged_diff_git_error(self, mocker):
        """Test handling of git command errors."""
        # Arrange
        from git import InvalidGitRepositoryError

        mock_get = mocker.patch("ai_toolbox.git_utils.get_diff")
        mock_get.side_effect = InvalidGitRepositoryError(
            "Not a git repo"
        )

        # Act & Assert - expect GitPython exception to surface
        with pytest.raises(InvalidGitRepositoryError):
            get_staged_diff()

    def test_get_staged_diff_git_not_found(self, mocker):
        """Test handling when git is not installed."""
        # Arrange
        mock_get = mocker.patch("ai_toolbox.git_utils.get_diff")
        mock_get.side_effect = FileNotFoundError(
            "git command not found"
        )

        # Act & Assert
        with pytest.raises(FileNotFoundError) as exc_info:
            get_staged_diff()

        assert "git command not found" in str(exc_info.value)


class TestCommitCommand:
    """Test cases for the commit click command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_commit_with_no_staged_changes(self, mocker):
        """Test commit command with no staged changes."""
        # Arrange
        mock_get_staged_diff = mocker.patch(
            "ai_toolbox.git_utils.get_diff"
        )
        mock_get_staged_diff.return_value = ""

        # Act
        result = self.runner.invoke(
            commit, obj={"model": "openai/gpt-4o-mini"}
        )

        # Assert
        assert result.exit_code == 0
        assert "No staged changes found" in result.output
        assert "Please stage some changes" in result.output
        mock_get_staged_diff.assert_called_once()

    def test_commit_with_whitespace_only_diff(self, mocker):
        """Test commit command with whitespace-only diff."""
        # Arrange
        mock_get_staged_diff = mocker.patch(
            "ai_toolbox.git_utils.get_diff"
        )
        mock_get_staged_diff.return_value = "   \n\t  \n"

        # Act
        result = self.runner.invoke(
            commit, obj={"model": "openai/gpt-4o-mini"}
        )

        # Assert
        assert result.exit_code == 0
        assert "No staged changes found" in result.output
        mock_get_staged_diff.assert_called_once()

    def test_commit_with_staged_changes_approve_workflow(
        self, mocker
    ):
        """Test commit command with staged changes and approve workflow."""
        # Arrange
        staged_diff = (
            "diff --git a/file.txt b/file.txt\n+new line\n"
        )
        generated_message = "feat: add new line to file.txt"

        mock_get_staged_diff = mocker.patch(
            "ai_toolbox.git_utils.get_diff"
        )
        mock_get_staged_diff.return_value = staged_diff

        # Mock the LLM completion
        mock_completion = mocker.patch(
            "ai_toolbox.commands.commit.completion"
        )
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            generated_message
        )
        mock_completion.return_value = mock_response

        # Mock subprocess.run for git commit
        mock_run = mocker.patch(
            "ai_toolbox.git_utils.run_commit"
        )

        # Act - simulate user choosing "1" (approve)
        result = self.runner.invoke(
            commit,
            input="1\n",
            obj={"model": "openai/gpt-4o-mini"},
        )

        # Assert
        assert result.exit_code == 0
        assert generated_message in result.output

        # Verify the LLM was called with correct prompt
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args
        assert len(call_args[1]["messages"]) == 1
        assert (
            staged_diff in call_args[1]["messages"][0]["content"]
        )

        # Verify git commit was called
        mock_run.assert_called_once_with(generated_message)

    def test_commit_with_staged_changes_abort_workflow(
        self, mocker
    ):
        """Test commit command with staged changes and abort workflow."""
        # Arrange
        staged_diff = (
            "diff --git a/file.txt b/file.txt\n+new line\n"
        )
        generated_message = "feat: add new line to file.txt"

        mock_get_staged_diff = mocker.patch(
            "ai_toolbox.git_utils.get_diff"
        )
        mock_get_staged_diff.return_value = staged_diff

        # Mock the LLM completion
        mock_completion = mocker.patch(
            "ai_toolbox.commands.commit.completion"
        )
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            generated_message
        )
        mock_completion.return_value = mock_response

        # Mock subprocess.run for git commit (should not be called)
        mock_run = mocker.patch(
            "ai_toolbox.git_utils.run_commit"
        )

        # Act - simulate user choosing "3" (abort)
        result = self.runner.invoke(
            commit,
            input="3\n",
            obj={"model": "openai/gpt-4o-mini"},
        )

        # Assert
        assert result.exit_code == 0
        assert generated_message in result.output

        # Verify git commit was NOT called
        mock_run.assert_not_called()

    def test_commit_with_staged_changes_adjust_workflow(
        self, mocker
    ):
        """Test commit command with staged changes and adjust workflow."""
        # Arrange
        staged_diff = (
            "diff --git a/file.txt b/file.txt\n+new line\n"
        )
        initial_message = "feat: add new line to file.txt"
        adjusted_message = (
            "feat: add important new line to file.txt"
        )

        mock_get_staged_diff = mocker.patch(
            "ai_toolbox.git_utils.get_diff"
        )
        mock_get_staged_diff.return_value = staged_diff

        # Mock the LLM completion - it will be called twice
        mock_completion = mocker.patch(
            "ai_toolbox.commands.commit.completion"
        )

        # First call returns initial message, second call returns adjusted message
        mock_response1 = Mock()
        mock_response1.choices = [Mock()]
        mock_response1.choices[0].message.content = (
            initial_message
        )

        mock_response2 = Mock()
        mock_response2.choices = [Mock()]
        mock_response2.choices[0].message.content = (
            adjusted_message
        )

        mock_completion.side_effect = [
            mock_response1,
            mock_response2,
        ]

        # Mock subprocess.run for git commit
        mock_run = mocker.patch(
            "ai_toolbox.git_utils.run_commit"
        )

        # Act - simulate user choosing "2" (adjust), providing feedback, then "1" (approve)
        result = self.runner.invoke(
            commit,
            input="2\nMake it more descriptive\n1\n",
            obj={"model": "openai/gpt-4o-mini"},
        )

        # Assert
        assert result.exit_code == 0
        assert initial_message in result.output
        assert adjusted_message in result.output

        # Verify the LLM was called twice
        assert mock_completion.call_count == 2

        # Check the second call includes the conversation history
        second_call_args = mock_completion.call_args_list[1]
        messages = second_call_args[1]["messages"]
        assert (
            len(messages) == 3
        )  # Original prompt + assistant response + user adjustment
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == initial_message
        assert messages[2]["role"] == "user"
        assert (
            messages[2]["content"] == "Make it more descriptive"
        )

        # Verify git commit was called with the adjusted message
        mock_run.assert_called_once_with(adjusted_message)

    def test_commit_git_commit_failure(self, mocker):
        """Test commit command when git commit fails."""
        # Arrange
        staged_diff = (
            "diff --git a/file.txt b/file.txt\n+new line\n"
        )
        generated_message = "feat: add new line to file.txt"

        mock_get_staged_diff = mocker.patch(
            "ai_toolbox.git_utils.get_diff"
        )
        mock_get_staged_diff.return_value = staged_diff

        # Mock the LLM completion
        mock_completion = mocker.patch(
            "ai_toolbox.commands.commit.completion"
        )
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            generated_message
        )
        mock_completion.return_value = mock_response

        # Mock subprocess.run for git commit to fail
        mock_run = mocker.patch(
            "ai_toolbox.git_utils.run_commit"
        )
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["git", "commit", "-m", generated_message],
            stderr="fatal: unable to create temporary file: Permission denied",
        )

        # Act - simulate user choosing "1" (approve)
        result = self.runner.invoke(
            commit,
            input="1\n",
            obj={"model": "openai/gpt-4o-mini"},
        )

        # Assert
        assert result.exit_code == 0
        assert "Permission denied" in result.output

    def test_commit_llm_authentication_error(self, mocker):
        """Test commit command when LLM authentication fails."""
        # Arrange
        staged_diff = (
            "diff --git a/file.txt b/file.txt\n+new line\n"
        )

        mock_get_staged_diff = mocker.patch(
            "ai_toolbox.git_utils.get_diff"
        )
        mock_get_staged_diff.return_value = staged_diff

        # Mock the LLM completion to raise AuthenticationError
        mock_completion = mocker.patch(
            "ai_toolbox.commands.commit.completion"
        )
        mock_completion.side_effect = AuthenticationError(
            message="Invalid API key",
            llm_provider="openai",
            model="gpt-4o-mini",
        )

        # Act
        result = self.runner.invoke(
            commit, obj={"model": "openai/gpt-4o-mini"}
        )

        # Assert
        assert result.exit_code == 0
        assert "Authentication failed." in result.output

    def test_commit_llm_general_error(self, mocker):
        """Test commit command when LLM call fails with general error."""
        # Arrange
        staged_diff = (
            "diff --git a/file.txt b/file.txt\n+new line\n"
        )

        mock_get_staged_diff = mocker.patch(
            "ai_toolbox.git_utils.get_diff"
        )
        mock_get_staged_diff.return_value = staged_diff

        # Mock the LLM completion to raise a general error
        mock_completion = mocker.patch(
            "ai_toolbox.commands.commit.completion"
        )
        mock_completion.side_effect = Exception(
            "Network timeout"
        )

        # Act
        result = self.runner.invoke(
            commit, obj={"model": "openai/gpt-4o-mini"}
        )

        # Assert
        assert result.exit_code == 0
        assert "Network timeout" in result.output

    def test_commit_empty_llm_response(self, mocker):
        """Test commit command when LLM returns empty response."""
        # Arrange
        staged_diff = (
            "diff --git a/file.txt b/file.txt\n+new line\n"
        )

        mock_get_staged_diff = mocker.patch(
            "ai_toolbox.git_utils.get_diff"
        )
        mock_get_staged_diff.return_value = staged_diff

        # Mock the LLM completion to return empty content
        mock_completion = mocker.patch(
            "ai_toolbox.commands.commit.completion"
        )
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = None
        mock_completion.return_value = mock_response

        # Mock subprocess.run for git commit
        mock_run = mocker.patch(
            "ai_toolbox.git_utils.run_commit"
        )

        # Act - simulate user choosing "1" (approve)
        result = self.runner.invoke(
            commit,
            input="1\n",
            obj={"model": "openai/gpt-4o-mini"},
        )

        # Assert
        assert result.exit_code == 0
        # Verify git commit was called with empty message
        mock_run.assert_called_once_with("")

    def test_commit_git_error(self, mocker):
        """Test commit command when git command fails."""
        # Arrange
        from git import InvalidGitRepositoryError

        mock_get_staged_diff = mocker.patch(
            "ai_toolbox.git_utils.get_diff"
        )
        mock_get_staged_diff.side_effect = (
            InvalidGitRepositoryError("Not a git repo")
        )

        # Act
        result = self.runner.invoke(
            commit, obj={"model": "openai/gpt-4o-mini"}
        )

        # Assert
        assert (
            result.exit_code == 0
        )  # Click command doesn't exit with error code
        assert "Error running git command" in result.output
        mock_get_staged_diff.assert_called_once()

    def test_commit_git_not_found(self, mocker):
        """Test commit command when git is not installed."""
        # Arrange
        mock_get_staged_diff = mocker.patch(
            "ai_toolbox.git_utils.get_diff"
        )
        mock_get_staged_diff.side_effect = FileNotFoundError(
            "Git command not found. Please ensure git is installed and in your PATH."
        )

        # Act
        result = self.runner.invoke(
            commit, obj={"model": "openai/gpt-4o-mini"}
        )

        # Assert
        assert (
            result.exit_code == 0
        )  # Click command doesn't exit with error code
        assert "Error: Git command not found" in result.output
        mock_get_staged_diff.assert_called_once()


class TestCommitPromptTemplate:
    """Test cases for the commit prompt template."""

    def test_prompt_template_format(self):
        """Test that the prompt template formats correctly with diff."""
        # Arrange
        test_diff = "diff --git a/example.py b/example.py\n+print('hello')\n"

        # Act
        formatted_prompt = COMMIT_MESSAGE_PROMPT_TEMPLATE.format(
            diff=test_diff
        )

        # Assert
        assert (
            "You are an expert software developer"
            in formatted_prompt
        )
        assert (
            "Conventional Commits specification"
            in formatted_prompt
        )
        assert test_diff in formatted_prompt
        assert "<diff>" in formatted_prompt
        assert "</diff>" in formatted_prompt
        assert (
            "Generate an appropriate commit message"
            in formatted_prompt
        )

    def test_prompt_template_includes_instructions(self):
        """Test that the prompt template includes all necessary instructions."""
        # Arrange
        test_diff = "test diff content"

        # Act
        formatted_prompt = COMMIT_MESSAGE_PROMPT_TEMPLATE.format(
            diff=test_diff
        )

        # Assert
        # Check for key instruction elements
        assert (
            "Follow the Conventional Commits specification"
            in formatted_prompt
        )
        assert (
            "Keep the first line (title) under 50 characters"
            in formatted_prompt
        )
        assert "Use imperative mood" in formatted_prompt
        assert (
            "Start with lowercase after the colon"
            in formatted_prompt
        )
        assert (
            "Do not end the title with a period"
            in formatted_prompt
        )

        # Check for commit types
        assert "feat: new feature" in formatted_prompt
        assert "fix: bug fix" in formatted_prompt
        assert "docs: documentation changes" in formatted_prompt
        assert "refactor: code change" in formatted_prompt
        assert (
            "test: adding or modifying tests" in formatted_prompt
        )
        assert "chore: maintenance tasks" in formatted_prompt

        # Check for output format instructions
        assert (
            "First line: commit title following conventional commits"
            in formatted_prompt
        )
        assert (
            "BREAKING CHANGE: <description>" in formatted_prompt
        )
        assert (
            "Return only the commit message text"
            in formatted_prompt
        )


class TestCommitCommandEdgeCases:
    """Test edge cases for the commit command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_commit_multiple_adjust_cycles(self, mocker):
        """Test commit command with multiple adjust cycles before approval."""
        # Arrange
        staged_diff = (
            "diff --git a/file.txt b/file.txt\n+new line\n"
        )
        messages = [
            "feat: add line",
            "feat: add new line to file",
            "feat: add important new line to file.txt",
        ]

        mock_get_staged_diff = mocker.patch(
            "ai_toolbox.git_utils.get_diff"
        )
        mock_get_staged_diff.return_value = staged_diff

        # Mock the LLM completion - it will be called three times
        mock_completion = mocker.patch(
            "ai_toolbox.commands.commit.completion"
        )
        mock_responses = []
        for message in messages:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = message
            mock_responses.append(mock_response)

        mock_completion.side_effect = mock_responses

        # Mock git_utils.run_commit for git commit
        mock_run = mocker.patch(
            "ai_toolbox.git_utils.run_commit"
        )

        # Act - simulate user choosing "2" (adjust) twice, then "1" (approve)
        result = self.runner.invoke(
            commit,
            input="2\nMake it longer\n2\nAdd file extension\n1\n",
            obj={"model": "openai/gpt-4o-mini"},
        )

        # Assert
        assert result.exit_code == 0
        assert messages[0] in result.output  # First message
        assert messages[1] in result.output  # Second message
        assert messages[2] in result.output  # Final message

        # Verify the LLM was called three times
        assert mock_completion.call_count == 3

        # Verify git commit was called with the final message
        mock_run.assert_called_once_with(messages[2])

    def test_commit_invalid_user_choice_then_valid(self, mocker):
        """Test commit command with invalid user choice followed by valid choice."""
        # Arrange
        staged_diff = (
            "diff --git a/file.txt b/file.txt\n+new line\n"
        )
        generated_message = "feat: add new line to file.txt"

        mock_get_staged_diff = mocker.patch(
            "ai_toolbox.git_utils.get_diff"
        )
        mock_get_staged_diff.return_value = staged_diff

        # Mock the LLM completion
        mock_completion = mocker.patch(
            "ai_toolbox.commands.commit.completion"
        )
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            generated_message
        )
        mock_completion.return_value = mock_response

        # Mock git_utils.run_commit for git commit
        mock_run = mocker.patch(
            "ai_toolbox.git_utils.run_commit"
        )

        # Act - simulate user entering invalid choice (4), then valid choice (1)
        # Note: click.IntRange should handle this, but we test the behavior
        result = self.runner.invoke(
            commit,
            input="4\n1\n",
            obj={"model": "openai/gpt-4o-mini"},
        )

        # Assert
        assert result.exit_code == 0
        assert "✅ Commit created successfully." in result.output
        mock_run.assert_called_once()

    def test_commit_with_unicode_characters(self, mocker):
        """Test commit command with unicode characters in diff."""
        # Arrange
        staged_diff = "diff --git a/unicode.txt b/unicode.txt\n+Hello 🌍 World! Café résumé naïve\n"
        generated_message = (
            "feat: add unicode greeting with special characters"
        )

        mock_get_staged_diff = mocker.patch(
            "ai_toolbox.git_utils.get_diff"
        )
        mock_get_staged_diff.return_value = staged_diff

        # Mock the LLM completion
        mock_completion = mocker.patch(
            "ai_toolbox.commands.commit.completion"
        )
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            generated_message
        )
        mock_completion.return_value = mock_response

        # Mock git_utils.run_commit for git commit
        mock_run = mocker.patch(
            "ai_toolbox.git_utils.run_commit"
        )

        # Act
        result = self.runner.invoke(
            commit,
            input="1\n",
            obj={"model": "openai/gpt-4o-mini"},
        )

        # Assert
        assert result.exit_code == 0
        assert "✅ Commit created successfully." in result.output

        # Verify git commit was called with the unicode message
        mock_run.assert_called_once_with(generated_message)
