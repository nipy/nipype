# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from .....testing import assert_equal
from ..gtract import gtractResampleAnisotropy


def test_gtractResampleAnisotropy_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    inputAnatomicalVolume=dict(argstr='--inputAnatomicalVolume %s',
    ),
    inputAnisotropyVolume=dict(argstr='--inputAnisotropyVolume %s',
    ),
    inputTransform=dict(argstr='--inputTransform %s',
    ),
    numberOfThreads=dict(argstr='--numberOfThreads %d',
    ),
    outputVolume=dict(argstr='--outputVolume %s',
    hash_files=False,
    ),
    transformType=dict(argstr='--transformType %s',
    ),
    )
    inputs = gtractResampleAnisotropy._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_gtractResampleAnisotropy_outputs():
    output_map = dict(outputVolume=dict(),
    )
    outputs = gtractResampleAnisotropy._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
