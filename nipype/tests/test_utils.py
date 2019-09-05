from nipype import utils


def test_pickle(tmp_path):
    testobj = 'iamateststr'
    pickle_fname = str(tmp_path / 'testpickle.pklz')
    utils.filemanip.savepkl(pickle_fname, testobj)
    outobj = utils.filemanip.loadpkl(pickle_fname)
    assert outobj == testobj


def test_pickle_versioning(tmp_path):
    testobj = 'iamateststr'
    pickle_fname = str(tmp_path / 'testpickle.pklz')
    utils.filemanip.savepkl(pickle_fname, testobj, versioning=True)
    outobj = utils.filemanip.loadpkl(pickle_fname)
    assert outobj == testobj
