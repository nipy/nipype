# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from nipype.testing import assert_equal
from nipype.interfaces.fsl.utils import CopyGeom

def test_CopyGeom_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    dest_file=dict(argstr='%s',
    copyfile=True,
    mandatory=True,
    position=1,
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_dims=dict(argstr='-d',
    position='-1',
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    in_file=dict(argstr='%s',
    mandatory=True,
    position=0,
    ),
    output_type=dict(),
    terminal_output=dict(nohash=True,
    ),
    )
    inputs = CopyGeom.input_spec()

    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(inputs.traits()[key], metakey), value

def test_CopyGeom_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = CopyGeom.output_spec()

    for key, metadata in output_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(outputs.traits()[key], metakey), value

