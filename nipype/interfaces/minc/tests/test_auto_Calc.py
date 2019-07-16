# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..minc import Calc


def test_Calc_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        check_dimensions=dict(
            argstr='-check_dimensions',
            xor=('check_dimensions', 'no_check_dimensions'),
        ),
        clobber=dict(
            argstr='-clobber',
            usedefault=True,
        ),
        copy_header=dict(
            argstr='-copy_header',
            xor=('copy_header', 'no_copy_header'),
        ),
        debug=dict(argstr='-debug', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        eval_width=dict(argstr='-eval_width %s', ),
        expfile=dict(
            argstr='-expfile %s',
            mandatory=True,
            xor=('expression', 'expfile'),
        ),
        expression=dict(
            argstr="-expression '%s'",
            mandatory=True,
            xor=('expression', 'expfile'),
        ),
        filelist=dict(
            argstr='-filelist %s',
            mandatory=True,
            xor=('input_files', 'filelist'),
        ),
        format_byte=dict(
            argstr='-byte',
            xor=('format_filetype', 'format_byte', 'format_short',
                 'format_int', 'format_long', 'format_float', 'format_double',
                 'format_signed', 'format_unsigned'),
        ),
        format_double=dict(
            argstr='-double',
            xor=('format_filetype', 'format_byte', 'format_short',
                 'format_int', 'format_long', 'format_float', 'format_double',
                 'format_signed', 'format_unsigned'),
        ),
        format_filetype=dict(
            argstr='-filetype',
            xor=('format_filetype', 'format_byte', 'format_short',
                 'format_int', 'format_long', 'format_float', 'format_double',
                 'format_signed', 'format_unsigned'),
        ),
        format_float=dict(
            argstr='-float',
            xor=('format_filetype', 'format_byte', 'format_short',
                 'format_int', 'format_long', 'format_float', 'format_double',
                 'format_signed', 'format_unsigned'),
        ),
        format_int=dict(
            argstr='-int',
            xor=('format_filetype', 'format_byte', 'format_short',
                 'format_int', 'format_long', 'format_float', 'format_double',
                 'format_signed', 'format_unsigned'),
        ),
        format_long=dict(
            argstr='-long',
            xor=('format_filetype', 'format_byte', 'format_short',
                 'format_int', 'format_long', 'format_float', 'format_double',
                 'format_signed', 'format_unsigned'),
        ),
        format_short=dict(
            argstr='-short',
            xor=('format_filetype', 'format_byte', 'format_short',
                 'format_int', 'format_long', 'format_float', 'format_double',
                 'format_signed', 'format_unsigned'),
        ),
        format_signed=dict(
            argstr='-signed',
            xor=('format_filetype', 'format_byte', 'format_short',
                 'format_int', 'format_long', 'format_float', 'format_double',
                 'format_signed', 'format_unsigned'),
        ),
        format_unsigned=dict(
            argstr='-unsigned',
            xor=('format_filetype', 'format_byte', 'format_short',
                 'format_int', 'format_long', 'format_float', 'format_double',
                 'format_signed', 'format_unsigned'),
        ),
        ignore_nan=dict(argstr='-ignore_nan', ),
        input_files=dict(
            argstr='%s',
            mandatory=True,
            position=-2,
            sep=' ',
        ),
        max_buffer_size_in_kb=dict(argstr='-max_buffer_size_in_kb %d', ),
        no_check_dimensions=dict(
            argstr='-nocheck_dimensions',
            xor=('check_dimensions', 'no_check_dimensions'),
        ),
        no_copy_header=dict(
            argstr='-nocopy_header',
            xor=('copy_header', 'no_copy_header'),
        ),
        outfiles=dict(),
        output_file=dict(
            argstr='%s',
            genfile=True,
            hash_files=False,
            name_source=['input_files'],
            name_template='%s_calc.mnc',
            position=-1,
        ),
        output_illegal=dict(
            argstr='-illegal_value',
            xor=('output_nan', 'output_zero', 'output_illegal_value'),
        ),
        output_nan=dict(
            argstr='-nan',
            xor=('output_nan', 'output_zero', 'output_illegal_value'),
        ),
        output_zero=dict(
            argstr='-zero',
            xor=('output_nan', 'output_zero', 'output_illegal_value'),
        ),
        propagate_nan=dict(argstr='-propagate_nan', ),
        quiet=dict(
            argstr='-quiet',
            xor=('verbose', 'quiet'),
        ),
        two=dict(argstr='-2', ),
        verbose=dict(
            argstr='-verbose',
            xor=('verbose', 'quiet'),
        ),
        voxel_range=dict(argstr='-range %d %d', ),
    )
    inputs = Calc.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_Calc_outputs():
    output_map = dict(output_file=dict(), )
    outputs = Calc.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
