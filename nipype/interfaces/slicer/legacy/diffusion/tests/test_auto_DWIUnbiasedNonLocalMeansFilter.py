# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..denoising import DWIUnbiasedNonLocalMeansFilter


def test_DWIUnbiasedNonLocalMeansFilter_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        hp=dict(argstr='--hp %f', ),
        inputVolume=dict(
            argstr='%s',
            position=-2,
            usedefault=True,
        ),
        ng=dict(argstr='--ng %d', ),
        outputVolume=dict(
            argstr='%s',
            hash_files=False,
            position=-1,
        ),
        rc=dict(
            argstr='--rc %s',
            sep=',',
        ),
        re=dict(
            argstr='--re %s',
            sep=',',
        ),
        rs=dict(
            argstr='--rs %s',
            sep=',',
        ),
    )
    inputs = DWIUnbiasedNonLocalMeansFilter.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_DWIUnbiasedNonLocalMeansFilter_outputs():
    output_map = dict(
        outputVolume=dict(
            position=-1,
            usedefault=True,
        ), )
    outputs = DWIUnbiasedNonLocalMeansFilter.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
