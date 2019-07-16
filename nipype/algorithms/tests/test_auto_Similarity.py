# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..metrics import Similarity


def test_Similarity_inputs():
    input_map = dict(
        mask1=dict(usedefault=True, ),
        mask2=dict(usedefault=True, ),
        metric=dict(usedefault=True, ),
        volume1=dict(
            mandatory=True,
            usedefault=True,
        ),
        volume2=dict(
            mandatory=True,
            usedefault=True,
        ),
    )
    inputs = Similarity.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_Similarity_outputs():
    output_map = dict(similarity=dict(), )
    outputs = Similarity.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
