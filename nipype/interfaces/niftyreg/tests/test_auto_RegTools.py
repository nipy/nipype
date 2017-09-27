# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..regutils import RegTools


def test_RegTools_inputs():
    input_map = dict(add_val=dict(argstr='-add %s',
    ),
    args=dict(argstr='%s',
    ),
    bin_flag=dict(argstr='-bin',
    ),
    chg_res_val=dict(argstr='-chgres %f %f %f',
    ),
    div_val=dict(argstr='-div %s',
    ),
    down_flag=dict(argstr='-down',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    in_file=dict(argstr='-in %s',
    mandatory=True,
    ),
    iso_flag=dict(argstr='-iso',
    ),
    mask_file=dict(argstr='-nan %s',
    ),
    mul_val=dict(argstr='-mul %s',
    ),
    noscl_flag=dict(argstr='-noscl',
    ),
    omp_core_val=dict(argstr='-omp %i',
    usedefault=True,
    ),
    out_file=dict(argstr='-out %s',
    name_source=['in_file'],
    name_template='%s_tools.nii.gz',
    ),
    resource_monitor=dict(nohash=True,
    usedefault=True,
    ),
    rms_val=dict(argstr='-rms %s',
    ),
    smo_g_val=dict(argstr='-smoG %f %f %f',
    ),
    smo_s_val=dict(argstr='-smoS %f %f %f',
    ),
    sub_val=dict(argstr='-sub %s',
    ),
    terminal_output=dict(nohash=True,
    ),
    thr_val=dict(argstr='-thr %f',
    ),
    )
    inputs = RegTools.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_RegTools_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = RegTools.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
