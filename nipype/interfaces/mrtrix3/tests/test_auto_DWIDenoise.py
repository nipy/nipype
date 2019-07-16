# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..preprocess import DWIDenoise


def test_DWIDenoise_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        bval_scale=dict(argstr='-bvalue_scaling %s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        extent=dict(argstr='-extent %d,%d,%d', ),
        grad_file=dict(
            argstr='-grad %s',
            usedefault=True,
        ),
        grad_fsl=dict(argstr='-fslgrad %s %s', ),
        in_bval=dict(usedefault=True, ),
        in_bvec=dict(
            argstr='-fslgrad %s %s',
            usedefault=True,
        ),
        in_file=dict(
            argstr='%s',
            mandatory=True,
            position=-2,
            usedefault=True,
        ),
        mask=dict(
            argstr='-mask %s',
            position=1,
            usedefault=True,
        ),
        noise=dict(
            argstr='-noise %s',
            usedefault=True,
        ),
        nthreads=dict(
            argstr='-nthreads %d',
            nohash=True,
        ),
        out_file=dict(
            argstr='%s',
            genfile=True,
            keep_extension=True,
            name_source='in_file',
            name_template='%s_denoised',
            position=-1,
            usedefault=True,
        ),
    )
    inputs = DWIDenoise.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_DWIDenoise_outputs():
    output_map = dict(
        noise=dict(usedefault=True, ),
        out_file=dict(usedefault=True, ),
    )
    outputs = DWIDenoise.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
