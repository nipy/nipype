# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ...testing import assert_equal
from ..meshfix import MeshFix


def test_MeshFix_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    cut_inner=dict(argstr='--cut-inner %d',
    ),
    cut_outer=dict(argstr='--cut-outer %d',
    ),
    decouple_inin=dict(argstr='--decouple-inin %d',
    ),
    decouple_outin=dict(argstr='--decouple-outin %d',
    ),
    decouple_outout=dict(argstr='--decouple-outout %d',
    ),
    dilation=dict(argstr='--dilate %d',
    ),
    dont_clean=dict(argstr='--no-clean',
    ),
    epsilon_angle=dict(argstr='-a %f',
    ),
    finetuning_distance=dict(argstr='%f',
    requires=['finetuning_substeps'],
    ),
    finetuning_inwards=dict(argstr='--fineTuneIn ',
    requires=['finetuning_distance', 'finetuning_substeps'],
    ),
    finetuning_outwards=dict(argstr='--fineTuneIn ',
    requires=['finetuning_distance', 'finetuning_substeps'],
    xor=['finetuning_inwards'],
    ),
    finetuning_substeps=dict(argstr='%d',
    requires=['finetuning_distance'],
    ),
    in_file1=dict(argstr='%s',
    mandatory=True,
    position=1,
    ),
    in_file2=dict(argstr='%s',
    position=2,
    ),
    join_closest_components=dict(argstr='-jc',
    xor=['join_closest_components'],
    ),
    join_overlapping_largest_components=dict(argstr='-j',
    xor=['join_closest_components'],
    ),
    laplacian_smoothing_steps=dict(argstr='--smooth %d',
    ),
    number_of_biggest_shells=dict(argstr='--shells %d',
    ),
    out_filename=dict(argstr='-o %s',
    genfile=True,
    ),
    output_type=dict(usedefault=True,
    ),
    quiet_mode=dict(argstr='-q',
    ),
    remove_handles=dict(argstr='--remove-handles',
    ),
    save_as_freesurfer_mesh=dict(argstr='--fsmesh',
    xor=['save_as_vrml', 'save_as_stl'],
    ),
    save_as_stl=dict(argstr='--stl',
    xor=['save_as_vmrl', 'save_as_freesurfer_mesh'],
    ),
    save_as_vmrl=dict(argstr='--wrl',
    xor=['save_as_stl', 'save_as_freesurfer_mesh'],
    ),
    set_intersections_to_one=dict(argstr='--intersect',
    ),
    uniform_remeshing_steps=dict(argstr='-u %d',
    requires=['uniform_remeshing_vertices'],
    ),
    uniform_remeshing_vertices=dict(argstr='--vertices %d',
    requires=['uniform_remeshing_steps'],
    ),
    x_shift=dict(argstr='--smooth %d',
    ),
    )
    inputs = MeshFix._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_MeshFix_outputs():
    output_map = dict(mesh_file=dict(),
    )
    outputs = MeshFix._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
