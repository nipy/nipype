# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..tensors import GenerateDirections


def test_GenerateDirections_inputs():
    input_map = dict(
        args=dict(argstr="%s",),
        display_debug=dict(argstr="-debug",),
        display_info=dict(argstr="-info",),
        environ=dict(nohash=True, usedefault=True,),
        niter=dict(argstr="-niter %s",),
        num_dirs=dict(argstr="%s", mandatory=True, position=-2,),
        out_file=dict(
            argstr="%s",
            extensions=None,
            hash_files=False,
            name_source=["num_dirs"],
            name_template="directions_%d.txt",
            position=-1,
        ),
        power=dict(argstr="-power %s",),
        quiet_display=dict(argstr="-quiet",),
    )
    inputs = GenerateDirections.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_GenerateDirections_outputs():
    output_map = dict(out_file=dict(extensions=None,),)
    outputs = GenerateDirections.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
