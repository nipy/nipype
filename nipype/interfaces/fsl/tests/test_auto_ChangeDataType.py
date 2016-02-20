# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..maths import ChangeDataType


def test_ChangeDataType_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    in_file=dict(argstr='%s',
    mandatory=True,
    position=2,
    ),
    internal_datatype=dict(argstr='-dt %s',
    position=1,
    ),
    nan2zeros=dict(argstr='-nan',
    position=3,
    usedefault=True,
    ),
    out_file=dict(argstr='%s',
    hash_files=False,
    position=-2,
    ),
    output_datatype=dict(argstr='-odt %s',
    mandatory=True,
    position=-1,
    ),
    output_type=dict(usedefault=True,
    ),
    terminal_output=dict(nohash=True,
    ),
    )
    inputs = ChangeDataType.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_ChangeDataType_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = ChangeDataType.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
