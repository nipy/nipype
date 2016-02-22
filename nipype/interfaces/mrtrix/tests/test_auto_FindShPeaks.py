# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..tensors import FindShPeaks


def test_FindShPeaks_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    directions_file=dict(argstr='%s',
    mandatory=True,
    position=-2,
    ),
    display_debug=dict(argstr='-debug',
    ),
    display_info=dict(argstr='-info',
    ),
    in_file=dict(argstr='%s',
    mandatory=True,
    position=-3,
    ),
    num_peaks=dict(argstr='-num %s',
    ),
    out_file=dict(argstr='%s',
    hash_files=False,
    keep_extension=False,
    name_source=['in_file'],
    name_template='%s_peak_dirs.mif',
    position=-1,
    ),
    peak_directions=dict(argstr='-direction %s',
    sep=' ',
    ),
    peak_threshold=dict(argstr='-threshold %s',
    ),
    peaks_image=dict(argstr='-peaks %s',
    ),
    quiet_display=dict(argstr='-quiet',
    ),
    )
    inputs = FindShPeaks._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_FindShPeaks_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = FindShPeaks._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
