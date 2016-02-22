# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from .....testing import assert_equal
from ..denoising import GaussianBlurImageFilter


def test_GaussianBlurImageFilter_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    inputVolume=dict(argstr='%s',
    position=-2,
    ),
    outputVolume=dict(argstr='%s',
    hash_files=False,
    position=-1,
    ),
    sigma=dict(argstr='--sigma %f',
    ),
    )
    inputs = GaussianBlurImageFilter._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_GaussianBlurImageFilter_outputs():
    output_map = dict(outputVolume=dict(position=-1,
    ),
    )
    outputs = GaussianBlurImageFilter._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
