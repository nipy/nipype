# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..tracking import DiffusionTensorStreamlineTrack


def test_DiffusionTensorStreamlineTrack_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    cutoff_value=dict(argstr='-cutoff %s',
    units='NA',
    ),
    desired_number_of_tracks=dict(argstr='-number %d',
    ),
    do_not_precompute=dict(argstr='-noprecomputed',
    ),
    exclude_file=dict(argstr='-exclude %s',
    xor=['exclude_file', 'exclude_spec'],
    ),
    exclude_spec=dict(argstr='-exclude %s',
    position=2,
    sep=',',
    units='mm',
    xor=['exclude_file', 'exclude_spec'],
    ),
    gradient_encoding_file=dict(argstr='-grad %s',
    mandatory=True,
    position=-2,
    ),
    in_file=dict(argstr='%s',
    mandatory=True,
    position=-2,
    ),
    include_file=dict(argstr='-include %s',
    xor=['include_file', 'include_spec'],
    ),
    include_spec=dict(argstr='-include %s',
    position=2,
    sep=',',
    units='mm',
    xor=['include_file', 'include_spec'],
    ),
    initial_cutoff_value=dict(argstr='-initcutoff %s',
    units='NA',
    ),
    initial_direction=dict(argstr='-initdirection %s',
    units='voxels',
    ),
    inputmodel=dict(argstr='%s',
    position=-3,
    usedefault=True,
    ),
    mask_file=dict(argstr='-mask %s',
    xor=['mask_file', 'mask_spec'],
    ),
    mask_spec=dict(argstr='-mask %s',
    position=2,
    sep=',',
    units='mm',
    xor=['mask_file', 'mask_spec'],
    ),
    maximum_number_of_tracks=dict(argstr='-maxnum %d',
    ),
    maximum_tract_length=dict(argstr='-length %s',
    units='mm',
    ),
    minimum_radius_of_curvature=dict(argstr='-curvature %s',
    units='mm',
    ),
    minimum_tract_length=dict(argstr='-minlength %s',
    units='mm',
    ),
    no_mask_interpolation=dict(argstr='-nomaskinterp',
    ),
    out_file=dict(argstr='%s',
    name_source=['in_file'],
    name_template='%s_tracked.tck',
    output_name='tracked',
    position=-1,
    ),
    seed_file=dict(argstr='-seed %s',
    xor=['seed_file', 'seed_spec'],
    ),
    seed_spec=dict(argstr='-seed %s',
    position=2,
    sep=',',
    units='mm',
    xor=['seed_file', 'seed_spec'],
    ),
    step_size=dict(argstr='-step %s',
    units='mm',
    ),
    stop=dict(argstr='-stop',
    ),
    unidirectional=dict(argstr='-unidirectional',
    ),
    )
    inputs = DiffusionTensorStreamlineTrack._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_DiffusionTensorStreamlineTrack_outputs():
    output_map = dict(tracked=dict(),
    )
    outputs = DiffusionTensorStreamlineTrack._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
