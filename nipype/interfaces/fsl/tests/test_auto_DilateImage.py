# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..maths import DilateImage


def test_DilateImage_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    in_file=dict(argstr='%s',
    mandatory=True,
    position=2,
    ),
    internal_datatype=dict(argstr='-dt %s',
    position=1,
    ),
    kernel_file=dict(argstr='%s',
    position=5,
    xor=['kernel_size'],
    ),
    kernel_shape=dict(argstr='-kernel %s',
    position=4,
    ),
    kernel_size=dict(argstr='%.4f',
    position=5,
    xor=['kernel_file'],
    ),
    nan2zeros=dict(argstr='-nan',
    position=3,
    ),
    operation=dict(argstr='-dil%s',
    mandatory=True,
    position=6,
    ),
    out_file=dict(argstr='%s',
    genfile=True,
    hash_files=False,
    position=-2,
    ),
    output_datatype=dict(argstr='-odt %s',
    position=-1,
    ),
    output_type=dict(),
    resource_monitor=dict(nohash=True,
    usedefault=True,
    ),
    terminal_output=dict(nohash=True,
    ),
    )
    inputs = DilateImage.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_DilateImage_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = DilateImage.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
