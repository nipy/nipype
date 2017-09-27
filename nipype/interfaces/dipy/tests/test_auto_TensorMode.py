# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..tensors import TensorMode


def test_TensorMode_inputs():
    input_map = dict(b0_thres=dict(usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    in_bval=dict(mandatory=True,
    ),
    in_bvec=dict(mandatory=True,
    ),
    in_file=dict(mandatory=True,
    ),
    mask_file=dict(),
    out_prefix=dict(),
    resource_monitor=dict(nohash=True,
    usedefault=True,
    ),
    )
    inputs = TensorMode.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_TensorMode_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = TensorMode.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
