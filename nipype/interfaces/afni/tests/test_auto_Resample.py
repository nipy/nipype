# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..utils import Resample


def test_Resample_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    in_file=dict(argstr='-inset %s',
    copyfile=False,
    mandatory=True,
    position=-1,
    ),
    master=dict(argstr='-master %s',
    ),
    orientation=dict(argstr='-orient %s',
    ),
    out_file=dict(argstr='-prefix %s',
    name_source='in_file',
    name_template='%s_resample',
    ),
    outputtype=dict(),
    resample_mode=dict(argstr='-rmode %s',
    ),
    terminal_output=dict(nohash=True,
    ),
    voxel_size=dict(argstr='-dxyz %f %f %f',
    ),
    )
    inputs = Resample.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_Resample_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = Resample.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
