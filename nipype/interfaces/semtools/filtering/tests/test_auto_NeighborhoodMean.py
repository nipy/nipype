# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..featuredetection import NeighborhoodMean


def test_NeighborhoodMean_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    inputMaskVolume=dict(argstr='--inputMaskVolume %s',
    ),
    inputRadius=dict(argstr='--inputRadius %d',
    ),
    inputVolume=dict(argstr='--inputVolume %s',
    ),
    outputVolume=dict(argstr='--outputVolume %s',
    hash_files=False,
    ),
    resource_monitor=dict(nohash=True,
    usedefault=True,
    ),
    terminal_output=dict(nohash=True,
    ),
    )
    inputs = NeighborhoodMean.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_NeighborhoodMean_outputs():
    output_map = dict(outputVolume=dict(),
    )
    outputs = NeighborhoodMean.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
