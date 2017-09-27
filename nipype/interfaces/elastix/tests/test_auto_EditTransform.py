# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..utils import EditTransform


def test_EditTransform_inputs():
    input_map = dict(ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    interpolation=dict(argstr='FinalBSplineInterpolationOrder',
    usedefault=True,
    ),
    output_file=dict(),
    output_format=dict(argstr='ResultImageFormat',
    ),
    output_type=dict(argstr='ResultImagePixelType',
    ),
    reference_image=dict(),
    resource_monitor=dict(nohash=True,
    usedefault=True,
    ),
    transform_file=dict(mandatory=True,
    ),
    )
    inputs = EditTransform.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_EditTransform_outputs():
    output_map = dict(output_file=dict(),
    )
    outputs = EditTransform.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
