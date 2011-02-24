from nipype.interfaces.fsl.dti import BEDPOSTX, create_bedpostx_pipeline
import nipype.pipeline.engine as pe
import os

fsl_course_dir = "/media/data/fsl_course"
working_dir = "/media/data/bedpostx_test"

mask_file = os.path.join(fsl_course_dir, "fsl_course_data/fdt/subj1.bedpostX/nodif_brain_mask.nii.gz")
bvecs_file = os.path.join(fsl_course_dir, "fsl_course_data/fdt/subj1/bvecs")
bvals_file = os.path.join(fsl_course_dir, "fsl_course_data/fdt/subj1/bvals")
dwi_file = os.path.join(fsl_course_dir, "fsl_course_data/fdt/subj1/data.nii.gz")


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

original_bedpostx = pe.Node(interface = BEDPOSTX(), name="original_bedpostx")
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

pipeline = pe.Workflow(name="test_bedpostx")
pipeline.base_dir = working_dir
pipeline.add_nodes([nipype_bedpostx, original_bedpostx])

pipeline.run(inseries=True)