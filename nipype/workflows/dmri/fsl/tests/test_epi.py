# -*- coding: utf-8 -*-
import os

import pytest
import nipype.workflows.fmri.fsl as fsl_wf
import nipype.interfaces.fsl as fsl
import nipype.interfaces.utility as util
from nipype.interfaces.fsl import no_fsl, no_fsl_course_data

import nipype.pipeline.engine as pe
import warnings
from nipype.workflows.dmri.fsl.epi import create_eddy_correct_pipeline


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
@pytest.mark.skipif(no_fsl_course_data(), reason="fsl data not available")
def test_create_eddy_correct_pipeline(tmpdir):
    fsl_course_dir = os.path.abspath(os.environ['FSL_COURSE_DATA'])

    dwi_file = os.path.join(fsl_course_dir, "fdt1/subj1/data.nii.gz")

    trim_dwi = pe.Node(fsl.ExtractROI(t_min=0, t_size=2), name="trim_dwi")
    trim_dwi.inputs.in_file = dwi_file

    nipype_eddycorrect = create_eddy_correct_pipeline("nipype_eddycorrect")
    nipype_eddycorrect.inputs.inputnode.ref_num = 0

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        original_eddycorrect = pe.Node(
            interface=fsl.EddyCorrect(), name="original_eddycorrect")
    original_eddycorrect.inputs.ref_num = 0

    test = pe.Node(util.AssertEqual(), name="eddy_corrected_dwi_test")

    pipeline = pe.Workflow(name="test_eddycorrect")
    pipeline.base_dir = tmpdir.mkdir("nipype_test_eddycorrect_").strpath

    pipeline.connect([
        (trim_dwi, original_eddycorrect, [("roi_file", "in_file")]),
        (trim_dwi, nipype_eddycorrect, [("roi_file", "inputnode.in_file")]),
        (nipype_eddycorrect, test, [("outputnode.eddy_corrected", "volume1")]),
        (original_eddycorrect, test, [("eddy_corrected", "volume2")]),
    ])

    pipeline.run(plugin='Linear')
