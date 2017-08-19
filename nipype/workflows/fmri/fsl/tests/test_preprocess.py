__author__ = 'oliver'

from ..preprocess import create_featreg_preproc, pickrun


def test_pickrun():
    files = ['1', '2', '3']
    assert pickrun(files, 0) == '1'
    assert pickrun(files, -1) == '3'


def test_create_featreg_preproc():
    # smoke test
    wf = create_featreg_preproc(whichrun=0)
    wf.get_node('extractref')
    assert wf._get_dot()
