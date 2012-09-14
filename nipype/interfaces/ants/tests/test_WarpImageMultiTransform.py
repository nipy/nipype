from nipype.interfaces.ants import *

baseDir = '/hjohnson/HDNI/20120828_ANTS_NIPYPE_TESTING'
imagedir = baseDir + "/ANTS_TEMPLATE_BUILD/run_dir/"

test = WarpImageMultiTransform()

test.inputs.dimension = 3
test.inputs.moving_image = baseDir + '/inputData/t1_average_BRAINSABC.nii.gz'
test.inputs.reference_image = baseDir + '/inputData/template_t1_clipped.nii.gz'
test.inputs.transformation_series = [baseDir + '/inputData/lmk_init.mat', baseDir + '/OutDirSimplified/template_t1_clipped_To_t1_average_BRAINSABC2Warp.nii.gz']
test.inputs.invert_affine = [1]

#'{0}MY02_T1_halfAffine.txt'.format(imagedir),
#result = test.run()
#print result.outputs

#target = baseDir + "/ANTS_TEMPLATE_BUILD/ANTS-Darwin-clang/bin/AverageAffineTransform 3 {0}01_T1_half.nii.gz 0.25 product2.nii.gz".format(imagedir)
#target = baseDir + "/ANTS_TEMPLATE_BUILD/ANTS-Darwin-clang/bin/AverageAffineTransform 3 {0}01_T1_half.nii.gz {0}02_T1_half.nii.gz product.nii.gz".format(imagedir)

print test.cmdline
print '++++++++++++++++'
#print target
#
#assert test.cmdline.strip() == target.strip()
