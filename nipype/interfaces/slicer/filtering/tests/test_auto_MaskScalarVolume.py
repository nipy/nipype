# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..arithmetic import MaskScalarVolume


def test_MaskScalarVolume_inputs():
    input_map = dict(
        InputVolume=dict(
            argstr='%s',
            extensions=None,
            position=-3,
        ),
        MaskVolume=dict(
            argstr='%s',
            extensions=None,
            position=-2,
        ),
        OutputVolume=dict(
            argstr='%s',
            hash_files=False,
            position=-1,
        ),
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        label=dict(argstr='--label %d', ),
        replace=dict(argstr='--replace %d', ),
    )
    inputs = MaskScalarVolume.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_MaskScalarVolume_outputs():
    output_map = dict(
        OutputVolume=dict(
            extensions=None,
            position=-1,
        ), )
    outputs = MaskScalarVolume.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
