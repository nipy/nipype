# from nipype import config, logging
# config.enable_debug_mode()
# logging.update_logging(config)

from nipype.interfaces.ants import *

baseDir = '/hjohnson/HDNI/20120828_ANTS_NIPYPE_TESTING'

imagedir = baseDir + "/ANTS_TEMPLATE_BUILD/run_dir/"

test = AverageImages()
test.inputs.dimension = 3
test.inputs.average_image = "/tmp/average.nii.gz"
test.inputs.normalize = 1
test.inputs.images = [baseDir + '/inputData/t1_average_BRAINSABC.nii.gz',baseDir + '/inputData/t1_average_BRAINSABC.nii.gz',baseDir + '/inputData/t1_average_BRAINSABC.nii.gz']

result = test.run()
print result.outputs

target = baseDir + "/ANTS_TEMPLATE_BUILD/ANTS-Darwin-clang/bin/AverageImages 3 average.nii.gz 1 {0}01_T1_half.nii.gz {0}02_T1_half.nii.gz {0}03_T1_half.nii.gz".format(imagedir)

#print test.cmdline
#print '++++++++++++++++'
#print target

#assert test.cmdline.strip() == target.strip()
