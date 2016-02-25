# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..utils import BrainMask


def test_BrainMask_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    bval_scale=dict(argstr='-bvalue_scaling %s',
    ),
    grad_file=dict(argstr='-grad %s',
    ),
    grad_fsl=dict(argstr='-fslgrad %s %s',
    ),
    in_bval=dict(),
    in_bvec=dict(argstr='-fslgrad %s %s',
    ),
    in_file=dict(argstr='%s',
    mandatory=True,
    position=-2,
    ),
    nthreads=dict(argstr='-nthreads %d',
    nohash=True,
    ),
    out_file=dict(argstr='%s',
    mandatory=True,
    position=-1,
    usedefault=True,
    ),
    )
    inputs = BrainMask._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_BrainMask_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = BrainMask._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
