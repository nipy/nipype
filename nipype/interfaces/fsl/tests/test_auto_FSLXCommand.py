# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..dti import FSLXCommand


def test_FSLXCommand_inputs():
    input_map = dict(all_ard=dict(argstr='--allard',
    xor=('no_ard', 'all_ard'),
    ),
    args=dict(argstr='%s',
    ),
    burn_in=dict(argstr='--burnin=%d',
    ),
    burn_in_no_ard=dict(argstr='--burninnoard=%d',
    ),
    bvals=dict(argstr='--bvals=%s',
    mandatory=True,
    ),
    bvecs=dict(argstr='--bvecs=%s',
    mandatory=True,
    ),
    cnlinear=dict(argstr='--cnonlinear',
    xor=('no_spat', 'non_linear', 'cnlinear'),
    ),
    dwi=dict(argstr='--data=%s',
    mandatory=True,
    ),
    dyads=dict(),
    f0_ard=dict(argstr='--f0 --ardf0',
    xor=['f0_noard', 'f0_ard', 'all_ard'],
    ),
    f0_noard=dict(argstr='--f0',
    xor=['f0_noard', 'f0_ard'],
    ),
    force_dir=dict(argstr='--forcedir',
    usedefault=True,
    ),
    fsamples=dict(),
    fudge=dict(argstr='--fudge=%d',
    ),
    logdir=dict(argstr='--logdir=%s',
    usedefault=True,
    ),
    mask=dict(argstr='--mask=%s',
    mandatory=True,
    ),
    mean_S0samples=dict(keep_extension=False,
    ),
    mean_dsamples=dict(keep_extension=False,
    ),
    mean_fsamples=dict(),
    mean_tausamples=dict(keep_extension=False,
    ),
    model=dict(argstr='--model=%d',
    ),
    n_fibres=dict(argstr='--nfibres=%d',
    mandatory=True,
    usedefault=True,
    ),
    n_jumps=dict(argstr='--njumps=%d',
    ),
    no_ard=dict(argstr='--noard',
    xor=('no_ard', 'all_ard'),
    ),
    no_spat=dict(argstr='--nospat',
    xor=('no_spat', 'non_linear', 'cnlinear'),
    ),
    non_linear=dict(argstr='--nonlinear',
    xor=('no_spat', 'non_linear', 'cnlinear'),
    ),
    output_type=dict(usedefault=True,
    ),
    phsamples=dict(),
    rician=dict(argstr='--rician',
    usedefault=True,
    ),
    sample_every=dict(argstr='--sampleevery=%d',
    ),
    seed=dict(argstr='--seed=%d',
    ),
    thsamples=dict(),
    update_proposal_every=dict(argstr='--updateproposalevery=%d',
    ),
    )
    inputs = FSLXCommand._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_FSLXCommand_outputs():
    output_map = dict(dyads=dict(),
    fsamples=dict(),
    mean_S0samples=dict(),
    mean_dsamples=dict(),
    mean_fsamples=dict(),
    mean_tausamples=dict(),
    phsamples=dict(),
    thsamples=dict(),
    )
    outputs = FSLXCommand._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
