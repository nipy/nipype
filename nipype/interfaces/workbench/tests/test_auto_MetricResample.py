# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..metric import MetricResample


def test_MetricResample_inputs():
    input_map = dict(
        area_metrics=dict(
            argstr='-area-metrics',
            position=5,
            xor=['area_surfs'],
        ),
        area_surfs=dict(
            argstr='-area-surfs',
            position=5,
            xor=['area_metrics'],
        ),
        args=dict(argstr='%s', ),
        current_area=dict(
            argstr='%s',
            position=6,
            usedefault=True,
        ),
        current_sphere=dict(
            argstr='%s',
            mandatory=True,
            position=1,
            usedefault=True,
        ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        in_file=dict(
            argstr='%s',
            mandatory=True,
            position=0,
            usedefault=True,
        ),
        largest=dict(
            argstr='-largest',
            position=10,
        ),
        method=dict(
            argstr='%s',
            mandatory=True,
            position=3,
        ),
        new_area=dict(
            argstr='%s',
            position=7,
            usedefault=True,
        ),
        new_sphere=dict(
            argstr='%s',
            mandatory=True,
            position=2,
            usedefault=True,
        ),
        out_file=dict(
            argstr='%s',
            keep_extension=True,
            name_source=['new_sphere'],
            name_template='%s.out',
            position=4,
            usedefault=True,
        ),
        roi_metric=dict(
            argstr='-current-roi %s',
            position=8,
            usedefault=True,
        ),
        valid_roi_out=dict(
            argstr='-valid-roi-out',
            position=9,
        ),
    )
    inputs = MetricResample.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_MetricResample_outputs():
    output_map = dict(
        out_file=dict(usedefault=True, ),
        roi_file=dict(usedefault=True, ),
    )
    outputs = MetricResample.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
