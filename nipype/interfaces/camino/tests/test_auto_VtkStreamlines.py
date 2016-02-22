# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..convert import VtkStreamlines


def test_VtkStreamlines_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    colourorient=dict(argstr='-colourorient',
    ),
    in_file=dict(argstr=' < %s',
    mandatory=True,
    position=-2,
    ),
    inputmodel=dict(argstr='-inputmodel %s',
    usedefault=True,
    ),
    interpolate=dict(argstr='-interpolate',
    ),
    interpolatescalars=dict(argstr='-interpolatescalars',
    ),
    out_file=dict(argstr='> %s',
    position=-1,
    usedefault=True,
    ),
    scalar_file=dict(argstr='-scalarfile %s',
    position=3,
    ),
    seed_file=dict(argstr='-seedfile %s',
    position=1,
    ),
    target_file=dict(argstr='-targetfile %s',
    position=2,
    ),
    voxeldims=dict(argstr='-voxeldims %s',
    position=4,
    units='mm',
    ),
    )
    inputs = VtkStreamlines._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_VtkStreamlines_outputs():
    output_map = dict(vtk=dict(),
    )
    outputs = VtkStreamlines._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
