__author__ = 'oliver'

from ..preprocess import create_featreg_preproc, pickrun


def test_pickrun():
    files = ['1', '2', '3', '4']
    assert pickrun(files, 0) == '1'
    assert pickrun(files, 'first') == '1'
    assert pickrun(files, -1) == '4'
    assert pickrun(files, 'last') == '4'
    assert pickrun(files, 'middle') == '3'


def test_create_featreg_preproc():
    """smoke test"""
    wf = create_featreg_preproc(whichrun=0)

    # test type
    import nipype
    assert type(wf) == nipype.pipeline.engine.Workflow

    # test methods
    assert wf.get_node('extractref')
    assert wf._get_dot()
