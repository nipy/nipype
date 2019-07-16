# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..utils import TVResampleTask


def test_TVResampleTask_inputs():
    input_map = dict(
        align=dict(argstr='-align %s', ),
        args=dict(argstr='%s', ),
        array_size=dict(
            argstr='-size %d %d %d',
            xor=['target_file'],
        ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        in_file=dict(
            argstr='-in %s',
            mandatory=True,
            usedefault=True,
        ),
        interpolation=dict(argstr='-interp %s', ),
        origin=dict(
            argstr='-origin %g %g %g',
            xor=['target_file'],
        ),
        out_file=dict(
            argstr='-out %s',
            keep_extension=True,
            name_source='in_file',
            name_template='%s_resampled',
            usedefault=True,
        ),
        target_file=dict(
            argstr='-target %s',
            usedefault=True,
            xor=['array_size', 'voxel_size', 'origin'],
        ),
        voxel_size=dict(
            argstr='-vsize %g %g %g',
            xor=['target_file'],
        ),
    )
    inputs = TVResampleTask.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_TVResampleTask_outputs():
    output_map = dict(out_file=dict(usedefault=True, ), )
    outputs = TVResampleTask.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
