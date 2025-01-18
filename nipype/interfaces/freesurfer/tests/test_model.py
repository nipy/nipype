# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import numpy as np
import nibabel as nb

import pytest

from nipype.interfaces.freesurfer import model, no_freesurfer
import nipype.pipeline.engine as pe


@pytest.mark.skipif(no_freesurfer(), reason="freesurfer is not installed")
def test_concatenate(tmpdir):
    tmpdir.chdir()

    in1 = tmpdir.join("cont1.nii").strpath
    in2 = tmpdir.join("cont2.nii").strpath
    out = "bar.nii"

    data1 = np.zeros((3, 3, 3, 1), dtype=np.float32)
    data2 = np.ones((3, 3, 3, 5), dtype=np.float32)
    out_data = np.concatenate((data1, data2), axis=3)
    mean_data = np.mean(out_data, axis=3)

    nb.Nifti1Image(data1, affine=np.eye(4)).to_filename(in1)
    nb.Nifti1Image(data2, affine=np.eye(4)).to_filename(in2)

    # Test default behavior
    res = model.Concatenate(in_files=[in1, in2]).run()
    assert res.outputs.concatenated_file == tmpdir.join("concat_output.nii.gz").strpath
    assert np.allclose(nb.load("concat_output.nii.gz").get_fdata(), out_data)

    # Test specified concatenated_file
    res = model.Concatenate(in_files=[in1, in2], concatenated_file=out).run()
    assert res.outputs.concatenated_file == tmpdir.join(out).strpath
    assert np.allclose(nb.load(out).get_fdata(), out_data)

    # Test in workflow
    wf = pe.Workflow("test_concatenate", base_dir=tmpdir.strpath)
    concat = pe.Node(
        model.Concatenate(in_files=[in1, in2], concatenated_file=out), name="concat"
    )
    wf.add_nodes([concat])
    wf.run()
    assert np.allclose(
        nb.load(tmpdir.join("test_concatenate", "concat", out).strpath).get_fdata(),
        out_data,
    )

    # Test a simple statistic
    res = model.Concatenate(
        in_files=[in1, in2], concatenated_file=out, stats="mean"
    ).run()
    assert np.allclose(nb.load(out).get_fdata(), mean_data)
