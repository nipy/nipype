from .. import get_info
from ..info import get_nipype_gitversion


def test_nipype_info():
    exception_not_raised = True
    try:
        get_info()
    except Exception:
        exception_not_raised = False
    assert exception_not_raised


def test_git_hash():
    #removing the first "g" from gitversion
    get_nipype_gitversion()[1:] == get_info()['commit_hash']
