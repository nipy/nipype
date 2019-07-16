# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..preprocess import Smooth


def test_Smooth_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        in_file=dict(
            argstr='--i %s',
            mandatory=True,
            usedefault=True,
        ),
        num_iters=dict(
            argstr='--niters %d',
            mandatory=True,
            xor=['surface_fwhm'],
        ),
        proj_frac=dict(
            argstr='--projfrac %s',
            xor=['proj_frac_avg'],
        ),
        proj_frac_avg=dict(
            argstr='--projfrac-avg %.2f %.2f %.2f',
            xor=['proj_frac'],
        ),
        reg_file=dict(
            argstr='--reg %s',
            mandatory=True,
            usedefault=True,
        ),
        smoothed_file=dict(
            argstr='--o %s',
            genfile=True,
            usedefault=True,
        ),
        subjects_dir=dict(usedefault=True, ),
        surface_fwhm=dict(
            argstr='--fwhm %f',
            mandatory=True,
            requires=['reg_file'],
            xor=['num_iters'],
        ),
        vol_fwhm=dict(argstr='--vol-fwhm %f', ),
    )
    inputs = Smooth.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_Smooth_outputs():
    output_map = dict(smoothed_file=dict(usedefault=True, ), )
    outputs = Smooth.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
