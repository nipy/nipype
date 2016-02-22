# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..dti import DTIFit


def test_DTIFit_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    base_name=dict(argstr='-o %s',
    position=1,
    usedefault=True,
    ),
    bvals=dict(argstr='-b %s',
    mandatory=True,
    position=4,
    ),
    bvecs=dict(argstr='-r %s',
    mandatory=True,
    position=3,
    ),
    cni=dict(argstr='--cni=%s',
    ),
    dwi=dict(argstr='-k %s',
    mandatory=True,
    position=0,
    ),
    gradnonlin=dict(argstr='--gradnonlin=%s',
    ),
    little_bit=dict(argstr='--littlebit',
    ),
    mask=dict(argstr='-m %s',
    mandatory=True,
    position=2,
    ),
    max_x=dict(argstr='-X %d',
    ),
    max_y=dict(argstr='-Y %d',
    ),
    max_z=dict(argstr='-Z %d',
    ),
    min_x=dict(argstr='-x %d',
    ),
    min_y=dict(argstr='-y %d',
    ),
    min_z=dict(argstr='-z %d',
    ),
    out_fa=dict(keep_extension=False,
    ),
    out_l1=dict(keep_extension=False,
    ),
    out_l2=dict(keep_extension=False,
    ),
    out_l3=dict(keep_extension=False,
    ),
    out_md=dict(keep_extension=False,
    ),
    out_mo=dict(keep_extension=False,
    ),
    out_s0=dict(keep_extension=False,
    ),
    out_v1=dict(keep_extension=False,
    ),
    out_v2=dict(keep_extension=False,
    ),
    out_v3=dict(keep_extension=False,
    ),
    output_type=dict(usedefault=True,
    ),
    save_tensor=dict(argstr='--save_tensor',
    usedefault=True,
    ),
    sse=dict(argstr='--sse',
    ),
    tensor=dict(keep_extension=False,
    ),
    )
    inputs = DTIFit._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_DTIFit_outputs():
    output_map = dict(out_fa=dict(),
    out_l1=dict(),
    out_l2=dict(),
    out_l3=dict(),
    out_md=dict(),
    out_mo=dict(),
    out_s0=dict(),
    out_v1=dict(),
    out_v2=dict(),
    out_v3=dict(),
    tensor=dict(),
    )
    outputs = DTIFit._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
