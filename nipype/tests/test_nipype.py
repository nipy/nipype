from .. import get_info
from ..info import get_nipype_gitversion
import pytest


def test_nipype_info():
    exception_not_raised = True
    try:
        get_info()
    except Exception:
        exception_not_raised = False
    assert exception_not_raised


@pytest.mark.skipif(not get_nipype_gitversion(),
                    reason="not able to get version from get_nipype_gitversion")
def test_git_hash():
    # removing the first "g" from gitversion
    get_nipype_gitversion()[1:] == get_info()['commit_hash']
