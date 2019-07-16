# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..preprocess import SkullStrip


def test_SkullStrip_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        in_file=dict(
            argstr='-input %s',
            copyfile=False,
            mandatory=True,
            position=1,
            usedefault=True,
        ),
        num_threads=dict(
            nohash=True,
            usedefault=True,
        ),
        out_file=dict(
            argstr='-prefix %s',
            name_source='in_file',
            name_template='%s_skullstrip',
            usedefault=True,
        ),
        outputtype=dict(),
    )
    inputs = SkullStrip.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_SkullStrip_outputs():
    output_map = dict(out_file=dict(usedefault=True, ), )
    outputs = SkullStrip.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
