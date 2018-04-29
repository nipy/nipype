# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import
import os

import pytest
import nipype.interfaces.fsl as fsl
import nipype.interfaces.utility as util
from nipype.interfaces.fsl import no_fsl, no_fsl_course_data

import nipype.pipeline.engine as pe
import warnings
from nipype.workflows.dmri.fsl.dti import create_bedpostx_pipeline
from nipype.utils.filemanip import simplify_list


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
@pytest.mark.skipif(no_fsl_course_data(), reason="fsl data not available")
def test_create_bedpostx_pipeline(tmpdir):
    fsl_course_dir = os.path.abspath(os.environ['FSL_COURSE_DATA'])

    mask_file = os.path.join(fsl_course_dir,
                             "fdt2/subj1.bedpostX/nodif_brain_mask.nii.gz")
    bvecs_file = os.path.join(fsl_course_dir, "fdt2/subj1/bvecs")
    bvals_file = os.path.join(fsl_course_dir, "fdt2/subj1/bvals")
    dwi_file = os.path.join(fsl_course_dir, "fdt2/subj1/data.nii.gz")
    z_min = 62
    z_size = 2

    slice_mask = pe.Node(
        fsl.ExtractROI(
            x_min=0, x_size=-1, y_min=0, y_size=-1, z_min=z_min,
            z_size=z_size),
        name="slice_mask")
    slice_mask.inputs.in_file = mask_file

    slice_dwi = pe.Node(
        fsl.ExtractROI(
            x_min=0, x_size=-1, y_min=0, y_size=-1, z_min=z_min,
            z_size=z_size),
        name="slice_dwi")
    slice_dwi.inputs.in_file = dwi_file

    nipype_bedpostx = create_bedpostx_pipeline("nipype_bedpostx")
    nipype_bedpostx.inputs.inputnode.bvecs = bvecs_file
    nipype_bedpostx.inputs.inputnode.bvals = bvals_file
    nipype_bedpostx.inputs.xfibres.n_fibres = 1
    nipype_bedpostx.inputs.xfibres.fudge = 1
    nipype_bedpostx.inputs.xfibres.burn_in = 0
    nipype_bedpostx.inputs.xfibres.n_jumps = 1
    nipype_bedpostx.inputs.xfibres.sample_every = 1
    nipype_bedpostx.inputs.xfibres.cnlinear = True
    nipype_bedpostx.inputs.xfibres.seed = 0
    nipype_bedpostx.inputs.xfibres.model = 2

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        original_bedpostx = pe.Node(
            interface=fsl.BEDPOSTX(), name="original_bedpostx")
    original_bedpostx.inputs.bvecs = bvecs_file
    original_bedpostx.inputs.bvals = bvals_file
    original_bedpostx.inputs.environ['FSLPARALLEL'] = ""
    original_bedpostx.inputs.n_fibres = 1
    original_bedpostx.inputs.fudge = 1
    original_bedpostx.inputs.burn_in = 0
    original_bedpostx.inputs.n_jumps = 1
    original_bedpostx.inputs.sample_every = 1
    original_bedpostx.inputs.seed = 0
    original_bedpostx.inputs.model = 2

    test_f1 = pe.Node(util.AssertEqual(), name="mean_f1_test")

    pipeline = pe.Workflow(name="test_bedpostx")
    pipeline.base_dir = tmpdir.mkdir("nipype_test_bedpostx_").strpath

    pipeline.connect([
        (slice_mask, original_bedpostx, [("roi_file", "mask")]),
        (slice_mask, nipype_bedpostx, [("roi_file", "inputnode.mask")]),
        (slice_dwi, original_bedpostx, [("roi_file", "dwi")]),
        (slice_dwi, nipype_bedpostx, [("roi_file", "inputnode.dwi")]),
        (nipype_bedpostx, test_f1, [(("outputnode.mean_fsamples",
                                      simplify_list), "volume1")]),
        (original_bedpostx, test_f1, [("mean_fsamples", "volume2")]),
    ])

    pipeline.run(plugin='Linear')
