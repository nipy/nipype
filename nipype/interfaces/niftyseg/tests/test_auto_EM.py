# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..em import EM


def test_EM_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    bc_order_val=dict(argstr='-bc_order %s',
    ),
    bc_thresh_val=dict(argstr='-bc_thresh %s',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    in_file=dict(argstr='-in %s',
    mandatory=True,
    position=4,
    ),
    mask_file=dict(argstr='-mask %s',
    ),
    max_iter=dict(argstr='-max_iter %s',
    ),
    min_iter=dict(argstr='-min_iter %s',
    ),
    mrf_beta_val=dict(argstr='-mrf_beta %s',
    ),
    no_prior=dict(argstr='-nopriors %s',
    mandatory=True,
    xor=['prior_4D', 'priors'],
    ),
    out_bc_file=dict(argstr='-bc_out %s',
    name_source=['in_file'],
    name_template='%s_bc_em.nii.gz',
    ),
    out_file=dict(argstr='-out %s',
    name_source=['in_file'],
    name_template='%s_em.nii.gz',
    ),
    out_outlier_file=dict(argstr='-out_outlier %s',
    name_source=['in_file'],
    name_template='%s_outlier_em.nii.gz',
    ),
    outlier_val=dict(argstr='-outlier %s %s',
    ),
    prior_4D=dict(argstr='-prior4D %s',
    mandatory=True,
    xor=['no_prior', 'priors'],
    ),
    priors=dict(argstr='%s',
    mandatory=True,
    xor=['no_prior', 'prior_4D'],
    ),
    reg_val=dict(argstr='-reg %s',
    ),
    relax_priors=dict(argstr='-rf %s %s',
    ),
    resource_monitor=dict(nohash=True,
    usedefault=True,
    ),
    terminal_output=dict(nohash=True,
    ),
    )
    inputs = EM.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_EM_outputs():
    output_map = dict(out_bc_file=dict(),
    out_file=dict(),
    out_outlier_file=dict(),
    )
    outputs = EM.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
