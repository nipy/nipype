# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from .....testing import assert_equal
from ..brains import BRAINSLmkTransform


def test_BRAINSLmkTransform_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    inputFixedLandmarks=dict(argstr='--inputFixedLandmarks %s',
    ),
    inputMovingLandmarks=dict(argstr='--inputMovingLandmarks %s',
    ),
    inputMovingVolume=dict(argstr='--inputMovingVolume %s',
    ),
    inputReferenceVolume=dict(argstr='--inputReferenceVolume %s',
    ),
    numberOfThreads=dict(argstr='--numberOfThreads %d',
    ),
    outputAffineTransform=dict(argstr='--outputAffineTransform %s',
    hash_files=False,
    ),
    outputResampledVolume=dict(argstr='--outputResampledVolume %s',
    hash_files=False,
    ),
    )
    inputs = BRAINSLmkTransform._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_BRAINSLmkTransform_outputs():
    output_map = dict(outputAffineTransform=dict(),
    outputResampledVolume=dict(),
    )
    outputs = BRAINSLmkTransform._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
