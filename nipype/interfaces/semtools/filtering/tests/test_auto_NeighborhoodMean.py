# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from .....testing import assert_equal
from ..featuredetection import NeighborhoodMean


def test_NeighborhoodMean_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    inputMaskVolume=dict(argstr='--inputMaskVolume %s',
    ),
    inputRadius=dict(argstr='--inputRadius %d',
    ),
    inputVolume=dict(argstr='--inputVolume %s',
    ),
    outputVolume=dict(argstr='--outputVolume %s',
    hash_files=False,
    ),
    )
    inputs = NeighborhoodMean._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_NeighborhoodMean_outputs():
    output_map = dict(outputVolume=dict(),
    )
    outputs = NeighborhoodMean._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
