from nipype import utils
import pytest


@pytest.mark.parametrize("versioning", [True, False])
def test_pickle(tmp_path, versioning):
    testobj = 'iamateststr'
    pickle_fname = str(tmp_path / 'testpickle.pklz')
    utils.filemanip.savepkl(pickle_fname, testobj, versioning=versioning)
    outobj = utils.filemanip.loadpkl(pickle_fname)
    assert outobj == testobj
