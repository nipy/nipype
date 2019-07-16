# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..minc import Gennlxfm


def test_Gennlxfm_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        clobber=dict(
            argstr='-clobber',
            usedefault=True,
        ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        ident=dict(argstr='-ident', ),
        like=dict(
            argstr='-like %s',
            usedefault=True,
        ),
        output_file=dict(
            argstr='%s',
            genfile=True,
            hash_files=False,
            name_source=['like'],
            name_template='%s_gennlxfm.xfm',
            position=-1,
            usedefault=True,
        ),
        step=dict(argstr='-step %s', ),
        verbose=dict(argstr='-verbose', ),
    )
    inputs = Gennlxfm.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_Gennlxfm_outputs():
    output_map = dict(
        output_file=dict(usedefault=True, ),
        output_grid=dict(usedefault=True, ),
    )
    outputs = Gennlxfm.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
