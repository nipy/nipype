# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..gtract import gtractImageConformity


def test_gtractImageConformity_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        inputReferenceVolume=dict(
            argstr='--inputReferenceVolume %s',
            usedefault=True,
        ),
        inputVolume=dict(
            argstr='--inputVolume %s',
            usedefault=True,
        ),
        numberOfThreads=dict(argstr='--numberOfThreads %d', ),
        outputVolume=dict(
            argstr='--outputVolume %s',
            hash_files=False,
        ),
    )
    inputs = gtractImageConformity.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_gtractImageConformity_outputs():
    output_map = dict(outputVolume=dict(usedefault=True, ), )
    outputs = gtractImageConformity.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
