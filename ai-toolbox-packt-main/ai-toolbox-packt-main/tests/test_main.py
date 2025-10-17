from click.testing import CliRunner
from ai_toolbox.main import cli


def test_hello(mocker):
    runner = CliRunner()
    mock_completion = mocker.patch("ai_toolbox.main.completion")
    mock_completion.return_value = [
        mocker.Mock(
            choices=[
                mocker.Mock(
                    delta=mocker.Mock(
                        content="Mocked completion response"
                    )
                )
            ]
        )
    ]

    result = runner.invoke(cli, ["hello"])
    assert result.exit_code == 0
    assert "Mocked completion response" in result.output
