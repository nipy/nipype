# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..misc import Distance


def test_Distance_inputs():
    input_map = dict(
        mask_volume=dict(usedefault=True, ),
        method=dict(usedefault=True, ),
        volume1=dict(
            mandatory=True,
            usedefault=True,
        ),
        volume2=dict(
            mandatory=True,
            usedefault=True,
        ),
    )
    inputs = Distance.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_Distance_outputs():
    output_map = dict(
        distance=dict(),
        histogram=dict(usedefault=True, ),
        point1=dict(),
        point2=dict(),
    )
    outputs = Distance.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
