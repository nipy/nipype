# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..dti import ComputeMeanDiffusivity


def test_ComputeMeanDiffusivity_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        in_file=dict(
            argstr='< %s',
            mandatory=True,
            position=1,
            usedefault=True,
        ),
        inputdatatype=dict(argstr='-inputdatatype %s', ),
        inputmodel=dict(argstr='-inputmodel %s', ),
        out_file=dict(
            argstr='> %s',
            genfile=True,
            position=-1,
            usedefault=True,
        ),
        outputdatatype=dict(argstr='-outputdatatype %s', ),
        scheme_file=dict(
            argstr='%s',
            position=2,
            usedefault=True,
        ),
    )
    inputs = ComputeMeanDiffusivity.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_ComputeMeanDiffusivity_outputs():
    output_map = dict(md=dict(usedefault=True, ), )
    outputs = ComputeMeanDiffusivity.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
