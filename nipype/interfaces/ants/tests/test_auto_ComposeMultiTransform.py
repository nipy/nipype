# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..utils import ComposeMultiTransform


def test_ComposeMultiTransform_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        dimension=dict(
            argstr='%d',
            position=0,
            usedefault=True,
        ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        num_threads=dict(
            nohash=True,
            usedefault=True,
        ),
        output_transform=dict(
            argstr='%s',
            keep_extension=True,
            name_source=['transforms'],
            name_template='%s_composed',
            position=1,
            usedefault=True,
        ),
        reference_image=dict(
            argstr='%s',
            position=2,
            usedefault=True,
        ),
        transforms=dict(
            argstr='%s',
            mandatory=True,
            position=3,
        ),
    )
    inputs = ComposeMultiTransform.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_ComposeMultiTransform_outputs():
    output_map = dict(output_transform=dict(usedefault=True, ), )
    outputs = ComposeMultiTransform.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
