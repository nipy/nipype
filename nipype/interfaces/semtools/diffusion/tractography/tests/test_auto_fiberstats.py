# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..commandlineonly import fiberstats


def test_fiberstats_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        fiber_file=dict(
            argstr='--fiber_file %s',
            usedefault=True,
        ),
        verbose=dict(argstr='--verbose ', ),
    )
    inputs = fiberstats.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_fiberstats_outputs():
    output_map = dict()
    outputs = fiberstats.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
