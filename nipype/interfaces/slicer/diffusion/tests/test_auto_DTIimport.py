# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from .....testing import assert_equal
from ..diffusion import DTIimport


def test_DTIimport_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    inputFile=dict(argstr='%s',
    position=-2,
    ),
    outputTensor=dict(argstr='%s',
    hash_files=False,
    position=-1,
    ),
    testingmode=dict(argstr='--testingmode ',
    ),
    )
    inputs = DTIimport._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_DTIimport_outputs():
    output_map = dict(outputTensor=dict(position=-1,
    ),
    )
    outputs = DTIimport._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
