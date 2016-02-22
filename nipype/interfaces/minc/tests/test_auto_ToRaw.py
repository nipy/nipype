# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..minc import ToRaw


def test_ToRaw_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    input_file=dict(argstr='%s',
    mandatory=True,
    position=-2,
    ),
    nonormalize=dict(argstr='-nonormalize',
    xor=('normalize', 'nonormalize'),
    ),
    normalize=dict(argstr='-normalize',
    xor=('normalize', 'nonormalize'),
    ),
    out_file=dict(argstr='> %s',
    position=-1,
    usedefault=True,
    ),
    output_file=dict(hash_files=False,
    keep_extension=False,
    name_source=['input_file'],
    name_template='%s.raw',
    position=-1,
    ),
    write_byte=dict(argstr='-byte',
    xor=('write_byte', 'write_short', 'write_int', 'write_long', 'write_float', 'write_double'),
    ),
    write_double=dict(argstr='-double',
    xor=('write_byte', 'write_short', 'write_int', 'write_long', 'write_float', 'write_double'),
    ),
    write_float=dict(argstr='-float',
    xor=('write_byte', 'write_short', 'write_int', 'write_long', 'write_float', 'write_double'),
    ),
    write_int=dict(argstr='-int',
    xor=('write_byte', 'write_short', 'write_int', 'write_long', 'write_float', 'write_double'),
    ),
    write_long=dict(argstr='-long',
    xor=('write_byte', 'write_short', 'write_int', 'write_long', 'write_float', 'write_double'),
    ),
    write_range=dict(argstr='-range %s %s',
    ),
    write_short=dict(argstr='-short',
    xor=('write_byte', 'write_short', 'write_int', 'write_long', 'write_float', 'write_double'),
    ),
    write_signed=dict(argstr='-signed',
    xor=('write_signed', 'write_unsigned'),
    ),
    write_unsigned=dict(argstr='-unsigned',
    xor=('write_signed', 'write_unsigned'),
    ),
    )
    inputs = ToRaw._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_ToRaw_outputs():
    output_map = dict(output_file=dict(),
    )
    outputs = ToRaw._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
