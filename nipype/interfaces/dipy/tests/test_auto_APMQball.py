# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..anisotropic_power import APMQball


def test_APMQball_inputs():
    input_map = dict(
        b0_thres=dict(usedefault=True, ),
        in_bval=dict(
            mandatory=True,
            usedefault=True,
        ),
        in_bvec=dict(
            mandatory=True,
            usedefault=True,
        ),
        in_file=dict(
            mandatory=True,
            usedefault=True,
        ),
        mask_file=dict(usedefault=True, ),
        out_prefix=dict(),
    )
    inputs = APMQball.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_APMQball_outputs():
    output_map = dict(out_file=dict(usedefault=True, ), )
    outputs = APMQball.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
