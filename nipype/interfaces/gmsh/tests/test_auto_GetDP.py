# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from nipype.testing import assert_equal
from nipype.interfaces.gmsh.getdp import GetDP

def test_GetDP_inputs():
    input_map = dict(adapatation_constraint_file=dict(argstr='-adapt %s',
    ),
    args=dict(argstr='%s',
    ),
    binary_output_files=dict(argstr='-bin',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    gmsh_read_file=dict(argstr='-gmshread %s',
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    maximum_interpolation_order=dict(argstr='-order %d',
    ),
    mesh_based_output_files=dict(argstr='-v2',
    ),
    mesh_file=dict(argstr='-msh %s',
    mandatory=True,
    ),
    out_pos_filenames=dict(),
    out_table_filenames=dict(),
    output_name=dict(argstr='-name %s',
    usedefault=True,
    ),
    postprocessing_type=dict(argstr='-post %s',
    ),
    preprocessing_type=dict(argstr='-pre %s',
    ),
    problem_file=dict(argstr='%s',
    mandatory=True,
    position=1,
    ),
    restart_processing=dict(argstr='-restart',
    ),
    results_file=dict(argstr='-res %s',
    ),
    run_processing=dict(argstr='-cal',
    ),
    save_results_separately=dict(argstr='-split',
    ),
    solve=dict(argstr='-solve %s',
    ),
    terminal_output=dict(mandatory=True,
    nohash=True,
    ),
    )
    inputs = GetDP.input_spec()

    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(inputs.traits()[key], metakey), value

def test_GetDP_outputs():
    output_map = dict(postprocessing_files=dict(),
    preprocessing_file=dict(),
    results_file=dict(),
    table_files=dict(),
    )
    outputs = GetDP.output_spec()

    for key, metadata in output_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(outputs.traits()[key], metakey), value

