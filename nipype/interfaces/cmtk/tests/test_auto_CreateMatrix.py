# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..cmtk import CreateMatrix


def test_CreateMatrix_inputs():
    input_map = dict(
        count_region_intersections=dict(usedefault=True, ),
        out_endpoint_array_name=dict(
            genfile=True,
            usedefault=True,
        ),
        out_fiber_length_std_matrix_mat_file=dict(
            genfile=True,
            usedefault=True,
        ),
        out_intersection_matrix_mat_file=dict(
            genfile=True,
            usedefault=True,
        ),
        out_matrix_file=dict(
            genfile=True,
            usedefault=True,
        ),
        out_matrix_mat_file=dict(usedefault=True, ),
        out_mean_fiber_length_matrix_mat_file=dict(
            genfile=True,
            usedefault=True,
        ),
        out_median_fiber_length_matrix_mat_file=dict(
            genfile=True,
            usedefault=True,
        ),
        resolution_network_file=dict(
            mandatory=True,
            usedefault=True,
        ),
        roi_file=dict(
            mandatory=True,
            usedefault=True,
        ),
        tract_file=dict(
            mandatory=True,
            usedefault=True,
        ),
    )
    inputs = CreateMatrix.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_CreateMatrix_outputs():
    output_map = dict(
        endpoint_file=dict(usedefault=True, ),
        endpoint_file_mm=dict(usedefault=True, ),
        fiber_label_file=dict(usedefault=True, ),
        fiber_labels_noorphans=dict(usedefault=True, ),
        fiber_length_file=dict(usedefault=True, ),
        fiber_length_std_matrix_mat_file=dict(usedefault=True, ),
        filtered_tractographies=dict(),
        filtered_tractography=dict(usedefault=True, ),
        filtered_tractography_by_intersections=dict(usedefault=True, ),
        intersection_matrix_file=dict(usedefault=True, ),
        intersection_matrix_mat_file=dict(usedefault=True, ),
        matlab_matrix_files=dict(),
        matrix_file=dict(usedefault=True, ),
        matrix_files=dict(),
        matrix_mat_file=dict(usedefault=True, ),
        mean_fiber_length_matrix_mat_file=dict(usedefault=True, ),
        median_fiber_length_matrix_mat_file=dict(usedefault=True, ),
        stats_file=dict(usedefault=True, ),
    )
    outputs = CreateMatrix.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
