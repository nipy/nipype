# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from nipype.testing import assert_equal
from nipype.interfaces.fsl.preprocess import BET

def test_BET_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    center=dict(argstr='-c %s',
    units='voxels',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    frac=dict(argstr='-f %.2f',
    ),
    functional=dict(argstr='-F',
    xor=('functional', 'reduce_bias', 'robust', 'padding', 'remove_eyes', 'surfaces', 't2_guided'),
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    in_file=dict(argstr='%s',
    mandatory=True,
    position=0,
    ),
    mask=dict(argstr='-m',
    ),
    mesh=dict(argstr='-e',
    ),
    no_output=dict(argstr='-n',
    ),
    out_file=dict(argstr='%s',
    hash_files=False,
    name_source=['in_file'],
    name_template='%s_brain',
    position=1,
    ),
    outline=dict(argstr='-o',
    ),
    output_type=dict(),
    padding=dict(argstr='-Z',
    xor=('functional', 'reduce_bias', 'robust', 'padding', 'remove_eyes', 'surfaces', 't2_guided'),
    ),
    radius=dict(argstr='-r %d',
    units='mm',
    ),
    reduce_bias=dict(argstr='-B',
    xor=('functional', 'reduce_bias', 'robust', 'padding', 'remove_eyes', 'surfaces', 't2_guided'),
    ),
    remove_eyes=dict(argstr='-S',
    xor=('functional', 'reduce_bias', 'robust', 'padding', 'remove_eyes', 'surfaces', 't2_guided'),
    ),
    robust=dict(argstr='-R',
    xor=('functional', 'reduce_bias', 'robust', 'padding', 'remove_eyes', 'surfaces', 't2_guided'),
    ),
    skull=dict(argstr='-s',
    ),
    surfaces=dict(argstr='-A',
    xor=('functional', 'reduce_bias', 'robust', 'padding', 'remove_eyes', 'surfaces', 't2_guided'),
    ),
    t2_guided=dict(argstr='-A2 %s',
    xor=('functional', 'reduce_bias', 'robust', 'padding', 'remove_eyes', 'surfaces', 't2_guided'),
    ),
    terminal_output=dict(nohash=True,
    ),
    threshold=dict(argstr='-t',
    ),
    vertical_gradient=dict(argstr='-g %.2f',
    ),
    )
    inputs = BET.input_spec()

    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(inputs.traits()[key], metakey), value

def test_BET_outputs():
    output_map = dict(inskull_mask_file=dict(),
    inskull_mesh_file=dict(),
    mask_file=dict(),
    meshfile=dict(),
    out_file=dict(),
    outline_file=dict(),
    outskin_mask_file=dict(),
    outskin_mesh_file=dict(),
    outskull_mask_file=dict(),
    outskull_mesh_file=dict(),
    skull_mask_file=dict(),
    )
    outputs = BET.output_spec()

    for key, metadata in output_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(outputs.traits()[key], metakey), value

