# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..preprocess import Maskave


def test_Maskave_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        in_file=dict(
            argstr='%s',
            copyfile=False,
            mandatory=True,
            position=-2,
            usedefault=True,
        ),
        mask=dict(
            argstr='-mask %s',
            position=1,
            usedefault=True,
        ),
        num_threads=dict(
            nohash=True,
            usedefault=True,
        ),
        out_file=dict(
            argstr='> %s',
            keep_extension=True,
            name_source='in_file',
            name_template='%s_maskave.1D',
            position=-1,
            usedefault=True,
        ),
        outputtype=dict(),
        quiet=dict(
            argstr='-quiet',
            position=2,
        ),
    )
    inputs = Maskave.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_Maskave_outputs():
    output_map = dict(out_file=dict(usedefault=True, ), )
    outputs = Maskave.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
