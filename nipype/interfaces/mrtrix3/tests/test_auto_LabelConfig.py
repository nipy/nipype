# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..connectivity import LabelConfig


def test_LabelConfig_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    in_config=dict(argstr='%s',
    position=-2,
    ),
    in_file=dict(argstr='%s',
    mandatory=True,
    position=-3,
    ),
    lut_aal=dict(argstr='-lut_aal %s',
    ),
    lut_basic=dict(argstr='-lut_basic %s',
    ),
    lut_fs=dict(argstr='-lut_freesurfer %s',
    ),
    lut_itksnap=dict(argstr='-lut_itksnap %s',
    ),
    nthreads=dict(argstr='-nthreads %d',
    nohash=True,
    ),
    out_file=dict(argstr='%s',
    mandatory=True,
    position=-1,
    usedefault=True,
    ),
    spine=dict(argstr='-spine %s',
    ),
    )
    inputs = LabelConfig._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_LabelConfig_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = LabelConfig._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
