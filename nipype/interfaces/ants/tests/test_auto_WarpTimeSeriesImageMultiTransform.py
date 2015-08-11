from __future__ import unicode_literals
# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from nipype.testing import assert_equal
from nipype.interfaces.ants.resampling import WarpTimeSeriesImageMultiTransform

def test_WarpTimeSeriesImageMultiTransform_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    dimension=dict(argstr='%d',
    position=1,
    usedefault=True,
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    input_image=dict(argstr='%s',
    copyfile=True,
    mandatory=True,
    ),
    invert_affine=dict(),
    num_threads=dict(nohash=True,
    usedefault=True,
    ),
    out_postfix=dict(argstr='%s',
    usedefault=True,
    ),
    reference_image=dict(argstr='-R %s',
    xor=['tightest_box'],
    ),
    reslice_by_header=dict(argstr='--reslice-by-header',
    ),
    terminal_output=dict(nohash=True,
    ),
    tightest_box=dict(argstr='--tightest-bounding-box',
    xor=['reference_image'],
    ),
    transformation_series=dict(argstr='%s',
    copyfile=False,
    mandatory=True,
    ),
    use_bspline=dict(argstr='--use-Bspline',
    ),
    use_nearest=dict(argstr='--use-NN',
    ),
    )
    inputs = WarpTimeSeriesImageMultiTransform.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value

def test_WarpTimeSeriesImageMultiTransform_outputs():
    output_map = dict(output_image=dict(),
    )
    outputs = WarpTimeSeriesImageMultiTransform.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value

