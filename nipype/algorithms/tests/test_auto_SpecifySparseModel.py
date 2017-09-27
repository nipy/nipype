# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..modelgen import SpecifySparseModel


def test_SpecifySparseModel_inputs():
    input_map = dict(event_files=dict(mandatory=True,
    xor=['subject_info', 'event_files'],
    ),
    functional_runs=dict(copyfile=False,
    mandatory=True,
    ),
    high_pass_filter_cutoff=dict(mandatory=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    input_units=dict(mandatory=True,
    ),
    model_hrf=dict(),
    outlier_files=dict(copyfile=False,
    ),
    parameter_source=dict(usedefault=True,
    ),
    realignment_parameters=dict(copyfile=False,
    ),
    resource_monitor=dict(nohash=True,
    usedefault=True,
    ),
    save_plot=dict(),
    scale_regressors=dict(usedefault=True,
    ),
    scan_onset=dict(usedefault=True,
    ),
    stimuli_as_impulses=dict(usedefault=True,
    ),
    subject_info=dict(mandatory=True,
    xor=['subject_info', 'event_files'],
    ),
    time_acquisition=dict(mandatory=True,
    ),
    time_repetition=dict(mandatory=True,
    ),
    use_temporal_deriv=dict(requires=['model_hrf'],
    ),
    volumes_in_cluster=dict(usedefault=True,
    ),
    )
    inputs = SpecifySparseModel.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_SpecifySparseModel_outputs():
    output_map = dict(session_info=dict(),
    sparse_png_file=dict(),
    sparse_svg_file=dict(),
    )
    outputs = SpecifySparseModel.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
