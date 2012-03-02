import os

from nipype.testing import (skipif)
import nipype.workflows.fmri.fsl as fsl_wf
import nipype.interfaces.fsl as fsl
import nipype.interfaces.utility as util
from nipype.interfaces.fsl import no_fsl, no_fsl_course_data

import nipype.pipeline.engine as pe
import warnings
import tempfile
import shutil
from nipype.workflows.dmri.fsl.dti import create_eddy_correct_pipeline,\
    create_bedpostx_pipeline


@skipif(no_fsl)
@skipif(no_fsl_course_data)
def test_create_eddy_correct_pipeline():
    fsl_course_dir = os.path.abspath('fsl_course_data')

    dwi_file = os.path.join(fsl_course_dir, "fdt/subj1/data.nii.gz")

    nipype_eddycorrect = create_eddy_correct_pipeline("nipype_eddycorrect")
    nipype_eddycorrect.inputs.inputnode.in_file = dwi_file
    nipype_eddycorrect.inputs.inputnode.ref_num = 0

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        original_eddycorrect = pe.Node(interface=fsl.EddyCorrect(), name="original_eddycorrect")
    original_eddycorrect.inputs.in_file = dwi_file
    original_eddycorrect.inputs.ref_num = 0

    test = pe.Node(util.AssertEqual(), name="eddy_corrected_dwi_test")

    pipeline = pe.Workflow(name="test_eddycorrect")
    pipeline.base_dir = tempfile.mkdtemp(prefix="nipype_test_eddycorrect_")

    pipeline.connect([(nipype_eddycorrect, test, [("outputnode.eddy_corrected", "volume1")]),
                      (original_eddycorrect, test, [("eddy_corrected", "volume2")]),
                      ])

    pipeline.run(plugin='Linear')
    shutil.rmtree(pipeline.base_dir)


@skipif(no_fsl)
@skipif(no_fsl_course_data)
def test_create_bedpostx_pipeline():
    fsl_course_dir = os.path.abspath('fsl_course_data')

    mask_file = os.path.join(fsl_course_dir, "fdt/subj1.bedpostX/nodif_brain_mask.nii.gz")
    bvecs_file = os.path.join(fsl_course_dir, "fdt/subj1/bvecs")
    bvals_file = os.path.join(fsl_course_dir, "fdt/subj1/bvals")
    dwi_file = os.path.join(fsl_course_dir, "fdt/subj1/data.nii.gz")

    nipype_bedpostx = create_bedpostx_pipeline("nipype_bedpostx")
    nipype_bedpostx.inputs.inputnode.dwi = dwi_file
    nipype_bedpostx.inputs.inputnode.mask = mask_file
    nipype_bedpostx.inputs.inputnode.bvecs = bvecs_file
    nipype_bedpostx.inputs.inputnode.bvals = bvals_file
    nipype_bedpostx.inputs.xfibres.n_fibres = 2
    nipype_bedpostx.inputs.xfibres.fudge = 1
    nipype_bedpostx.inputs.xfibres.burn_in = 1000
    nipype_bedpostx.inputs.xfibres.n_jumps = 1250
    nipype_bedpostx.inputs.xfibres.sample_every = 25

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        original_bedpostx = pe.Node(interface=fsl.BEDPOSTX(), name="original_bedpostx")
    original_bedpostx.inputs.dwi = dwi_file
    original_bedpostx.inputs.mask = mask_file
    original_bedpostx.inputs.bvecs = bvecs_file
    original_bedpostx.inputs.bvals = bvals_file
    original_bedpostx.inputs.environ['FSLPARALLEL'] = ""
    original_bedpostx.inputs.fibres = 2
    original_bedpostx.inputs.weight = 1
    original_bedpostx.inputs.burn_period = 1000
    original_bedpostx.inputs.jumps = 1250
    original_bedpostx.inputs.sampling = 25

    test_f1 = pe.Node(util.AssertEqual(), name="mean_f1_test")
    test_f2 = pe.Node(util.AssertEqual(), name="mean_f2_test")
    test_th1 = pe.Node(util.AssertEqual(), name="mean_th1_test")
    test_th2 = pe.Node(util.AssertEqual(), name="mean_th2_test")
    test_ph1 = pe.Node(util.AssertEqual(), name="mean_ph1_test")
    test_ph2 = pe.Node(util.AssertEqual(), name="mean_ph2_test")

    pipeline = pe.Workflow(name="test_bedpostx")
    pipeline.base_dir = tempfile.mkdtemp(prefix="nipype_test_bedpostx_")

    def pickFirst(l):
        return l[0]

    def pickSecond(l):
        return l[1]

    pipeline.connect([(nipype_bedpostx, test_f1, [(("outputnode.mean_fsamples", pickFirst), "volume1")]),
                      (nipype_bedpostx, test_f2, [(("outputnode.mean_fsamples", pickSecond), "volume1")]),
                      (nipype_bedpostx, test_th1, [(("outputnode.mean_thsamples", pickFirst), "volume1")]),
                      (nipype_bedpostx, test_th2, [(("outputnode.mean_thsamples", pickSecond), "volume1")]),
                      (nipype_bedpostx, test_ph1, [(("outputnode.mean_phsamples", pickFirst), "volume1")]),
                      (nipype_bedpostx, test_ph2, [(("outputnode.mean_phsamples", pickSecond), "volume1")]),

                      (original_bedpostx, test_f1, [(("mean_fsamples", pickFirst), "volume2")]),
                      (original_bedpostx, test_f2, [(("mean_fsamples", pickSecond), "volume2")]),
                      (original_bedpostx, test_th1, [(("mean_thsamples", pickFirst), "volume2")]),
                      (original_bedpostx, test_th2, [(("mean_thsamples", pickSecond), "volume2")]),
                      (original_bedpostx, test_ph1, [(("mean_phsamples", pickFirst), "volume2")]),
                      (original_bedpostx, test_ph2, [(("mean_phsamples", pickSecond), "volume2")])
                      ])

    pipeline.run(plugin='Linear')
    shutil.rmtree(pipeline.base_dir)
