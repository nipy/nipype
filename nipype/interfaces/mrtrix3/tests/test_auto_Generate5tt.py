# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..utils import Generate5tt


def test_Generate5tt_inputs():
    input_map = dict(
        algorithm=dict(argstr="%s", mandatory=True, position=-3,),
        args=dict(argstr="%s",),
        bval_scale=dict(argstr="-bvalue_scaling %s",),
        environ=dict(nohash=True, usedefault=True,),
        grad_file=dict(argstr="-grad %s", extensions=None, xor=["grad_fsl"],),
        grad_fsl=dict(argstr="-fslgrad %s %s", xor=["grad_file"],),
        in_bval=dict(extensions=None,),
        in_bvec=dict(argstr="-fslgrad %s %s", extensions=None,),
        in_file=dict(argstr="%s", extensions=None, mandatory=True, position=-2,),
        nthreads=dict(argstr="-nthreads %d", nohash=True,),
        out_file=dict(argstr="%s", extensions=None, mandatory=True, position=-1,),
    )
    inputs = Generate5tt.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_Generate5tt_outputs():
    output_map = dict(out_file=dict(extensions=None,),)
    outputs = Generate5tt.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
