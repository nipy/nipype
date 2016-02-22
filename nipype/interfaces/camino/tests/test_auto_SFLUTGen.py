# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..calib import SFLUTGen


def test_SFLUTGen_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    binincsize=dict(argstr='-binincsize %d',
    units='NA',
    ),
    directmap=dict(argstr='-directmap',
    ),
    in_file=dict(argstr='-inputfile %s',
    mandatory=True,
    ),
    info_file=dict(argstr='-infofile %s',
    mandatory=True,
    ),
    minvectsperbin=dict(argstr='-minvectsperbin %d',
    units='NA',
    ),
    order=dict(argstr='-order %d',
    units='NA',
    ),
    out_file=dict(argstr='> %s',
    position=-1,
    usedefault=True,
    ),
    outputstem=dict(argstr='-outputstem %s',
    usedefault=True,
    ),
    pdf=dict(argstr='-pdf %s',
    usedefault=True,
    ),
    )
    inputs = SFLUTGen._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_SFLUTGen_outputs():
    output_map = dict(lut_one_fibre=dict(),
    lut_two_fibres=dict(),
    )
    outputs = SFLUTGen._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
