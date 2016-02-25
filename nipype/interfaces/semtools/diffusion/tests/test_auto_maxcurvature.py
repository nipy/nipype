# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from .....testing import assert_equal
from ..maxcurvature import maxcurvature


def test_maxcurvature_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    image=dict(argstr='--image %s',
    ),
    output=dict(argstr='--output %s',
    hash_files=False,
    ),
    sigma=dict(argstr='--sigma %f',
    ),
    verbose=dict(argstr='--verbose ',
    ),
    )
    inputs = maxcurvature._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_maxcurvature_outputs():
    output_map = dict(output=dict(),
    )
    outputs = maxcurvature._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
