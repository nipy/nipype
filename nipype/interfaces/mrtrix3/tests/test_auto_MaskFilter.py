# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..utils import MaskFilter


def test_MaskFilter_inputs():
    input_map = dict(
        args=dict(
            argstr="%s",
        ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        filter=dict(
            argstr="%s",
            mandatory=True,
            position=-2,
        ),
        in_file=dict(
            argstr="%s",
            extensions=None,
            mandatory=True,
            position=-3,
        ),
        npass=dict(
            argstr="-npass %d",
            position=1,
        ),
        out_file=dict(
            argstr="%s",
            extensions=None,
            mandatory=True,
            name_source=["input_image"],
            position=-1,
        ),
    )
    inputs = MaskFilter.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_MaskFilter_outputs():
    output_map = dict(
        out_file=dict(
            extensions=None,
        ),
    )
    outputs = MaskFilter.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
