from nipype.interfaces.ants import *

baseDir = '/hjohnson/HDNI/20120828_ANTS_NIPYPE_TESTING'
at = ApplyTransforms()
at.inputs.dimension = 3
at.inputs.input_image = baseDir + '/inputData/t1_average_BRAINSABC.nii.gz'
at.inputs.reference_image = baseDir + '/inputData/template_t1_clipped.nii.gz'
at.inputs.interpolation = 'Linear'
at.inputs.default_value = 0
at.inputs.transformation_files = [baseDir + '/inputData/lmk_init.mat', baseDir + '/OutDirSimplified/template_t1_clipped_To_t1_average_BRAINSABC2Warp.nii.gz']

print at.cmdline
print "--dimensionality 3    --input SUBJ_B_T1_resampled.nii.gz    --reference-image SUBJ_A_T1_resampled.nii.gz    --output antsResampleBtoA.nii.gz    --interpolation Linear    --default-value 0    --transform 20120430_1348_ANTS6_1Warp.nii.gz    --transform 20120430_1348_txfmv2fv_affine.mat"

#res = at.run()
#print res.outputs
