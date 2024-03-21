# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..utils import Generate5tt2gmwmi


def test_Generate5tt2gmwmi_inputs():
    input_map = dict(
        args=dict(
            argstr="%s",
        ),
        bval_scale=dict(
            argstr="-bvalue_scaling %s",
        ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        grad_file=dict(
            argstr="-grad %s",
            extensions=None,
            xor=["grad_fsl"],
        ),
        grad_fsl=dict(
            argstr="-fslgrad %s %s",
            xor=["grad_file"],
        ),
        in_bval=dict(
            extensions=None,
        ),
        in_bvec=dict(
            argstr="-fslgrad %s %s",
            extensions=None,
        ),
        in_file=dict(
            argstr="%s",
            extensions=None,
            mandatory=True,
            position=-2,
        ),
        mask_in=dict(
            argstr="-mask_in %s",
            extensions=None,
            position=-3,
        ),
        mask_out=dict(
            argstr="%s",
            extensions=None,
            mandatory=True,
            position=-1,
        ),
        nthreads=dict(
            argstr="-nthreads %d",
            nohash=True,
        ),
        out_bval=dict(
            extensions=None,
        ),
        out_bvec=dict(
            argstr="-export_grad_fsl %s %s",
            extensions=None,
        ),
    )
    inputs = Generate5tt2gmwmi.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_Generate5tt2gmwmi_outputs():
    output_map = dict(
        mask_out=dict(
            extensions=None,
        ),
    )
    outputs = Generate5tt2gmwmi.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
