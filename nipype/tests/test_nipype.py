import os
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


@pytest.mark.skipif(
    not get_nipype_gitversion(),
    reason="not able to get version from get_nipype_gitversion",
)
def test_git_hash():
    # removing the first "g" from gitversion
    get_nipype_gitversion()[1:] == get_info()["commit_hash"]


def _check_no_et():
    import os
    from unittest.mock import patch

    et = os.getenv("NIPYPE_NO_ET") is None

    with patch.dict("os.environ", {"NIPYPE_NO_ET": "1"}):
        from nipype.interfaces.base import BaseInterface

        ver_data = BaseInterface._etelemetry_version_data

    if et and ver_data is None:
        raise ValueError(
            "etelemetry enabled and version data missing - double hits likely"
        )

    return et


def test_no_et_bare(tmp_path):
    from unittest.mock import patch
    from nipype.pipeline import engine as pe
    from nipype.interfaces import utility as niu
    from nipype.interfaces.base import BaseInterface

    et = os.getenv("NIPYPE_NO_ET") is None

    # Pytest doesn't trigger this, so let's pretend it's there
    with patch.object(BaseInterface, "_etelemetry_version_data", {}):

        # Direct function call - environment not set
        f = niu.Function(function=_check_no_et)
        res = f.run()
        assert res.outputs.out == et

        # Basic node - environment not set
        n = pe.Node(
            niu.Function(function=_check_no_et), name="n", base_dir=str(tmp_path)
        )
        res = n.run()
        assert res.outputs.out == et

        # Linear run - environment not set
        wf1 = pe.Workflow(name="wf1", base_dir=str(tmp_path))
        wf1.add_nodes([pe.Node(niu.Function(function=_check_no_et), name="n")])
        res = wf1.run()
        assert next(iter(res.nodes)).result.outputs.out == et


@pytest.mark.parametrize("plugin", ("MultiProc", "LegacyMultiProc"))
@pytest.mark.parametrize("run_without_submitting", (True, False))
def test_no_et_multiproc(tmp_path, plugin, run_without_submitting):
    from unittest.mock import patch
    from nipype.pipeline import engine as pe
    from nipype.interfaces import utility as niu
    from nipype.interfaces.base import BaseInterface

    et = os.getenv("NIPYPE_NO_ET") is None

    # Multiprocessing runs initialize new processes with NIPYPE_NO_ET
    # This does not apply to unsubmitted jobs, run by the main thread
    expectation = et if run_without_submitting else False

    # Pytest doesn't trigger this, so let's pretend it's there
    with patch.object(BaseInterface, "_etelemetry_version_data", {}):

        wf = pe.Workflow(name="wf2", base_dir=str(tmp_path))
        n = pe.Node(
            niu.Function(function=_check_no_et),
            run_without_submitting=run_without_submitting,
            name="n",
        )
        wf.add_nodes([n])
        res = wf.run(plugin=plugin, plugin_args={"n_procs": 1})
        assert next(iter(res.nodes)).result.outputs.out is expectation
