import os

from nose import with_setup

from nipype.testing import (skipif)
import nipype.workflows.fsl as fsl_wf
import nipype.interfaces.fsl as fsl
import nipype.interfaces.utility as util
from nipype.interfaces.fsl import no_fsl, no_fsl_course_data

import nipype.pipeline.engine as pe
from nipype.testing.utils import setup_test_dir,\
    remove_test_dir
import warnings

global test_dir

@skipif(no_fsl)
@skipif(no_fsl_course_data)
@with_setup(setup_test_dir, remove_test_dir)
def test_create_eddy_correct_pipeline():
    fsl_course_dir = os.environ["FSL_COURSE_DATA"]

    dwi_file = os.path.join(fsl_course_dir, "fsl_course_data/fdt/subj1/data.nii.gz")

    nipype_eddycorrect = fsl_wf.create_eddy_correct_pipeline("nipype_eddycorrect")
    nipype_eddycorrect.inputs.inputnode.in_file = dwi_file
    nipype_eddycorrect.inputs.inputnode.ref_num = 0

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        original_eddycorrect = pe.Node(interface = fsl.EddyCorrect(), name="original_eddycorrect")
    original_eddycorrect.inputs.in_file = dwi_file
    original_eddycorrect.inputs.ref_num = 0

    test = pe.Node(util.AssertEqual(), name="eddy_corrected_dwi_test")

    pipeline = pe.Workflow(name="test_eddycorrect")
    pipeline.base_dir = test_dir

    pipeline.connect([(nipype_eddycorrect, test, [("outputnode.eddy_corrected", "inputnode.volume1")]),
                      (original_eddycorrect, test, [("eddy_corrected", "inputnode.volume2")]),
                      ])

    pipeline.run(inseries=True)

@skipif(no_fsl)
@skipif(no_fsl_course_data)
@with_setup(setup_test_dir, remove_test_dir)
def test_create_bedpostx_pipeline():
    fsl_course_dir = os.environ["FSL_COURSE_DATA"]

    mask_file = os.path.join(fsl_course_dir, "fsl_course_data/fdt/subj1.bedpostX/nodif_brain_mask.nii.gz")
    bvecs_file = os.path.join(fsl_course_dir, "fsl_course_data/fdt/subj1/bvecs")
    bvals_file = os.path.join(fsl_course_dir, "fsl_course_data/fdt/subj1/bvals")
    dwi_file = os.path.join(fsl_course_dir, "fsl_course_data/fdt/subj1/data.nii.gz")

    nipype_bedpostx = fsl_wf.create_bedpostx_pipeline("nipype_bedpostx")
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
        original_bedpostx = pe.Node(interface = fsl.BEDPOSTX(), name="original_bedpostx")
    original_bedpostx.inputs.dwi = dwi_file
    original_bedpostx.inputs.mask = mask_file
    original_bedpostx.inputs.bvecs = bvecs_file
    original_bedpostx.inputs.bvals = bvals_file
    original_bedpostx.inputs.environ['FSLPARALLEL']=""
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
    pipeline.base_dir = test_dir

    def pickFirst(l):
        return l[0]

    def pickSecond(l):
        return l[1]

    pipeline.connect([(nipype_bedpostx, test_f1, [(("outputnode.mean_fsamples", pickFirst), "inputnode.volume1")]),
                      (nipype_bedpostx, test_f2, [(("outputnode.mean_fsamples", pickSecond), "inputnode.volume1")]),
                      (nipype_bedpostx, test_th1, [(("outputnode.mean_thsamples", pickFirst), "inputnode.volume1")]),
                      (nipype_bedpostx, test_th2, [(("outputnode.mean_thsamples", pickSecond), "inputnode.volume1")]),
                      (nipype_bedpostx, test_ph1, [(("outputnode.mean_phsamples", pickFirst), "inputnode.volume1")]),
                      (nipype_bedpostx, test_ph2, [(("outputnode.mean_phsamples", pickSecond), "inputnode.volume1")]),

                      (original_bedpostx, test_f1, [(("mean_fsamples", pickFirst), "inputnode.volume2")]),
                      (original_bedpostx, test_f2, [(("mean_fsamples", pickSecond), "inputnode.volume2")]),
                      (original_bedpostx, test_th1, [(("mean_thsamples", pickFirst), "inputnode.volume2")]),
                      (original_bedpostx, test_th2, [(("mean_thsamples", pickSecond), "inputnode.volume2")]),
                      (original_bedpostx, test_ph1, [(("mean_phsamples", pickFirst), "inputnode.volume2")]),
                      (original_bedpostx, test_ph2, [(("mean_phsamples", pickSecond), "inputnode.volume2")])
                      ])

    pipeline.run(inseries=True)