# from nipype import config, logging
# config.enable_debug_mode()
# logging.update_logging(config)
from nipype.interfaces.ants import *

baseDir='/hjohnson/HDNI/20120828_ANTS_NIPYPE_TESTING'
imagedir = baseDir + "/ANTS_TEMPLATE_BUILD/run_dir/"

test = AverageAffineTransform()

test.inputs.dimension = 3
test.inputs.transforms = [baseDir + '/inputData/lmk_init.mat',baseDir + '/inputData/lmk_init.mat',baseDir + '/inputData/lmk_init.mat']
test.inputs.output_affine_transform = 'MYtemplatewarp.mat'

result = test.run()
print result.outputs

target = baseDir + "/ANTS_TEMPLATE_BUILD/ANTS-Darwin-clang/bin/AverageAffineTransform 3 {0}01_T1_half.nii.gz 0.25 product2.nii.gz".format(imagedir)
#target = baseDir + "/ANTS_TEMPLATE_BUILD/ANTS-Darwin-clang/bin/AverageAffineTransform 3 {0}01_T1_half.nii.gz {0}02_T1_half.nii.gz product.nii.gz".format(imagedir)

print test.cmdline
print '++++++++++++++++'
print target

#assert test.cmdline.strip() == target.strip()
