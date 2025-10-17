import pytest

from ai_toolbox import tool_utils


class DummyCompletedProcess:
    def __init__(self, stdout: str = "", stderr: str = ""):
        self.stdout = stdout
        self.stderr = stderr


def test_run_pylint_returns_combined_output(mocker):
    cp = DummyCompletedProcess(
        stdout="pylint-out", stderr="pylint-err"
    )
    mock_run = mocker.patch("subprocess.run", return_value=cp)

    out = tool_utils.run_pylint("some/path.py")
    assert "pylint-out" in out
    assert "pylint-err" in out
    mock_run.assert_called_once()


def test_run_security_scan_returns_output(mocker):
    cp = DummyCompletedProcess(
        stdout='{"results": []}', stderr=""
    )
    mock_run = mocker.patch("subprocess.run", return_value=cp)

    out = tool_utils.run_security_scan("some/path")
    assert "results" in out
    mock_run.assert_called_once()


def test_run_pylint_file_not_found(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.side_effect = FileNotFoundError()

    out = tool_utils.run_pylint("some/path.py")
    assert "pylint not installed" in out


def test_run_security_scan_file_not_found(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.side_effect = FileNotFoundError()

    out = tool_utils.run_security_scan("some/path")
    assert "bandit not installed" in out


def test_validate_path_raises_on_empty():
    with pytest.raises(ValueError):
        tool_utils.run_pylint("")
    with pytest.raises(ValueError):
        tool_utils.run_security_scan("")
