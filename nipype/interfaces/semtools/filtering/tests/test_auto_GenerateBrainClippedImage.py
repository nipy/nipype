# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..featuredetection import GenerateBrainClippedImage


def test_GenerateBrainClippedImage_inputs():
    input_map = dict(
        args=dict(argstr="%s",),
        environ=dict(nohash=True, usedefault=True,),
        inputImg=dict(argstr="--inputImg %s", extensions=None,),
        inputMsk=dict(argstr="--inputMsk %s", extensions=None,),
        numberOfThreads=dict(argstr="--numberOfThreads %d",),
        outputFileName=dict(argstr="--outputFileName %s", hash_files=False,),
    )
    inputs = GenerateBrainClippedImage.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_GenerateBrainClippedImage_outputs():
    output_map = dict(outputFileName=dict(extensions=None,),)
    outputs = GenerateBrainClippedImage.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
