# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..preprocess import CARegister


def test_CARegister_inputs():
    input_map = dict(
        A=dict(argstr='-A %d', ),
        align=dict(argstr='-align-%s', ),
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        in_file=dict(
            argstr='%s',
            mandatory=True,
            position=-3,
            usedefault=True,
        ),
        invert_and_save=dict(
            argstr='-invert-and-save',
            position=-4,
        ),
        l_files=dict(argstr='-l %s', ),
        levels=dict(argstr='-levels %d', ),
        mask=dict(
            argstr='-mask %s',
            usedefault=True,
        ),
        no_big_ventricles=dict(argstr='-nobigventricles', ),
        num_threads=dict(),
        out_file=dict(
            argstr='%s',
            genfile=True,
            position=-1,
            usedefault=True,
        ),
        subjects_dir=dict(usedefault=True, ),
        template=dict(
            argstr='%s',
            position=-2,
            usedefault=True,
        ),
        transform=dict(
            argstr='-T %s',
            usedefault=True,
        ),
    )
    inputs = CARegister.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_CARegister_outputs():
    output_map = dict(out_file=dict(), )
    outputs = CARegister.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
