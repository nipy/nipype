# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..convert import Shredder


def test_Shredder_inputs():
    input_map = dict(
        args=dict(
            argstr="%s",
        ),
        chunksize=dict(
            argstr="%d",
            position=2,
            units="NA",
        ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        in_file=dict(
            argstr="< %s",
            extensions=None,
            mandatory=True,
            position=-2,
        ),
        offset=dict(
            argstr="%d",
            position=1,
            units="NA",
        ),
        out_file=dict(
            argstr="> %s",
            extensions=None,
            genfile=True,
            position=-1,
        ),
        space=dict(
            argstr="%d",
            position=3,
            units="NA",
        ),
    )
    inputs = Shredder.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_Shredder_outputs():
    output_map = dict(
        shredded=dict(
            extensions=None,
        ),
    )
    outputs = Shredder.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
