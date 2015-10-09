# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from nipype.testing import assert_equal
from nipype.interfaces.afni.preprocess import BlurInMask

def test_BlurInMask_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    automask=dict(argstr='-automask',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    float_out=dict(argstr='-float',
    ),
    fwhm=dict(argstr='-FWHM %f',
    mandatory=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
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
    out_file=dict(argstr='-prefix %s',
    keep_extension=False,
    name_source='in_file',
    name_template='%s_blur',
    position=-1,
    ),
    outputtype=dict(),
    preserve=dict(argstr='-preserve',
    ),
    terminal_output=dict(nohash=True,
    ),
    )
    inputs = BlurInMask.input_spec()

    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(inputs.traits()[key], metakey), value

def test_BlurInMask_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = BlurInMask.output_spec()

    for key, metadata in output_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(outputs.traits()[key], metakey), value

