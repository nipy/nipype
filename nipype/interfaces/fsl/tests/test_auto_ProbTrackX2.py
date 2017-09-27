# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..dti import ProbTrackX2


def test_ProbTrackX2_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    avoid_mp=dict(argstr='--avoid=%s',
    ),
    c_thresh=dict(argstr='--cthr=%.3f',
    ),
    colmask4=dict(argstr='--colmask4=%s',
    ),
    correct_path_distribution=dict(argstr='--pd',
    ),
    dist_thresh=dict(argstr='--distthresh=%.3f',
    ),
    distthresh1=dict(argstr='--distthresh1=%.3f',
    ),
    distthresh3=dict(argstr='--distthresh3=%.3f',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    fibst=dict(argstr='--fibst=%d',
    ),
    fopd=dict(argstr='--fopd=%s',
    ),
    force_dir=dict(argstr='--forcedir',
    usedefault=True,
    ),
    fsamples=dict(mandatory=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    inv_xfm=dict(argstr='--invxfm=%s',
    ),
    loop_check=dict(argstr='--loopcheck',
    ),
    lrtarget3=dict(argstr='--lrtarget3=%s',
    ),
    mask=dict(argstr='-m %s',
    mandatory=True,
    ),
    meshspace=dict(argstr='--meshspace=%s',
    ),
    mod_euler=dict(argstr='--modeuler',
    ),
    n_samples=dict(argstr='--nsamples=%d',
    usedefault=True,
    ),
    n_steps=dict(argstr='--nsteps=%d',
    ),
    network=dict(argstr='--network',
    ),
    omatrix1=dict(argstr='--omatrix1',
    ),
    omatrix2=dict(argstr='--omatrix2',
    requires=['target2'],
    ),
    omatrix3=dict(argstr='--omatrix3',
    requires=['target3', 'lrtarget3'],
    ),
    omatrix4=dict(argstr='--omatrix4',
    ),
    onewaycondition=dict(argstr='--onewaycondition',
    ),
    opd=dict(argstr='--opd',
    usedefault=True,
    ),
    os2t=dict(argstr='--os2t',
    ),
    out_dir=dict(argstr='--dir=%s',
    genfile=True,
    ),
    output_type=dict(),
    phsamples=dict(mandatory=True,
    ),
    rand_fib=dict(argstr='--randfib=%d',
    ),
    random_seed=dict(argstr='--rseed',
    ),
    resource_monitor=dict(nohash=True,
    usedefault=True,
    ),
    s2tastext=dict(argstr='--s2tastext',
    ),
    sample_random_points=dict(argstr='--sampvox',
    ),
    samples_base_name=dict(argstr='--samples=%s',
    usedefault=True,
    ),
    seed=dict(argstr='--seed=%s',
    mandatory=True,
    ),
    seed_ref=dict(argstr='--seedref=%s',
    ),
    simple=dict(argstr='--simple',
    usedefault=False,
    ),
    step_length=dict(argstr='--steplength=%.3f',
    ),
    stop_mask=dict(argstr='--stop=%s',
    ),
    target2=dict(argstr='--target2=%s',
    ),
    target3=dict(argstr='--target3=%s',
    ),
    target4=dict(argstr='--target4=%s',
    ),
    target_masks=dict(argstr='--targetmasks=%s',
    ),
    terminal_output=dict(nohash=True,
    ),
    thsamples=dict(mandatory=True,
    ),
    use_anisotropy=dict(argstr='--usef',
    ),
    verbose=dict(argstr='--verbose=%d',
    ),
    waycond=dict(argstr='--waycond=%s',
    ),
    wayorder=dict(argstr='--wayorder',
    ),
    waypoints=dict(argstr='--waypoints=%s',
    ),
    xfm=dict(argstr='--xfm=%s',
    ),
    )
    inputs = ProbTrackX2.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_ProbTrackX2_outputs():
    output_map = dict(fdt_paths=dict(),
    log=dict(),
    lookup_tractspace=dict(),
    matrix1_dot=dict(),
    matrix2_dot=dict(),
    matrix3_dot=dict(),
    network_matrix=dict(),
    particle_files=dict(),
    targets=dict(),
    way_total=dict(),
    )
    outputs = ProbTrackX2.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
