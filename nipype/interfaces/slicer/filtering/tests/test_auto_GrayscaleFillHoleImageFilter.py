# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from .....testing import assert_equal
from ..morphology import GrayscaleFillHoleImageFilter


def test_GrayscaleFillHoleImageFilter_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    inputVolume=dict(argstr='%s',
    position=-2,
    ),
    outputVolume=dict(argstr='%s',
    hash_files=False,
    position=-1,
    ),
    )
    inputs = GrayscaleFillHoleImageFilter._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_GrayscaleFillHoleImageFilter_outputs():
    output_map = dict(outputVolume=dict(position=-1,
    ),
    )
    outputs = GrayscaleFillHoleImageFilter._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
