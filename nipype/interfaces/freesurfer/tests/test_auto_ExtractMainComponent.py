# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..utils import ExtractMainComponent


def test_ExtractMainComponent_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    in_file=dict(argstr='%s',
    mandatory=True,
    position=1,
    ),
    out_file=dict(argstr='%s',
    name_source='in_file',
    name_template='%s.maincmp',
    position=2,
    ),
    )
    inputs = ExtractMainComponent._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_ExtractMainComponent_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = ExtractMainComponent._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
