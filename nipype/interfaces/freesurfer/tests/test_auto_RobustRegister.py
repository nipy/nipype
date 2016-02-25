# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..preprocess import RobustRegister


def test_RobustRegister_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    auto_sens=dict(argstr='--satit',
    mandatory=True,
    xor=['outlier_sens'],
    ),
    est_int_scale=dict(argstr='--iscale',
    ),
    force_double=dict(argstr='--doubleprec',
    ),
    force_float=dict(argstr='--floattype',
    ),
    half_source=dict(argstr='--halfmov %s',
    ),
    half_source_xfm=dict(argstr='--halfmovlta %s',
    ),
    half_targ=dict(argstr='--halfdst %s',
    ),
    half_targ_xfm=dict(argstr='--halfdstlta %s',
    ),
    half_weights=dict(argstr='--halfweights %s',
    ),
    high_iterations=dict(argstr='--highit %d',
    ),
    in_xfm_file=dict(argstr='--transform',
    ),
    init_orient=dict(argstr='--initorient',
    ),
    iteration_thresh=dict(argstr='--epsit %.3f',
    ),
    least_squares=dict(argstr='--leastsquares',
    ),
    mask_source=dict(argstr='--maskmov %s',
    ),
    mask_target=dict(argstr='--maskdst %s',
    ),
    max_iterations=dict(argstr='--maxit %d',
    ),
    no_init=dict(argstr='--noinit',
    ),
    no_multi=dict(argstr='--nomulti',
    ),
    out_reg_file=dict(argstr='--lta %s',
    genfile=True,
    ),
    outlier_limit=dict(argstr='--wlimit %.3f',
    ),
    outlier_sens=dict(argstr='--sat %.4f',
    mandatory=True,
    xor=['auto_sens'],
    ),
    registered_file=dict(argstr='--warp %s',
    ),
    source_file=dict(argstr='--mov %s',
    mandatory=True,
    ),
    subjects_dir=dict(),
    subsample_thresh=dict(argstr='--subsample %d',
    ),
    target_file=dict(argstr='--dst %s',
    mandatory=True,
    ),
    trans_only=dict(argstr='--transonly',
    ),
    weights_file=dict(argstr='--weights %s',
    ),
    write_vo2vox=dict(argstr='--vox2vox',
    ),
    )
    inputs = RobustRegister._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_RobustRegister_outputs():
    output_map = dict(half_source=dict(),
    half_source_xfm=dict(),
    half_targ=dict(),
    half_targ_xfm=dict(),
    half_weights=dict(),
    out_reg_file=dict(),
    registered_file=dict(),
    weights_file=dict(),
    )
    outputs = RobustRegister._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
