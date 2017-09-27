# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..featuredetection import GenerateBrainClippedImage


def test_GenerateBrainClippedImage_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    inputImg=dict(argstr='--inputImg %s',
    ),
    inputMsk=dict(argstr='--inputMsk %s',
    ),
    numberOfThreads=dict(argstr='--numberOfThreads %d',
    ),
    outputFileName=dict(argstr='--outputFileName %s',
    hash_files=False,
    ),
    resource_monitor=dict(nohash=True,
    usedefault=True,
    ),
    terminal_output=dict(nohash=True,
    ),
    )
    inputs = GenerateBrainClippedImage.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_GenerateBrainClippedImage_outputs():
    output_map = dict(outputFileName=dict(),
    )
    outputs = GenerateBrainClippedImage.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
