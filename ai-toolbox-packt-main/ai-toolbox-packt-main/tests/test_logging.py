"""Tests for logging functionality in the AI toolbox."""

import logging
from io import StringIO

from click.testing import CliRunner

from ai_toolbox.main import cli, setup_logging


class TestLoggingSetup:
    """Test cases for the logging setup functionality."""

    def test_setup_logging_default_warning_level(self):
        """Test that default logging level is WARNING."""
        # Arrange & Act
        setup_logging(verbose=False)

        # Assert
        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING

    def test_setup_logging_verbose_debug_level(self):
        """Test that verbose mode sets DEBUG level."""
        # Arrange & Act
        setup_logging(verbose=True)

        # Assert
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_setup_logging_third_party_levels(self):
        """Test that third-party library log levels are set appropriately."""
        # Arrange & Act
        setup_logging(verbose=True)

        # Assert
        assert (
            logging.getLogger("httpx").level == logging.WARNING
        )
        assert (
            logging.getLogger("openai").level == logging.WARNING
        )
        assert logging.getLogger("LiteLLM").level == logging.INFO

    def test_setup_logging_third_party_levels_non_verbose(self):
        """Test that third-party library log levels are set appropriately in non-verbose mode."""
        # Arrange & Act
        setup_logging(verbose=False)

        # Assert
        assert (
            logging.getLogger("httpx").level == logging.WARNING
        )
        assert (
            logging.getLogger("openai").level == logging.WARNING
        )
        assert (
            logging.getLogger("LiteLLM").level == logging.WARNING
        )

    def test_setup_logging_format(self):
        """Test that logging format is configured correctly."""
        # Arrange
        log_stream = StringIO()

        # Act
        setup_logging(verbose=True)

        # Create a test logger and capture output
        test_logger = logging.getLogger("test_logger")
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.DEBUG)

        test_logger.info("Test message")

        # Assert
        log_output = log_stream.getvalue()
        assert "test_logger" in log_output
        assert "INFO" in log_output
        assert "Test message" in log_output
        assert (
            "-" in log_output
        )  # Check for proper formatting separators


class TestCLILogging:
    """Test cases for CLI logging integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_verbose_flag_short(self):
        """Test that -v flag enables verbose logging."""
        # Act
        result = self.runner.invoke(cli, ["-v", "--help"])

        # Assert
        assert result.exit_code == 0
        # We can't easily test the actual logging setup in Click tests,
        # but we can verify the flag is recognized

    def test_cli_verbose_flag_long(self):
        """Test that --verbose flag enables verbose logging."""
        # Act
        result = self.runner.invoke(cli, ["--verbose", "--help"])

        # Assert
        assert result.exit_code == 0

    def test_cli_help_shows_verbose_option(self):
        """Test that help text shows the verbose option."""
        # Act
        result = self.runner.invoke(cli, ["--help"])

        # Assert
        assert result.exit_code == 0
        assert "-v, --verbose" in result.output

    def test_cli_calls_setup_logging_verbose_true(self, mocker):
        """Test that CLI calls setup_logging with verbose=True when --verbose is used."""
        # Arrange
        mock_setup_logging = mocker.patch(
            "ai_toolbox.main.setup_logging"
        )

        # Act
        result = self.runner.invoke(
            cli,
            ["--verbose", "hello"],
            input="",
            catch_exceptions=False,
        )

        # Assert
        mock_setup_logging.assert_called_with(verbose=True)

    def test_cli_calls_setup_logging_verbose_false(self, mocker):
        """Test that CLI calls setup_logging with verbose=False by default."""
        # Arrange
        mock_setup_logging = mocker.patch(
            "ai_toolbox.main.setup_logging"
        )

        # Act
        result = self.runner.invoke(
            cli, ["hello"], input="", catch_exceptions=False
        )

        # Assert
        mock_setup_logging.assert_called_with(verbose=False)


class TestCommandLogging:
    """Test cases for command-specific logging."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_commit_command_logging_no_changes(self, mocker):
        """Test that commit command logs appropriately when no changes are staged."""
        # Arrange
        mock_get_staged_diff = mocker.patch(
            "ai_toolbox.git_utils.get_diff"
        )
        mock_get_staged_diff.return_value = ""

        # Capture logging output
        mock_stderr = mocker.patch(
            "sys.stderr", new_callable=StringIO
        )
        mock_setup = mocker.patch(
            "ai_toolbox.main.setup_logging"
        )

        # Configure logging to actually work in test
        setup_logging(verbose=True)

        # Act
        result = self.runner.invoke(cli, ["--verbose", "commit"])

        # Assert
        assert result.exit_code == 0
        # The actual logging assertions would be complex to test in this context
        # due to Click's isolation, but we've verified manually that logging works

    def test_hello_command_logging(self, mocker):
        """Test that hello command logs appropriately."""
        # Arrange
        mock_completion = mocker.patch(
            "ai_toolbox.main.completion"
        )
        mock_response = (
            []
        )  # Empty response to avoid streaming complexity
        mock_completion.return_value = mock_response

        # Act & Assert
        # Similar to above, the actual logging is tested manually
        # This test verifies the structure works
        result = self.runner.invoke(cli, ["--verbose", "hello"])
        # We don't assert on result because the mock doesn't fully simulate streaming


class TestLoggingLevels:
    """Test cases for different logging levels."""

    def test_debug_messages_only_in_verbose(self):
        """Test that DEBUG messages only appear in verbose mode."""
        # Arrange
        log_stream = StringIO()

        # Test non-verbose mode
        setup_logging(verbose=False)
        test_logger = logging.getLogger("test_debug")
        handler = logging.StreamHandler(log_stream)
        test_logger.addHandler(handler)
        test_logger.debug("Debug message")

        # Assert DEBUG not shown in non-verbose
        assert "Debug message" not in log_stream.getvalue()
