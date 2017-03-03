# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..preprocess import AntsMotionCorr


def test_AntsMotionCorr_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    average_image=dict(argstr='-a %s',
    position=1,
    ),
    dimensionality=dict(argstr='-d %d',
    position=0,
    usedefault=True,
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    fixed_image=dict(requires=['metric_type'],
    ),
    gradient_step_length=dict(requires=['transformation_model'],
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    iterations=dict(argstr='-i %d',
    sep='x',
    ),
    metric_type=dict(argstr='%s',
    ),
    metric_weight=dict(requires=['metric_type'],
    ),
    moving_image=dict(requires=['metric_type'],
    ),
    n_images=dict(argstr='-n %d',
    ),
    num_threads=dict(nohash=True,
    usedefault=True,
    ),
    output_average_image=dict(argstr='%s',
    genfile=True,
    hash_files=False,
    ),
    output_transform_prefix=dict(),
    output_warped_image=dict(),
    radius_or_bins=dict(requires=['metric_type'],
    ),
    sampling_percentage=dict(requires=['metric_type'],
    ),
    sampling_strategy=dict(requires=['metric_type'],
    ),
    shrink_factors=dict(argstr='-f %d',
    sep='x',
    ),
    smoothing_sigmas=dict(argstr='-s %f',
    sep='x',
    ),
    terminal_output=dict(nohash=True,
    ),
    transformation_model=dict(argstr='%s',
    ),
    use_estimate_learning_rate_once=dict(argstr='-l %d',
    ),
    use_fixed_reference_image=dict(argstr='-u %d',
    ),
    use_scales_estimator=dict(argstr='-e %d',
    ),
    write_displacement=dict(argstr='-w %d',
    ),
    )
    inputs = AntsMotionCorr.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_AntsMotionCorr_outputs():
    output_map = dict(average_image=dict(),
    composite_transform=dict(),
    displacement_field=dict(),
    inverse_composite_transform=dict(),
    inverse_warped_image=dict(),
    save_state=dict(),
    warped_image=dict(),
    )
    outputs = AntsMotionCorr.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
