# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..utils import SwapDimensions


def test_SwapDimensions_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    in_file=dict(argstr='%s',
    mandatory=True,
    position=1,
    ),
    new_dims=dict(argstr='%s %s %s',
    mandatory=True,
    ),
    out_file=dict(argstr='%s',
    hash_files=False,
    ),
    output_type=dict(usedefault=True,
    ),
    )
    inputs = SwapDimensions._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_SwapDimensions_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = SwapDimensions._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
