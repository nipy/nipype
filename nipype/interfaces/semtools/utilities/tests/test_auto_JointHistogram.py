from __future__ import unicode_literals
# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from nipype.testing import assert_equal
from nipype.interfaces.semtools.utilities.brains import JointHistogram

def test_JointHistogram_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    inputMaskVolumeInXAxis=dict(argstr='--inputMaskVolumeInXAxis %s',
    ),
    inputMaskVolumeInYAxis=dict(argstr='--inputMaskVolumeInYAxis %s',
    ),
    inputVolumeInXAxis=dict(argstr='--inputVolumeInXAxis %s',
    ),
    inputVolumeInYAxis=dict(argstr='--inputVolumeInYAxis %s',
    ),
    outputJointHistogramImage=dict(argstr='--outputJointHistogramImage %s',
    ),
    terminal_output=dict(nohash=True,
    ),
    verbose=dict(argstr='--verbose ',
    ),
    )
    inputs = JointHistogram.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value

def test_JointHistogram_outputs():
    output_map = dict()
    outputs = JointHistogram.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value

