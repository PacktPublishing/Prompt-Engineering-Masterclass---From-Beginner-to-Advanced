from ai_toolbox import git_utils


def test_get_diff_staged_calls_repo_git_diff(mocker):
    mock_repo = mocker.Mock()
    mock_repo.git.diff.return_value = "STAGED_DIFF"

    mocker.patch(
        "ai_toolbox.git_utils.Repo", return_value=mock_repo
    )
    diff = git_utils.get_diff(staged=True, path=".")
    assert diff == "STAGED_DIFF"
    mock_repo.git.diff.assert_called_with("--staged")


def test_get_diff_uncommitted_calls_repo_git_diff(mocker):
    mock_repo = mocker.Mock()
    mock_repo.git.diff.return_value = "WORKTREE_DIFF"

    mocker.patch(
        "ai_toolbox.git_utils.Repo", return_value=mock_repo
    )
    diff = git_utils.get_diff(staged=False, path=".")
    assert diff == "WORKTREE_DIFF"
    mock_repo.git.diff.assert_called_with()


def test_run_commit_calls_repo_commit(mocker):
    mock_repo = mocker.Mock()

    mocker.patch(
        "ai_toolbox.git_utils.Repo", return_value=mock_repo
    )
    git_utils.run_commit("msg", path=".")
    mock_repo.git.commit.assert_called_with(m="msg")
