# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..specialized import BRAINSROIAuto


def test_BRAINSROIAuto_inputs():
    input_map = dict(
        ROIAutoDilateSize=dict(argstr='--ROIAutoDilateSize %f', ),
        args=dict(argstr='%s', ),
        closingSize=dict(argstr='--closingSize %f', ),
        cropOutput=dict(argstr='--cropOutput ', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        inputVolume=dict(
            argstr='--inputVolume %s',
            extensions=None,
        ),
        maskOutput=dict(argstr='--maskOutput ', ),
        numberOfThreads=dict(argstr='--numberOfThreads %d', ),
        otsuPercentileThreshold=dict(argstr='--otsuPercentileThreshold %f', ),
        outputROIMaskVolume=dict(
            argstr='--outputROIMaskVolume %s',
            hash_files=False,
        ),
        outputVolume=dict(
            argstr='--outputVolume %s',
            hash_files=False,
        ),
        outputVolumePixelType=dict(argstr='--outputVolumePixelType %s', ),
        thresholdCorrectionFactor=dict(
            argstr='--thresholdCorrectionFactor %f', ),
    )
    inputs = BRAINSROIAuto.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_BRAINSROIAuto_outputs():
    output_map = dict(
        outputROIMaskVolume=dict(extensions=None, ),
        outputVolume=dict(extensions=None, ),
    )
    outputs = BRAINSROIAuto.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
