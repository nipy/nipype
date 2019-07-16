# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..confounds import ACompCor


def test_ACompCor_inputs():
    input_map = dict(
        components_file=dict(usedefault=True, ),
        failure_mode=dict(usedefault=True, ),
        header_prefix=dict(),
        high_pass_cutoff=dict(usedefault=True, ),
        ignore_initial_volumes=dict(usedefault=True, ),
        mask_files=dict(),
        mask_index=dict(
            requires=['mask_files'],
            xor=['merge_method'],
        ),
        mask_names=dict(),
        merge_method=dict(
            requires=['mask_files'],
            xor=['mask_index'],
        ),
        num_components=dict(xor=['variance_threshold'], ),
        pre_filter=dict(usedefault=True, ),
        realigned_file=dict(
            mandatory=True,
            usedefault=True,
        ),
        regress_poly_degree=dict(usedefault=True, ),
        repetition_time=dict(),
        save_metadata=dict(usedefault=True, ),
        save_pre_filter=dict(usedefault=True, ),
        use_regress_poly=dict(
            deprecated='0.15.0',
            new_name='pre_filter',
        ),
        variance_threshold=dict(xor=['num_components'], ),
    )
    inputs = ACompCor.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_ACompCor_outputs():
    output_map = dict(
        components_file=dict(usedefault=True, ),
        metadata_file=dict(usedefault=True, ),
        pre_filter_file=dict(usedefault=True, ),
    )
    outputs = ACompCor.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
