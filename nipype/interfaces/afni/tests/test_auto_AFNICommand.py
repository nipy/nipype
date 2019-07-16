# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..base import AFNICommand


def test_AFNICommand_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        num_threads=dict(
            nohash=True,
            usedefault=True,
        ),
        outputtype=dict(),
    )
    inputs = AFNICommand.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
