# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..utils import Mesh2PVE


def test_Mesh2PVE_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    in_file=dict(argstr='%s',
    mandatory=True,
    position=-3,
    ),
    in_first=dict(argstr='-first %s',
    ),
    out_file=dict(argstr='%s',
    mandatory=True,
    position=-1,
    usedefault=True,
    ),
    reference=dict(argstr='%s',
    mandatory=True,
    position=-2,
    ),
    )
    inputs = Mesh2PVE._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_Mesh2PVE_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = Mesh2PVE._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
