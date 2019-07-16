# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..registration import ComposeXfm


def test_ComposeXfm_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        in_aff=dict(
            argstr='-aff %s',
            mandatory=True,
            usedefault=True,
        ),
        in_df=dict(
            argstr='-df %s',
            mandatory=True,
            usedefault=True,
        ),
        out_file=dict(
            argstr='-out %s',
            genfile=True,
            usedefault=True,
        ),
    )
    inputs = ComposeXfm.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_ComposeXfm_outputs():
    output_map = dict(out_file=dict(usedefault=True, ), )
    outputs = ComposeXfm.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
