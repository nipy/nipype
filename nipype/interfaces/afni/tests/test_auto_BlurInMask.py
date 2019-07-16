# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..preprocess import BlurInMask


def test_BlurInMask_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        automask=dict(argstr='-automask', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        float_out=dict(argstr='-float', ),
        fwhm=dict(
            argstr='-FWHM %f',
            mandatory=True,
        ),
        in_file=dict(
            argstr='-input %s',
            copyfile=False,
            mandatory=True,
            position=1,
            usedefault=True,
        ),
        mask=dict(
            argstr='-mask %s',
            usedefault=True,
        ),
        multimask=dict(
            argstr='-Mmask %s',
            usedefault=True,
        ),
        num_threads=dict(
            nohash=True,
            usedefault=True,
        ),
        options=dict(
            argstr='%s',
            position=2,
        ),
        out_file=dict(
            argstr='-prefix %s',
            name_source='in_file',
            name_template='%s_blur',
            position=-1,
            usedefault=True,
        ),
        outputtype=dict(),
        preserve=dict(argstr='-preserve', ),
    )
    inputs = BlurInMask.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_BlurInMask_outputs():
    output_map = dict(out_file=dict(usedefault=True, ), )
    outputs = BlurInMask.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
