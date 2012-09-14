#!/usr/bin/env python
# from nipype import config
# config.enable_debug_mode()

from nipype.interfaces.ants import *

baseDir = '/hjohnson/HDNI'
test = antsRegistration()
test.inputs.fixed_image = [baseDir + '/20120828_ANTS_NIPYPE_TESTING/inputData/t1_average_BRAINSABC_clipped.nii.gz']*2
test.inputs.moving_image = [baseDir + '/20120828_ANTS_NIPYPE_TESTING/inputData/template_t1_clipped.nii.gz']*2
test.inputs.output_transform_prefix = "t1_average_BRAINSABC_To_template_t1_clipped"
test.inputs.initial_moving_transform = baseDir + '/20120828_ANTS_NIPYPE_TESTING/inputData/lmk_init.mat'
test.inputs.transforms = ['Affine', 'SyN']
test.inputs.transform_parameters = [(2.0,), (0.25, 3.0, 0.0)]
test.inputs.number_of_iterations = [[1500, 200], [100, 50, 30]]
test.inputs.dimension = 3
test.inputs.write_composite_transform = True
test.inputs.metric = ['Mattes']*2
test.inputs.metric_weight = [1]*2 # Default (value ignored currently by ANTs)
test.inputs.radius_or_number_of_bins = [32]*2
test.inputs.sampling_strategy = ['Random', None]
test.inputs.sampling_percentage = [0.05, None]
test.inputs.convergence_threshold = [1.e-8, 1.e-9]
test.inputs.convergence_window_size = [20]*2
test.inputs.smoothing_sigmas = [[1,0], [2,1,0]]
test.inputs.shrink_factors = [[2,1], [3,2,1]]
test.inputs.use_estimate_learning_rate_once = [True, True]
test.inputs.use_histogram_matching = [True, True] # This is the default
test.inputs.output_warped_image = 't1_average_BRAINSABC_To_template_t1_clipped_INTERNAL_WARPED.nii.gz'
#test.inputs.output_inverse_warped_image = True

# result = test.run()
# print result.outputs

target = 'antsRegistration --dimensionality 3 --initial-moving-transform [{0}/20120828_ANTS_NIPYPE_TESTING/inputData/lmk_init.mat,0] --output [t1_average_BRAINSABC_To_template_t1_clipped,t1_average_BRAINSABC_To_template_t1_clipped_INTERNAL_WARPED.nii.gz] --transform Affine[2.0] --metric Mattes[{0}/20120828_ANTS_NIPYPE_TESTING/inputData/t1_average_BRAINSABC_clipped.nii.gz,{0}/20120828_ANTS_NIPYPE_TESTING/inputData/template_t1_clipped.nii.gz,1,32,Random,0.05] --convergence [1500x200,1e-08,20] --smoothing-sigmas 1x0 --shrink-factors 2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[0.25,3.0,0.0] --metric Mattes[{0}/20120828_ANTS_NIPYPE_TESTING/inputData/t1_average_BRAINSABC_clipped.nii.gz,{0}/20120828_ANTS_NIPYPE_TESTING/inputData/template_t1_clipped.nii.gz,1,32] --convergence [100x50x30,1e-09,20] --smoothing-sigmas 2x1x0 --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 --write-composite-transform 1'.format(baseDir)

print test.cmdline
print ' test cmdline'
print '++++++++++++++++'
print '    target'
print target
print ''
assert test.cmdline.strip() == target.strip()
