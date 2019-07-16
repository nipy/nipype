# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..minc import BestLinReg


def test_BestLinReg_inputs():
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
        output_mnc=dict(
            argstr='%s',
            genfile=True,
            hash_files=False,
            keep_extension=False,
            name_source=['source'],
            name_template='%s_bestlinreg.mnc',
            position=-1,
            usedefault=True,
        ),
        output_xfm=dict(
            argstr='%s',
            genfile=True,
            hash_files=False,
            keep_extension=False,
            name_source=['source'],
            name_template='%s_bestlinreg.xfm',
            position=-2,
            usedefault=True,
        ),
        source=dict(
            argstr='%s',
            mandatory=True,
            position=-4,
            usedefault=True,
        ),
        target=dict(
            argstr='%s',
            mandatory=True,
            position=-3,
            usedefault=True,
        ),
        verbose=dict(argstr='-verbose', ),
    )
    inputs = BestLinReg.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_BestLinReg_outputs():
    output_map = dict(
        output_mnc=dict(usedefault=True, ),
        output_xfm=dict(usedefault=True, ),
    )
    outputs = BestLinReg.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
