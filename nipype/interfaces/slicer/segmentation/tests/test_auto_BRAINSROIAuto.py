# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from .....testing import assert_equal
from ..specialized import BRAINSROIAuto


def test_BRAINSROIAuto_inputs():
    input_map = dict(ROIAutoDilateSize=dict(argstr='--ROIAutoDilateSize %f',
    ),
    args=dict(argstr='%s',
    ),
    closingSize=dict(argstr='--closingSize %f',
    ),
    inputVolume=dict(argstr='--inputVolume %s',
    ),
    numberOfThreads=dict(argstr='--numberOfThreads %d',
    ),
    otsuPercentileThreshold=dict(argstr='--otsuPercentileThreshold %f',
    ),
    outputClippedVolumeROI=dict(argstr='--outputClippedVolumeROI %s',
    hash_files=False,
    ),
    outputROIMaskVolume=dict(argstr='--outputROIMaskVolume %s',
    hash_files=False,
    ),
    outputVolumePixelType=dict(argstr='--outputVolumePixelType %s',
    ),
    thresholdCorrectionFactor=dict(argstr='--thresholdCorrectionFactor %f',
    ),
    )
    inputs = BRAINSROIAuto._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_BRAINSROIAuto_outputs():
    output_map = dict(outputClippedVolumeROI=dict(),
    outputROIMaskVolume=dict(),
    )
    outputs = BRAINSROIAuto._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
