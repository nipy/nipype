# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..registration import ExpertAutomatedRegistration


def test_ExpertAutomatedRegistration_inputs():
    input_map = dict(
        affineMaxIterations=dict(argstr='--affineMaxIterations %d', ),
        affineSamplingRatio=dict(argstr='--affineSamplingRatio %f', ),
        args=dict(argstr='%s', ),
        bsplineMaxIterations=dict(argstr='--bsplineMaxIterations %d', ),
        bsplineSamplingRatio=dict(argstr='--bsplineSamplingRatio %f', ),
        controlPointSpacing=dict(argstr='--controlPointSpacing %d', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        expectedOffset=dict(argstr='--expectedOffset %f', ),
        expectedRotation=dict(argstr='--expectedRotation %f', ),
        expectedScale=dict(argstr='--expectedScale %f', ),
        expectedSkew=dict(argstr='--expectedSkew %f', ),
        fixedImage=dict(
            argstr='%s',
            position=-2,
            usedefault=True,
        ),
        fixedImageMask=dict(
            argstr='--fixedImageMask %s',
            usedefault=True,
        ),
        fixedLandmarks=dict(argstr='--fixedLandmarks %s...', ),
        initialization=dict(argstr='--initialization %s', ),
        interpolation=dict(argstr='--interpolation %s', ),
        loadTransform=dict(
            argstr='--loadTransform %s',
            usedefault=True,
        ),
        metric=dict(argstr='--metric %s', ),
        minimizeMemory=dict(argstr='--minimizeMemory ', ),
        movingImage=dict(
            argstr='%s',
            position=-1,
            usedefault=True,
        ),
        movingLandmarks=dict(argstr='--movingLandmarks %s...', ),
        numberOfThreads=dict(argstr='--numberOfThreads %d', ),
        randomNumberSeed=dict(argstr='--randomNumberSeed %d', ),
        registration=dict(argstr='--registration %s', ),
        resampledImage=dict(
            argstr='--resampledImage %s',
            hash_files=False,
        ),
        rigidMaxIterations=dict(argstr='--rigidMaxIterations %d', ),
        rigidSamplingRatio=dict(argstr='--rigidSamplingRatio %f', ),
        sampleFromOverlap=dict(argstr='--sampleFromOverlap ', ),
        saveTransform=dict(
            argstr='--saveTransform %s',
            hash_files=False,
        ),
        verbosityLevel=dict(argstr='--verbosityLevel %s', ),
    )
    inputs = ExpertAutomatedRegistration.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_ExpertAutomatedRegistration_outputs():
    output_map = dict(
        resampledImage=dict(usedefault=True, ),
        saveTransform=dict(usedefault=True, ),
    )
    outputs = ExpertAutomatedRegistration.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
