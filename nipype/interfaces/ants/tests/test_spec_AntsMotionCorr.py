# -*- coding: utf-8 -*-
from __future__ import division
from nipype.interfaces.ants.preprocess import AntsMotionCorr

def test_AntsMotionCorr_cmd():
    ants_mc = AntsMotionCorr()
    ants_mc.inputs.metric_type = 'GC'
    ants_mc.inputs.metric_weight = 1
    ants_mc.inputs.radius_or_bins = 1
    ants_mc.inputs.sampling_strategy = "Random"
    ants_mc.inputs.sampling_percentage = 0.05
    ants_mc.inputs.iterations = [10, 3]
    ants_mc.inputs.smoothing_sigmas = [0, 0]
    ants_mc.inputs.shrink_factors = [1, 1]
    ants_mc.inputs.n_images = 10
    ants_mc.inputs.use_fixed_reference_image = True
    ants_mc.inputs.use_scales_estimator = True
    ants_mc.inputs.output_average_image = 'wat'
    ants_mc.inputs.output_warped_image = 'warped.nii.gz'
    ants_mc.inputs.output_transform_prefix = 'motcorr'
    ants_mc.inputs.transformation_model = 'Affine'
    ants_mc.inputs.gradient_step_length = 0.005
    ants_mc.inputs.fixed_image = "average_image.nii.gz"
    ants_mc.inputs.moving_image = "input.nii.gz"

    expected_command = (
        "antsMotionCorr -d 3 -i 10x3 -m GC[average_image.nii.gz,input.nii.gz,1.0,1,Random,0.05] "
        "-n 10 -o [motcorr,warped.nii.gz,average_image.nii.gz] -f 1x1 -s 0.0x0.0 -t Affine[0.005] "
        "-u 1 -e 1"
    )
    assert ants_mc.cmdline == expected_command
