# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..preprocess import BlurInMask


def test_BlurInMask_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    automask=dict(argstr='-automask',
    ),
    float_out=dict(argstr='-float',
    ),
    fwhm=dict(argstr='-FWHM %f',
    mandatory=True,
    ),
    in_file=dict(argstr='-input %s',
    copyfile=False,
    mandatory=True,
    position=1,
    ),
    mask=dict(argstr='-mask %s',
    ),
    multimask=dict(argstr='-Mmask %s',
    ),
    options=dict(argstr='%s',
    position=2,
    ),
    out_file=dict(keep_extension=False,
    ),
    outputtype=dict(usedefault=True,
    ),
    prefix=dict(argstr='-prefix %s',
    keep_extension=False,
    ),
    preserve=dict(argstr='-preserve',
    ),
    )
    inputs = BlurInMask._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_BlurInMask_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = BlurInMask._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
