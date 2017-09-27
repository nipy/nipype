# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..fiberprocess import fiberprocess


def test_fiberprocess_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    displacement_field=dict(argstr='--displacement_field %s',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    fiber_file=dict(argstr='--fiber_file %s',
    ),
    fiber_output=dict(argstr='--fiber_output %s',
    hash_files=False,
    ),
    fiber_radius=dict(argstr='--fiber_radius %f',
    ),
    h_field=dict(argstr='--h_field %s',
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    index_space=dict(argstr='--index_space ',
    ),
    noDataChange=dict(argstr='--noDataChange ',
    ),
    no_warp=dict(argstr='--no_warp ',
    ),
    resource_monitor=dict(nohash=True,
    usedefault=True,
    ),
    saveProperties=dict(argstr='--saveProperties ',
    ),
    tensor_volume=dict(argstr='--tensor_volume %s',
    ),
    terminal_output=dict(nohash=True,
    ),
    verbose=dict(argstr='--verbose ',
    ),
    voxel_label=dict(argstr='--voxel_label %d',
    ),
    voxelize=dict(argstr='--voxelize %s',
    hash_files=False,
    ),
    voxelize_count_fibers=dict(argstr='--voxelize_count_fibers ',
    ),
    )
    inputs = fiberprocess.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_fiberprocess_outputs():
    output_map = dict(fiber_output=dict(),
    voxelize=dict(),
    )
    outputs = fiberprocess.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
