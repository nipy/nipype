from nipype.interfaces.fsl.dti import EddyCorrect, create_eddycorrect_pipeline
import nipype.pipeline.engine as pe

fsl_course_dir = "/media/data/fsl_course"
working_dir = "/media/data/eddycorrect_test"

dwi_file = fsl_course_dir + "fsl_course_data/fdt/subj1/data.nii.gz"


nipype_eddycorrect = create_eddycorrect_pipeline("nipype_eddycorrect")
nipype_eddycorrect.inputs.inputnode.in_file = dwi_file
nipype_eddycorrect.inputs.inputnode.ref_num = 0

original_eddycorrect = pe.Node(interface = EddyCorrect(), name="original_eddycorrect")
nipype_eddycorrect.inputs.in_file = dwi_file
nipype_eddycorrect.inputs.ref_num = 0

pipeline = pe.Workflow(name="test_eddycorrect")
pipeline.add_nodes([nipype_eddycorrect, original_eddycorrect])

pipeline.run(inseries=True)