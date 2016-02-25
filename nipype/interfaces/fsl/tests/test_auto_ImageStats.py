# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..utils import ImageStats


def test_ImageStats_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    in_file=dict(argstr='%s',
    mandatory=True,
    position=2,
    ),
    mask_file=dict(argstr='-k %s',
    ),
    op_string=dict(argstr='%s',
    mandatory=True,
    position=3,
    ),
    output_type=dict(usedefault=True,
    ),
    split_4d=dict(argstr='-t',
    position=1,
    ),
    )
    inputs = ImageStats._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_ImageStats_outputs():
    output_map = dict(out_stat=dict(),
    )
    outputs = ImageStats._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
