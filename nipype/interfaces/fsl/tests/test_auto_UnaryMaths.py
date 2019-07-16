# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..maths import UnaryMaths


def test_UnaryMaths_inputs():
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
        internal_datatype=dict(
            argstr='-dt %s',
            position=1,
        ),
        nan2zeros=dict(
            argstr='-nan',
            position=3,
        ),
        operation=dict(
            argstr='-%s',
            mandatory=True,
            position=4,
        ),
        out_file=dict(
            argstr='%s',
            genfile=True,
            hash_files=False,
            position=-2,
            usedefault=True,
        ),
        output_datatype=dict(
            argstr='-odt %s',
            position=-1,
        ),
        output_type=dict(),
    )
    inputs = UnaryMaths.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_UnaryMaths_outputs():
    output_map = dict(out_file=dict(usedefault=True, ), )
    outputs = UnaryMaths.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
