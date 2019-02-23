# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..minc import Average


def test_Average_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        avgdim=dict(argstr='-avgdim %s', ),
        binarize=dict(argstr='-binarize', ),
        binrange=dict(argstr='-binrange %s %s', ),
        binvalue=dict(argstr='-binvalue %s', ),
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
        input_files=dict(
            argstr='%s',
            mandatory=True,
            position=-2,
            sep=' ',
            xor=('input_files', 'filelist'),
        ),
        max_buffer_size_in_kb=dict(
            argstr='-max_buffer_size_in_kb %d',
            usedefault=True,
        ),
        no_check_dimensions=dict(
            argstr='-nocheck_dimensions',
            xor=('check_dimensions', 'no_check_dimensions'),
        ),
        no_copy_header=dict(
            argstr='-nocopy_header',
            xor=('copy_header', 'no_copy_header'),
        ),
        nonormalize=dict(
            argstr='-nonormalize',
            xor=('normalize', 'nonormalize'),
        ),
        normalize=dict(
            argstr='-normalize',
            xor=('normalize', 'nonormalize'),
        ),
        output_file=dict(
            argstr='%s',
            genfile=True,
            hash_files=False,
            name_source=['input_files'],
            name_template='%s_averaged.mnc',
            position=-1,
        ),
        quiet=dict(
            argstr='-quiet',
            xor=('verbose', 'quiet'),
        ),
        sdfile=dict(argstr='-sdfile %s', ),
        two=dict(argstr='-2', ),
        verbose=dict(
            argstr='-verbose',
            xor=('verbose', 'quiet'),
        ),
        voxel_range=dict(argstr='-range %d %d', ),
        weights=dict(
            argstr='-weights %s',
            sep=',',
        ),
        width_weighted=dict(
            argstr='-width_weighted',
            requires=('avgdim', ),
        ),
    )
    inputs = Average.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_Average_outputs():
    output_map = dict(output_file=dict(), )
    outputs = Average.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
