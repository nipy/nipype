import os
import shutil
from tempfile import mkdtemp
from nipype.testing import assert_equal
import nipype.interfaces.io as nio

def test_aggregate_outputs():
    basedir = mkdtemp()
    os.makedirs(os.path.join(basedir,'s1'))
    filename = os.path.join(basedir,'s1','s1.nii')
    fp = open(filename,'w')
    fp.close()
    ds = nio.SubjectSource()
    ds.inputs.base_directory = basedir
    ds.inputs.file_layout = 's%s.nii'
    ds.inputs.subject_info = dict(func=['1'])
    ds.inputs.subject_id = 's1'
    res = ds.run()
    yield assert_equal, res.outputs.func, filename
    shutil.rmtree(basedir)
