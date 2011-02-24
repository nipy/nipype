from nipype.interfaces.fsl.dti import EddyCorrect, create_eddycorrect_pipeline
import nipype.pipeline.engine as pe
import os
from nipype.interfaces.fsl.maths import BinaryMaths
from nipype.interfaces.fsl.utils import ImageStats
from nipype.interfaces.utility import IdentityInterface

fsl_course_dir = "/media/data/fsl_course"
working_dir = "/media/data/eddycorrect_test"

dwi_file = os.path.join(fsl_course_dir, "fsl_course_data/fdt/subj1/data.nii.gz")


nipype_eddycorrect = create_eddycorrect_pipeline("nipype_eddycorrect")
nipype_eddycorrect.inputs.inputnode.in_file = dwi_file
nipype_eddycorrect.inputs.inputnode.ref_num = 0

original_eddycorrect = pe.Node(interface = EddyCorrect(), name="original_eddycorrect")
original_eddycorrect.inputs.in_file = dwi_file
original_eddycorrect.inputs.ref_num = 0

difference = pe.Node(interface=BinaryMaths(operation="sub"), name="difference")

mean = pe.Node(interface=ImageStats(op_string="-m"), name="mean")

test = pe.Node(interface=IdentityInterface(fields=["mean"]), name="test")

def assert_zero(val):
    assert val == 0

pipeline = pe.Workflow(name="test_eddycorrect")
pipeline.base_dir = working_dir

pipeline.connect([(nipype_eddycorrect, difference, [("merge.merged_file", "in_file")]),
                  (original_eddycorrect, difference, [("eddy_corrected", "operand_file")]),
                  (difference, mean, [("out_file", "in_file")]),
                  (mean, test, [(("out_stat", assert_zero), "mean")])
                  ])

pipeline.run(inseries=True)