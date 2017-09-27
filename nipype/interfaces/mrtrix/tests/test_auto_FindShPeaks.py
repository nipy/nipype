# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
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
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
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
    resource_monitor=dict(nohash=True,
    usedefault=True,
    ),
    terminal_output=dict(nohash=True,
    ),
    )
    inputs = FindShPeaks.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_FindShPeaks_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = FindShPeaks.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
