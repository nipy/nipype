from __future__ import unicode_literals
# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from nipype.testing import assert_equal
from nipype.interfaces.afni.preprocess import Refit

def test_Refit_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    deoblique=dict(argstr='-deoblique',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    in_file=dict(argstr='%s',
    copyfile=True,
    mandatory=True,
    position=-1,
    ),
    terminal_output=dict(nohash=True,
    ),
    xorigin=dict(argstr='-xorigin %s',
    ),
    yorigin=dict(argstr='-yorigin %s',
    ),
    zorigin=dict(argstr='-zorigin %s',
    ),
    )
    inputs = Refit.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value

def test_Refit_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = Refit.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value

