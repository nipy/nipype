# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..minc import Dump


def test_Dump_inputs():
    input_map = dict(
        annotations_brief=dict(
            argstr='-b %s',
            xor=('annotations_brief', 'annotations_full'),
        ),
        annotations_full=dict(
            argstr='-f %s',
            xor=('annotations_brief', 'annotations_full'),
        ),
        args=dict(argstr='%s', ),
        coordinate_data=dict(
            argstr='-c',
            xor=('coordinate_data', 'header_data'),
        ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        header_data=dict(
            argstr='-h',
            xor=('coordinate_data', 'header_data'),
        ),
        input_file=dict(
            argstr='%s',
            extensions=None,
            mandatory=True,
            position=-2,
        ),
        line_length=dict(argstr='-l %d', ),
        netcdf_name=dict(argstr='-n %s', ),
        out_file=dict(
            argstr='> %s',
            genfile=True,
            position=-1,
        ),
        output_file=dict(
            extensions=None,
            hash_files=False,
            keep_extension=False,
            name_source=['input_file'],
            name_template='%s_dump.txt',
            position=-1,
        ),
        precision=dict(argstr='%s', ),
        variables=dict(
            argstr='-v %s',
            sep=',',
        ),
    )
    inputs = Dump.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_Dump_outputs():
    output_map = dict(output_file=dict(extensions=None, ), )
    outputs = Dump.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
