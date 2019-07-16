# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..diffusion import dtiaverage


def test_dtiaverage_inputs():
    input_map = dict(
        DTI_double=dict(argstr='--DTI_double ', ),
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        inputs=dict(argstr='--inputs %s...', ),
        tensor_output=dict(
            argstr='--tensor_output %s',
            hash_files=False,
        ),
        verbose=dict(argstr='--verbose ', ),
    )
    inputs = dtiaverage.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_dtiaverage_outputs():
    output_map = dict(tensor_output=dict(usedefault=True, ), )
    outputs = dtiaverage.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
