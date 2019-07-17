# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..gtract import gtractFastMarchingTracking


def test_gtractFastMarchingTracking_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        costStepSize=dict(argstr='--costStepSize %f', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        inputAnisotropyVolume=dict(
            argstr='--inputAnisotropyVolume %s',
            extensions=None,
        ),
        inputCostVolume=dict(
            argstr='--inputCostVolume %s',
            extensions=None,
        ),
        inputStartingSeedsLabelMapVolume=dict(
            argstr='--inputStartingSeedsLabelMapVolume %s',
            extensions=None,
        ),
        inputTensorVolume=dict(
            argstr='--inputTensorVolume %s',
            extensions=None,
        ),
        maximumStepSize=dict(argstr='--maximumStepSize %f', ),
        minimumStepSize=dict(argstr='--minimumStepSize %f', ),
        numberOfIterations=dict(argstr='--numberOfIterations %d', ),
        numberOfThreads=dict(argstr='--numberOfThreads %d', ),
        outputTract=dict(
            argstr='--outputTract %s',
            hash_files=False,
        ),
        seedThreshold=dict(argstr='--seedThreshold %f', ),
        startingSeedsLabel=dict(argstr='--startingSeedsLabel %d', ),
        trackingThreshold=dict(argstr='--trackingThreshold %f', ),
        writeXMLPolyDataFile=dict(argstr='--writeXMLPolyDataFile ', ),
    )
    inputs = gtractFastMarchingTracking.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_gtractFastMarchingTracking_outputs():
    output_map = dict(outputTract=dict(extensions=None, ), )
    outputs = gtractFastMarchingTracking.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
