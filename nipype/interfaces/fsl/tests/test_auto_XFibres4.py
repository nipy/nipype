# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..dti import XFibres4


def test_XFibres4_inputs():
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
    dwi=dict(argstr='--data=%s',
    mandatory=True,
    ),
    force_dir=dict(argstr='--forcedir',
    usedefault=True,
    ),
    fudge=dict(argstr='--fudge=%d',
    ),
    gradnonlin=dict(argstr='--gradnonlin=%s',
    ),
    logdir=dict(argstr='--logdir=%s',
    usedefault=True,
    ),
    mask=dict(argstr='--mask=%s',
    mandatory=True,
    ),
    model=dict(argstr='--model=%d',
    ),
    n_fibres=dict(argstr='--nfibres=%d',
    ),
    n_jumps=dict(argstr='--njumps=%d',
    ),
    no_ard=dict(argstr='--noard',
    xor=('no_ard', 'all_ard'),
    ),
    no_spat=dict(argstr='--nospat',
    xor=('no_spat', 'non_linear'),
    ),
    non_linear=dict(argstr='--nonlinear',
    xor=('no_spat', 'non_linear'),
    ),
    output_type=dict(usedefault=True,
    ),
    sample_every=dict(argstr='--sampleevery=%d',
    ),
    seed=dict(argstr='--seed=%d',
    ),
    update_proposal_every=dict(argstr='--updateproposalevery=%d',
    ),
    )
    inputs = XFibres4._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_XFibres4_outputs():
    output_map = dict(dyads=dict(),
    fsamples=dict(),
    mean_S0samples=dict(),
    mean_dsamples=dict(),
    mean_fsamples=dict(),
    phsamples=dict(),
    thsamples=dict(),
    )
    outputs = XFibres4._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
