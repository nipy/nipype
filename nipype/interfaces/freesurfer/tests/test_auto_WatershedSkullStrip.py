# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..preprocess import WatershedSkullStrip


def test_WatershedSkullStrip_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        brain_atlas=dict(
            argstr='-brain_atlas %s',
            position=-4,
            usedefault=True,
        ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        in_file=dict(
            argstr='%s',
            mandatory=True,
            position=-2,
            usedefault=True,
        ),
        out_file=dict(
            argstr='%s',
            mandatory=True,
            position=-1,
            usedefault=True,
        ),
        subjects_dir=dict(usedefault=True, ),
        t1=dict(argstr='-T1', ),
        transform=dict(
            argstr='%s',
            position=-3,
            usedefault=True,
        ),
    )
    inputs = WatershedSkullStrip.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_WatershedSkullStrip_outputs():
    output_map = dict(out_file=dict(usedefault=True, ), )
    outputs = WatershedSkullStrip.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
