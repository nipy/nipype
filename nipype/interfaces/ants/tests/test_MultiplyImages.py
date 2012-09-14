# from nipype import config, logging
# config.enable_debug_mode()
# logging.update_logging(config)
from nipype.interfaces.ants import *

baseDir = '/hjohnson/HDNI/20120828_ANTS_NIPYPE_TESTING'

test = MultiplyImages()
test.inputs.dimension = 3
test.inputs.first_input = baseDir + '/inputData/t1_average_BRAINSABC.nii.gz'
test.inputs.second_input = 0.25
test.inputs.output_product_image = "/tmp/product2.nii.gz"

result = test.run()
print result.outputs

#target = baseDir + "/ANTS_TEMPLATE_BUILD/ANTS-Darwin-clang/bin/MultiplyImages 3 {0}01_T1_half.nii.gz {0}02_T1_half.nii.gz product.nii.gz".format(imagedir)

print test.cmdline
print '++++++++++++++++'
#print target

#assert test.cmdline.strip() == target.strip()
