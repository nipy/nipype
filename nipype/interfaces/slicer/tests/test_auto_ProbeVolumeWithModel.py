# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..surface import ProbeVolumeWithModel


def test_ProbeVolumeWithModel_inputs():
    input_map = dict(InputModel=dict(argstr='%s',
    position=-2,
    ),
    InputVolume=dict(argstr='%s',
    position=-3,
    ),
    OutputModel=dict(argstr='%s',
    hash_files=False,
    position=-1,
    ),
    args=dict(argstr='%s',
    ),
    )
    inputs = ProbeVolumeWithModel._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_ProbeVolumeWithModel_outputs():
    output_map = dict(OutputModel=dict(position=-1,
    ),
    )
    outputs = ProbeVolumeWithModel._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
