# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..utils import MRIsCalc


def test_MRIsCalc_inputs():
    input_map = dict(
        action=dict(
            argstr='%s',
            mandatory=True,
            position=-2,
        ),
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        in_file1=dict(
            argstr='%s',
            mandatory=True,
            position=-3,
            usedefault=True,
        ),
        in_file2=dict(
            argstr='%s',
            position=-1,
            usedefault=True,
            xor=['in_float', 'in_int'],
        ),
        in_float=dict(
            argstr='%f',
            position=-1,
            xor=['in_file2', 'in_int'],
        ),
        in_int=dict(
            argstr='%d',
            position=-1,
            xor=['in_file2', 'in_float'],
        ),
        out_file=dict(
            argstr='-o %s',
            mandatory=True,
            usedefault=True,
        ),
        subjects_dir=dict(usedefault=True, ),
    )
    inputs = MRIsCalc.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_MRIsCalc_outputs():
    output_map = dict(out_file=dict(usedefault=True, ), )
    outputs = MRIsCalc.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
