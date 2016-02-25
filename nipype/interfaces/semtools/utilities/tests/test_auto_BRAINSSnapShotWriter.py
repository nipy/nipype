# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from .....testing import assert_equal
from ..brains import BRAINSSnapShotWriter


def test_BRAINSSnapShotWriter_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    inputBinaryVolumes=dict(argstr='--inputBinaryVolumes %s...',
    ),
    inputPlaneDirection=dict(argstr='--inputPlaneDirection %s',
    sep=',',
    ),
    inputSliceToExtractInIndex=dict(argstr='--inputSliceToExtractInIndex %s',
    sep=',',
    ),
    inputSliceToExtractInPercent=dict(argstr='--inputSliceToExtractInPercent %s',
    sep=',',
    ),
    inputSliceToExtractInPhysicalPoint=dict(argstr='--inputSliceToExtractInPhysicalPoint %s',
    sep=',',
    ),
    inputVolumes=dict(argstr='--inputVolumes %s...',
    ),
    outputFilename=dict(argstr='--outputFilename %s',
    hash_files=False,
    ),
    )
    inputs = BRAINSSnapShotWriter._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_BRAINSSnapShotWriter_outputs():
    output_map = dict(outputFilename=dict(),
    )
    outputs = BRAINSSnapShotWriter._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
