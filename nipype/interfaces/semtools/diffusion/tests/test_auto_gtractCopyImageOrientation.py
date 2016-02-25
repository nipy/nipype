# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from .....testing import assert_equal
from ..gtract import gtractCopyImageOrientation


def test_gtractCopyImageOrientation_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    inputReferenceVolume=dict(argstr='--inputReferenceVolume %s',
    ),
    inputVolume=dict(argstr='--inputVolume %s',
    ),
    numberOfThreads=dict(argstr='--numberOfThreads %d',
    ),
    outputVolume=dict(argstr='--outputVolume %s',
    hash_files=False,
    ),
    )
    inputs = gtractCopyImageOrientation._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_gtractCopyImageOrientation_outputs():
    output_map = dict(outputVolume=dict(),
    )
    outputs = gtractCopyImageOrientation._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
