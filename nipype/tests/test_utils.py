from nipype import utils
import pytest


@pytest.mark.parametrize("load_versioning", [True, False])
@pytest.mark.parametrize("save_versioning", [True, False])
def test_pickle(tmp_path, save_versioning, load_versioning):
    testobj = 'iamateststr'
    pickle_fname = str(tmp_path / 'testpickle.pklz')
    utils.filemanip.savepkl(pickle_fname, testobj, versioning=save_versioning)
    outobj = utils.filemanip.loadpkl(pickle_fname, versioning=load_versioning)
    assert outobj == testobj
