# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from nipype.testing import assert_equal
from nipype.interfaces.mrtrix.tracking import StreamlineTrack
def test_StreamlineTrack_inputs():
    input_map = dict(do_not_precompute=dict(argstr='-noprecomputed',
    ),
    maximum_number_of_tracks=dict(argstr='-maxnum %d',
    ),
    exclude_file=dict(position=2,
    argstr='-exclude %s',
    ),
    cutoff_value=dict(units='NA',
    argstr='-cutoff %s',
    ),
    seed_file=dict(position=2,
    argstr='-seed %s',
    ),
    step_size=dict(units='mm',
    argstr='-step %s',
    ),
    in_file=dict(position=-2,
    mandatory=True,
    argstr='%s',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    no_mask_interpolation=dict(argstr='-nomaskinterp',
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    include_file=dict(position=2,
    argstr='-include %s',
    ),
    maximum_tract_length=dict(units='mm',
    argstr='-length %s',
    ),
    args=dict(argstr='%s',
    ),
    stop=dict(argstr='-gzip',
    ),
    minimum_radius_of_curvature=dict(units='mm',
    argstr='-curvature %s',
    ),
    inputmodel=dict(position=-3,
    usedefault=True,
    argstr='%s',
    ),
    initial_direction=dict(units='voxels',
    argstr='-initdirection %s',
    ),
    exclude_spec=dict(sep=',',
    units='mm',
    position=2,
    argstr='-seed %s',
    ),
    desired_number_of_tracks=dict(argstr='-number %d',
    ),
    seed_spec=dict(sep=',',
    units='mm',
    position=2,
    argstr='-seed %s',
    ),
    initial_cutoff_value=dict(units='NA',
    argstr='-initcutoff %s',
    ),
    minimum_tract_length=dict(units='mm',
    argstr='-minlength %s',
    ),
    mask_spec=dict(sep=',',
    units='mm',
    position=2,
    argstr='-seed %s',
    ),
    out_file=dict(position=-1,
    genfile=True,
    argstr='%s',
    ),
    include_spec=dict(sep=',',
    units='mm',
    position=2,
    argstr='-seed %s',
    ),
    terminal_output=dict(mandatory=True,
    nohash=True,
    ),
    unidirectional=dict(argstr='-unidirectional',
    ),
    mask_file=dict(position=2,
    argstr='-exclude %s',
    ),
    )
    inputs = StreamlineTrack.input_spec()

    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(inputs.traits()[key], metakey), value
def test_StreamlineTrack_outputs():
    output_map = dict(tracked=dict(),
    )
    outputs = StreamlineTrack.output_spec()

    for key, metadata in output_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
