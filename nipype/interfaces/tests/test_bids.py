import os
import json
import sys

import pytest
from nipype.interfaces.bids_utils import BIDSDataGrabber
from nipype.utils.filemanip import dist_is_editable

have_pybids = True
try:
    import bids
    from bids import grabbids as gb
    filepath = os.path.realpath(os.path.dirname(bids.__file__))
    datadir = os.path.realpath(os.path.join(filepath, 'grabbids/tests/data/'))
except ImportError:
    have_pybids = False


# There are three reasons these tests will be skipped:
@pytest.mark.skipif(not have_pybids,
                    reason="Pybids is not installed")
@pytest.mark.skipif(sys.version_info < (3, 0),
                    reason="Pybids no longer supports Python 2")
@pytest.mark.skipif(not dist_is_editable('pybids'),
                    reason="Pybids is not installed in editable mode")
def test_bids_grabber(tmpdir):
    tmpdir.chdir()
    bg = BIDSDataGrabber()
    bg.inputs.base_dir = os.path.join(datadir, 'ds005')
    bg.inputs.subject = '01'
    results = bg.run()
    assert os.path.basename(results.outputs.anat[0]) == 'sub-01_T1w.nii.gz'
    assert os.path.basename(results.outputs.func[0]) == (
           'sub-01_task-mixedgamblestask_run-01_bold.nii.gz')


@pytest.mark.skipif(not have_pybids,
                    reason="Pybids is not installed")
@pytest.mark.skipif(sys.version_info < (3, 0),
                    reason="Pybids no longer supports Python 2")
@pytest.mark.skipif(not dist_is_editable('pybids'),
                    reason="Pybids is not installed in editable mode")
def test_bids_fields(tmpdir):
    tmpdir.chdir()
    bg = BIDSDataGrabber(infields = ['subject'], outfields = ['dwi'])
    bg.inputs.base_dir = os.path.join(datadir, 'ds005')
    bg.inputs.subject = '01'
    bg.inputs.output_query['dwi'] = dict(modality='dwi')
    results = bg.run()
    assert os.path.basename(results.outputs.dwi[0]) == 'sub-01_dwi.nii.gz'
