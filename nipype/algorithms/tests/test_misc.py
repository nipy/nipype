# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import pytest
import os

import nibabel as nb

from nipype.algorithms import misc
from nipype.utils.filemanip import fname_presuffix
from nipype.testing.fixtures import create_analyze_pair_file_in_directory
from nipype.utils import NUMPY_MMAP
from nipype.testing import example_data


def test_CreateNifti(create_analyze_pair_file_in_directory):

    filelist, outdir = create_analyze_pair_file_in_directory

    create_nifti = misc.CreateNifti()

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        create_nifti.run()

    # .inputs based parameters setting
    create_nifti.inputs.header_file = filelist[0]
    create_nifti.inputs.data_file = fname_presuffix(
        filelist[0], '', '.img', use_ext=False)

    result = create_nifti.run()

    assert os.path.exists(result.outputs.nifti_file)
    assert nb.load(result.outputs.nifti_file, mmap=NUMPY_MMAP)


def test_CalculateMedian(create_analyze_pair_file_in_directory):

    mean = misc.CalculateMedian()

    with pytest.raises(TypeError):
        mean.run()

    mean.inputs.in_files = example_data('ds003_sub-01_mc.nii.gz')
    eg = mean.run()

    assert os.path.exists(eg.outputs.median_files)
    assert nb.load(eg.outputs.median_files, mmap=NUMPY_MMAP)
