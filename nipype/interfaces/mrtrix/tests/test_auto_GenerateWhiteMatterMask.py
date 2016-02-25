# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..preprocess import GenerateWhiteMatterMask


def test_GenerateWhiteMatterMask_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    binary_mask=dict(argstr='%s',
    mandatory=True,
    position=-2,
    ),
    encoding_file=dict(argstr='-grad %s',
    mandatory=True,
    position=1,
    ),
    in_file=dict(argstr='%s',
    mandatory=True,
    position=-3,
    ),
    noise_level_margin=dict(argstr='-margin %s',
    ),
    out_WMProb_filename=dict(argstr='%s',
    genfile=True,
    position=-1,
    ),
    )
    inputs = GenerateWhiteMatterMask._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_GenerateWhiteMatterMask_outputs():
    output_map = dict(WMprobabilitymap=dict(),
    )
    outputs = GenerateWhiteMatterMask._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
