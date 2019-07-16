# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..featuredetection import HammerAttributeCreator


def test_HammerAttributeCreator_inputs():
    input_map = dict(
        Scale=dict(argstr='--Scale %d', ),
        Strength=dict(argstr='--Strength %f', ),
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        inputCSFVolume=dict(
            argstr='--inputCSFVolume %s',
            usedefault=True,
        ),
        inputGMVolume=dict(
            argstr='--inputGMVolume %s',
            usedefault=True,
        ),
        inputWMVolume=dict(
            argstr='--inputWMVolume %s',
            usedefault=True,
        ),
        outputVolumeBase=dict(argstr='--outputVolumeBase %s', ),
    )
    inputs = HammerAttributeCreator.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_HammerAttributeCreator_outputs():
    output_map = dict()
    outputs = HammerAttributeCreator.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
