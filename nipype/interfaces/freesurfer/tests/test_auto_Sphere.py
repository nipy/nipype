# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..utils import Sphere


def test_Sphere_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        in_file=dict(
            argstr='%s',
            copyfile=True,
            mandatory=True,
            position=-2,
            usedefault=True,
        ),
        in_smoothwm=dict(
            copyfile=True,
            usedefault=True,
        ),
        magic=dict(argstr='-q', ),
        num_threads=dict(),
        out_file=dict(
            argstr='%s',
            hash_files=False,
            name_source=['in_file'],
            name_template='%s.sphere',
            position=-1,
            usedefault=True,
        ),
        seed=dict(argstr='-seed %d', ),
        subjects_dir=dict(usedefault=True, ),
    )
    inputs = Sphere.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_Sphere_outputs():
    output_map = dict(out_file=dict(usedefault=True, ), )
    outputs = Sphere.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
