# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
import tempfile
import shutil
import numpy as np
import nibabel as nib

from nipype.testing import assert_equal, skipif
from nipype.interfaces.freesurfer import model, no_freesurfer
import nipype.pipeline.engine as pe


@skipif(no_freesurfer)
def test_concatenate():
    tmp_dir = os.path.realpath(tempfile.mkdtemp())
    cwd = os.getcwd()
    os.chdir(tmp_dir)
    in1 = os.path.join(tmp_dir, 'cont1.nii')
    in2 = os.path.join(tmp_dir, 'cont2.nii')
    out = 'bar.nii'

    data1 = np.zeros((3, 3, 3, 1), dtype=np.float32)
    data2 = np.ones((3, 3, 3, 5), dtype=np.float32)
    out_data = np.concatenate((data1, data2), axis=3)
    mean_data = np.mean(out_data, axis=3)

    nib.Nifti1Image(data1, affine=np.eye(4)).to_filename(in1)
    nib.Nifti1Image(data2, affine=np.eye(4)).to_filename(in2)

    # Test default behavior
    res = model.Concatenate(in_files=[in1, in2]).run()
    yield (assert_equal, res.outputs.concatenated_file,
           os.path.join(tmp_dir, 'concat_output.nii.gz'))
    yield (assert_equal, nib.load('concat_output.nii.gz').get_data(), out_data)

    # Test specified concatenated_file
    res = model.Concatenate(in_files=[in1, in2], concatenated_file=out).run()
    yield (assert_equal, res.outputs.concatenated_file,
           os.path.join(tmp_dir, out))
    yield (assert_equal, nib.load(out).get_data(), out_data)

    # Test in workflow
    wf = pe.Workflow('test_concatenate', base_dir=tmp_dir)
    concat = pe.Node(model.Concatenate(in_files=[in1, in2],
                                       concatenated_file=out),
                     name='concat')
    wf.add_nodes([concat])
    wf.run()
    yield (assert_equal, nib.load(os.path.join(tmp_dir, 'test_concatenate',
                                               'concat', out)).get_data(),
           out_data)

    # Test a simple statistic
    res = model.Concatenate(in_files=[in1, in2], concatenated_file=out,
                            stats='mean').run()
    yield (assert_equal, nib.load(out).get_data(), mean_data)

    os.chdir(cwd)
    shutil.rmtree(tmp_dir)
