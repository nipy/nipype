# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..registration import ANTS


def test_ANTS_inputs():
    input_map = dict(
        affine_gradient_descent_option=dict(argstr="%s",),
        args=dict(argstr="%s",),
        delta_time=dict(requires=["number_of_time_steps"],),
        dimension=dict(argstr="%d", position=1,),
        environ=dict(nohash=True, usedefault=True,),
        fixed_image=dict(mandatory=True,),
        gradient_step_length=dict(requires=["transformation_model"],),
        metric=dict(mandatory=True,),
        metric_weight=dict(mandatory=True, requires=["metric"], usedefault=True,),
        mi_option=dict(argstr="--MI-option %s", sep="x",),
        moving_image=dict(argstr="%s", mandatory=True,),
        num_threads=dict(nohash=True, usedefault=True,),
        number_of_affine_iterations=dict(
            argstr="--number-of-affine-iterations %s", sep="x",
        ),
        number_of_iterations=dict(argstr="--number-of-iterations %s", sep="x",),
        number_of_time_steps=dict(requires=["gradient_step_length"],),
        output_transform_prefix=dict(
            argstr="--output-naming %s", mandatory=True, usedefault=True,
        ),
        radius=dict(mandatory=True, requires=["metric"],),
        regularization=dict(argstr="%s",),
        regularization_deformation_field_sigma=dict(requires=["regularization"],),
        regularization_gradient_field_sigma=dict(requires=["regularization"],),
        smoothing_sigmas=dict(argstr="--gaussian-smoothing-sigmas %s", sep="x",),
        subsampling_factors=dict(argstr="--subsampling-factors %s", sep="x",),
        symmetry_type=dict(requires=["delta_time"],),
        transformation_model=dict(argstr="%s", mandatory=True,),
        use_histogram_matching=dict(argstr="%s", usedefault=True,),
    )
    inputs = ANTS.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_ANTS_outputs():
    output_map = dict(
        affine_transform=dict(extensions=None,),
        inverse_warp_transform=dict(extensions=None,),
        metaheader=dict(extensions=None,),
        metaheader_raw=dict(extensions=None,),
        warp_transform=dict(extensions=None,),
    )
    outputs = ANTS.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
