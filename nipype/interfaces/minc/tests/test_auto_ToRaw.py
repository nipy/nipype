# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..minc import ToRaw


def test_ToRaw_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    input_file=dict(argstr='%s',
    mandatory=True,
    position=-2,
    ),
    nonormalize=dict(argstr='-nonormalize',
    xor=(u'normalize', u'nonormalize'),
    ),
    normalize=dict(argstr='-normalize',
    xor=(u'normalize', u'nonormalize'),
    ),
    out_file=dict(argstr='> %s',
    genfile=True,
    position=-1,
    ),
    output_file=dict(hash_files=False,
    keep_extension=False,
    name_source=[u'input_file'],
    name_template='%s.raw',
    position=-1,
    ),
    terminal_output=dict(nohash=True,
    ),
    write_byte=dict(argstr='-byte',
    xor=(u'write_byte', u'write_short', u'write_int', u'write_long', u'write_float', u'write_double'),
    ),
    write_double=dict(argstr='-double',
    xor=(u'write_byte', u'write_short', u'write_int', u'write_long', u'write_float', u'write_double'),
    ),
    write_float=dict(argstr='-float',
    xor=(u'write_byte', u'write_short', u'write_int', u'write_long', u'write_float', u'write_double'),
    ),
    write_int=dict(argstr='-int',
    xor=(u'write_byte', u'write_short', u'write_int', u'write_long', u'write_float', u'write_double'),
    ),
    write_long=dict(argstr='-long',
    xor=(u'write_byte', u'write_short', u'write_int', u'write_long', u'write_float', u'write_double'),
    ),
    write_range=dict(argstr='-range %s %s',
    ),
    write_short=dict(argstr='-short',
    xor=(u'write_byte', u'write_short', u'write_int', u'write_long', u'write_float', u'write_double'),
    ),
    write_signed=dict(argstr='-signed',
    xor=(u'write_signed', u'write_unsigned'),
    ),
    write_unsigned=dict(argstr='-unsigned',
    xor=(u'write_signed', u'write_unsigned'),
    ),
    )
    inputs = ToRaw.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_ToRaw_outputs():
    output_map = dict(output_file=dict(),
    )
    outputs = ToRaw.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
