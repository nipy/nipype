# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..model import SphericalAverage


def test_SphericalAverage_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        erode=dict(argstr='-erode %d', ),
        fname=dict(
            argstr='%s',
            mandatory=True,
            position=-5,
        ),
        hemisphere=dict(
            argstr='%s',
            mandatory=True,
            position=-4,
        ),
        in_average=dict(
            argstr='%s',
            genfile=True,
            position=-2,
        ),
        in_orig=dict(
            argstr='-orig %s',
            usedefault=True,
        ),
        in_surf=dict(
            argstr='%s',
            mandatory=True,
            position=-3,
            usedefault=True,
        ),
        out_file=dict(
            argstr='%s',
            genfile=True,
            position=-1,
            usedefault=True,
        ),
        subject_id=dict(
            argstr='-o %s',
            mandatory=True,
        ),
        subjects_dir=dict(usedefault=True, ),
        threshold=dict(argstr='-t %.1f', ),
        which=dict(
            argstr='%s',
            mandatory=True,
            position=-6,
        ),
    )
    inputs = SphericalAverage.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_SphericalAverage_outputs():
    output_map = dict(out_file=dict(usedefault=True, ), )
    outputs = SphericalAverage.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
