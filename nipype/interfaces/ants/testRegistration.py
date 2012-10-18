from nipype.interfaces.ants.registration import Registration
reg = Registration()
reg.inputs.fixed_image = ['fixed1.nii', 'fixed2.nii']
reg.inputs.moving_image = ['moving1.nii', 'moving2.nii']
reg.inputs.output_transform_prefix = "t1_average_BRAINSABC_To_template_t1_clipped"
reg.inputs.initial_moving_transform = 'trans.mat'
reg.inputs.transforms = ['Affine', 'SyN']
reg.inputs.transform_parameters = [(2.0,), (0.25, 3.0, 0.0)]
reg.inputs.number_of_iterations = [[1500, 200], [100, 50, 30]]
reg.inputs.dimension = 3
reg.inputs.write_composite_transform = True
reg.inputs.metric = ['Mattes']*2
reg.inputs.metric_weight = [1]*2 # Default (value ignored currently by ANTs)
reg.inputs.radius_or_number_of_bins = [32]*2
reg.inputs.sampling_strategy = ['Random', None]
reg.inputs.sampling_percentage = [0.05, None]
reg.inputs.convergence_threshold = [1.e-8, 1.e-9]
reg.inputs.convergence_window_size = [20]*2
reg.inputs.smoothing_sigmas = [[1,0], [2,1,0]]
reg.inputs.shrink_factors = [[2,1], [3,2,1]]
reg.inputs.use_estimate_learning_rate_once = [True, True]
reg.inputs.use_histogram_matching = [True, True] # This is the default
reg.inputs.output_warped_image = 't1_average_BRAINSABC_To_template_t1_clipped_INTERNAL_WARPED.nii.gz'
reg.inputs.winsorize_lower_quantile = 0.025
reg.inputs.winsorize_upper_quantile = 0.975
reg.inputs.collapse_linear_transforms_to_fixed_image_header = False
print reg.cmdline