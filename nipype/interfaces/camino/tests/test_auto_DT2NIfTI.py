# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..convert import DT2NIfTI


def test_DT2NIfTI_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        header_file=dict(
            argstr='-header %s',
            mandatory=True,
            position=3,
            usedefault=True,
        ),
        in_file=dict(
            argstr='-inputfile %s',
            mandatory=True,
            position=1,
            usedefault=True,
        ),
        output_root=dict(
            argstr='-outputroot %s',
            genfile=True,
            position=2,
            usedefault=True,
        ),
    )
    inputs = DT2NIfTI.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_DT2NIfTI_outputs():
    output_map = dict(
        dt=dict(usedefault=True, ),
        exitcode=dict(usedefault=True, ),
        lns0=dict(usedefault=True, ),
    )
    outputs = DT2NIfTI.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
