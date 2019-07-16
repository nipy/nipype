# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..maths import MathsCommand


def test_MathsCommand_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        in_file=dict(
            argstr='%s',
            mandatory=True,
            position=2,
            usedefault=True,
        ),
        out_file=dict(
            argstr='%s',
            name_source=['in_file'],
            name_template='%s',
            position=-2,
            usedefault=True,
        ),
        output_datatype=dict(
            argstr='-odt %s',
            position=-3,
        ),
    )
    inputs = MathsCommand.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_MathsCommand_outputs():
    output_map = dict(out_file=dict(usedefault=True, ), )
    outputs = MathsCommand.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
