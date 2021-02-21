# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..utils import CheckTalairachAlignment


def test_CheckTalairachAlignment_inputs():
    input_map = dict(
        args=dict(
            argstr="%s",
        ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        in_file=dict(
            argstr="-xfm %s",
            extensions=None,
            mandatory=True,
            position=-1,
            xor=["subject"],
        ),
        subject=dict(
            argstr="-subj %s",
            mandatory=True,
            position=-1,
            xor=["in_file"],
        ),
        subjects_dir=dict(),
        threshold=dict(
            argstr="-T %.3f",
            usedefault=True,
        ),
    )
    inputs = CheckTalairachAlignment.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_CheckTalairachAlignment_outputs():
    output_map = dict(
        out_file=dict(
            extensions=None,
        ),
    )
    outputs = CheckTalairachAlignment.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
