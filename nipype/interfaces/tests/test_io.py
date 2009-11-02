import os

from nipype.testing import *

import nipype.interfaces.io as nio

def test_aggregate_outputs():
    # Testing is datasource has a bad path and input files cannot be
    # found.
    ds = nio.DataSource()
    ds.inputs.base_directory = os.getcwd()
    ds.inputs.subject_template = '%s'
    ds.inputs.file_template = '%s.nii'
    info = {}
    info['s1'] = ((['f3','f5','f7','f10'],'func'), (['struct'],'struct'))
    ds.inputs.subject_info = info
    ds.inputs.subject_id = 's1'
    yield assert_raises, IOError, ds.aggregate_outputs
