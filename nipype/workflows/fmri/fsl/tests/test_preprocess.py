__author__ = 'oliver, with additions by adina'

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

def test_create_featreg_preproc_params():
    """
    Test workflow generation for differing preprocessing complexities.
    """
    #create the full range of complexety the workflow can display
    #motion correction, highpass filtering, smoothing
    full = create_featreg_preproc()
    nomc1 = create_featreg_preproc(whichrun = None)
    nomc2 = create_featreg_preproc(whichvol = None)
    nomc3 = create_featreg_preproc(whichrun = None, whichvol = None)
    nohp = create_featreg_preproc(highpass = False)
    nohp_nomc = create_featreg_preproc(whichvol = None, highpass = False)
    #obtain list of node names
    nodes_full = full.list_node_names()
    nodes_nomc1 = nomc1.list_node_names()
    nodes_nomc2 = nomc2.list_node_names()
    nodes_nomc3 = nomc3.list_node_names()
    nodes_nohp = nohp.list_node_names()
    nodes_nohp_nomc = nohp_nomc.list_node_names()

    # test that using either or both None options yields identical wf
    assert nodes_nomc1 == nodes_nomc2 == nodes_nomc3

    # test that no motion correction strips realignment, ref. extraction and
    # motion plots from wf
    node_diff = [node for node in nodes_full if node not in nodes_nomc1 and
    nodes_nomc2 and nodes_nomc3 and nodes_nohp_nomc]
    checklist = ['extractref', 'plot_motion', 'realign']
    assert all(string in node_diff for string in checklist)

    # test that no highpass filtering strips addmean, hiphpass and meanfunc4
    # node from wf
    node_diff_hp = [node for node in nodes_full if node not in nodes_nohp]
    checklist_hp = ['addmean', 'highpass', 'meanfunc4']
    assert all(string in node_diff_hp for string in checklist_hp)
