# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..utils import SVAdjustVoxSp


def test_SVAdjustVoxSp_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        ignore_exception=dict(
            deprecated='1.0.0',
            nohash=True,
            usedefault=True,
        ),
        in_file=dict(
            argstr='-in %s',
            mandatory=True,
        ),
        origin=dict(
            argstr='-origin %g %g %g',
            xor=['target_file'],
        ),
        out_file=dict(
            argstr='-out %s',
            keep_extension=True,
            name_source='in_file',
            name_template='%s_avs',
        ),
        target_file=dict(
            argstr='-target %s',
            xor=['voxel_size', 'origin'],
        ),
        terminal_output=dict(
            deprecated='1.0.0',
            nohash=True,
        ),
        voxel_size=dict(
            argstr='-vsize %g %g %g',
            xor=['target_file'],
        ),
    )
    inputs = SVAdjustVoxSp.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_SVAdjustVoxSp_outputs():
    output_map = dict(out_file=dict(), )
    outputs = SVAdjustVoxSp.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
