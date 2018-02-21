from .. import get_info


def test_nipype_info():
    exception_not_raised = True
    try:
        get_info()
    except Exception:
        exception_not_raised = False
    assert exception_not_raised


# def test_fail_always():
#     assert False
