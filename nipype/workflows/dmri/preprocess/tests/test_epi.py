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
from nipype.workflows.dmri.preprocess.epi import eddy_correct


#@skipif(no_fsl)
#@skipif(no_fsl_course_data)
#def test_eddy_correct():
#    fsl_course_dir = os.path.abspath('fsl_course_data')
#    dwi_file = os.path.join(fsl_course_dir, "fdt/subj1/data.nii.gz")
#    bval_file = os.path.join(fsl_course_dir, "fdt/subj1/bval.txt")
#
#    ecc = eddy_correct()
#    ecc.inputs.inputnode.in_file = dwi_file
#    ecc.inputs.inputnode.in_bval = bval_file
#
#    with warnings.catch_warnings():
#        warnings.simplefilter("ignore")
#        original_eddycorrect = pe.Node(interface=fsl.EddyCorrect(), name="original_eddycorrect")
#    original_eddycorrect.inputs.in_file = dwi_file
#    original_eddycorrect.inputs.ref_num = 0
#
#    test = pe.Node(util.AssertEqual(), name="eddy_corrected_dwi_test")
#
#    pipeline = pe.Workflow(name="test_eddycorrect")
#    pipeline.base_dir = tempfile.mkdtemp(prefix="nipype_test_eddycorrect_")
#
#    pipeline.connect([(nipype_eddycorrect, test, [("outputnode.eddy_corrected", "volume1")]),
#                      (original_eddycorrect, test, [("eddy_corrected", "volume2")]),
#                      ])
#
#    pipeline.run(plugin='Linear')
#    shutil.rmtree(pipeline.base_dir)

