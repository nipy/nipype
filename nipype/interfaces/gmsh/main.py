from nipype.interfaces.base import (CommandLine, CommandLineInputSpec,
				    traits, TraitedSpec, isdefined, InputMultiPath,
				    File)
import os, os.path as op
from nipype.utils.filemanip import split_filename

class GmshInputSpec(CommandLineInputSpec):
	'''
	Geometry options:
	'''
	unroll_geometry = traits.Bool(argstr='-0', desc="Output unrolled geometry, then exit")
	geometrical_tolerance = traits.Float(argstr='-tol %f',
	      desc="Set geometrical tolerance")


	match_geometries_and_meshes = traits.Bool(argstr='-match', desc="Match geometries and meshes")
	'''
	Mesh options:
	  -1, -2, -3           Perform 1D, 2D or 3D mesh generation, then exit
	'''
	mesh_generation_dimension = traits.Enum(['1', '2', '3'], argstr='-%s',
		desc='Perform 1D, 2D or 3D mesh generation, then exit')

	output_type = traits.Enum('msh', ['msh', 'msh1', 'msh2', 'unv', 'vrml', 'ply2', 'stl', 'mesh', 'bdf', 'cgns', 'p3d', 'diff', 'med'], argstr='-format %s',
		usedefault=True, desc='Select output mesh format (auto (default), msh, msh1, msh2, unv, vrml, ply2, stl, mesh, bdf, cgns, p3d, diff, med, ...)')

	version = traits.Enum(['1', '2'], desc='Select msh file version')

	uniform_mesh_refinement = traits.Bool(argstr='-refine', desc="Perform uniform mesh refinement, then exit")
	#-part int            Partition after batch mesh generation

	#-partWeight tri|quad|tet|prism|hex int Weight of a triangle/quad/etc. during partitioning

	renumber_mesh_elements = traits.Bool(argstr='-renumber', desc="Renumber the mesh elements after batch mesh generation")

	save_all_elements = traits.Bool(argstr='-saveall', desc="Save all elements (discard physical group definitions)")

	use_binary_format = traits.Bool(argstr='-bin', desc="Use binary format when available")

	save_vertices_with_parametric_coords = traits.Bool(argstr='-parametric', desc="Save vertices with their parametric coordinates")

	number_of_subdivisions = traits.Bool(argstr='-numsubedges', desc="Set num of subdivisions for high order element display")

	meshing_algorithm = traits.Enum("meshadapt", "del2d", "front2d", "delquad", "del3d", "front3d", "mmg3d",
							argstr="-algo %s", desc="operation to perform")

	smoothing_steps = traits.Int(argstr='-smooth %d', desc="Set number of mesh smoothing steps")
	mesh_order = traits.Int(argstr='-order %d', desc="Set mesh order (1, ..., 5)")

	highorder_optimize = traits.Bool(argstr='-hoOptimize', desc="Optimize high order meshes")

	highorder_element_quality = traits.Float(argstr='-hoMindisto %d', desc="Min high-order element quality before optim (0.0->1.0)")
	highorder_num_layers = traits.Int(argstr='-hoNLayers %d', requires=["highorder_optimize"],
		desc="Number of high order element layers to optimize")
	highorder_elasticity = traits.Float(argstr='-hoElasticity %d', desc="Poisson ration for elasticity analogy (nu in [-1.0,0.5])")

	optimize_netgen = traits.Bool(argstr='-optimize_netgen', desc="Optimize quality of tetrahedral elements")
	optimize_lloyd = traits.Bool(argstr='-optimize_lloyd', desc="Optimize 2D meshes using Lloyd algorithm")
	generate_microstructure = traits.Bool(argstr='-microstructure', desc="Generate polycrystal Voronoi geometry")

	element_size_scaling_factor = traits.Float(argstr='-clscale %d', desc="Set global mesh element size scaling factor")

	min_element_size = traits.Float(argstr='-clmin %d', desc="Set minimum mesh element size")
	max_element_size = traits.Float(argstr='-clmax %d', desc="Set maximum mesh element size")

	max_anisotropy = traits.Float(argstr='-anisoMax %d', desc="Set maximum anisotropy (only used in bamg for now)")

	smoothing_ratio = traits.Float(argstr='-smoothRatio %d', desc="Set smoothing ratio between mesh sizes at nodes of a same edge (only used in bamg)")

	compute_element_sizes_from_curvature = traits.Bool(argstr='-clcurv', desc="Automatically compute element sizes from curvatures")

	accuracy_of_LCFIELD_for_1D_mesh = traits.Bool(argstr='-epslc1d', desc="Set accuracy of evaluation of LCFIELD for 1D mesh")

	'''
	  -swapangle           Set the threshold angle (in degree) between two adjacent faces below which a swap is allowed
	  -rand float          Set random perturbation factor
	'''
	background_mesh_file = File(exists=True, argstr="-bgm %s", desc="Load background mesh from file")

	run_consistency_checks_on_mesh = traits.Bool(argstr='-check', desc="Perform various consistency checks on mesh")
	'''
	  -mpass int           Do several passes on the mesh for complex backround fields
	'''
	ignore_partitions_boundaries = traits.Bool(argstr='-ignorePartBound', desc="Ignore partitions boundaries")

	'''
	Post-processing options:
	  -link int            Select link mode between views (0, 1, 2, 3, 4)
	  combine_views = traits.Bool(argstr='-combine', desc="Combine views having identical names into multi-time-step views")

	Other options:
	  -                    Parse input files, then exit
	'''

	create_new = traits.Bool(argstr='-new', desc="Create new model before merge next file")
	merge_next = traits.Bool(argstr='-merge', desc="Merge next files")
	'''
	  -open                Open next files
	  run_processing = traits.Bool(argstr='-cal', desc="Run processing")
	  -a, -g, -m, -s, -p   Start in automatic, geometry, mesh, solver or post-processing mode
	  -string "string"     Parse option string at startup
	  -option file         Parse option file at startup
	  -convert files       Convert files into latest binary formats, then exit
	'''
	in_files = InputMultiPath(exists=True, argstr="%s", position=-2, mandatory=True)
	output_type = traits.Enum('msh', ['stl', 'msh', 'wrl', 'vrml', 'fs', 'off'], usedefault=True, desc='The output type to save the file as.')
	out_filename = File(genfile=True, argstr="-o %s", position=-1, desc='Specify output file name')

class GmshOutputSpec(TraitedSpec):
    mesh_file = File(exists=True, desc='The output mesh file')

class Gmsh(CommandLine):
    """
    Gmsh, a 3D mesh generator with pre- and post-processing facilities
	Copyright (C) 1997-2013 Christophe Geuzaine and Jean-Francois Remacle

    .. seealso::

    GetDP, MeshFix

    Example
    -------

    >>> from nipype.interfaces.gmsh import Gmsh
    >>> msh = Gmsh()
    >>> msh.inputs.in_files = ['lh-pial.stl']
    >>> msh.run()                                    # doctest: +SKIP
    """
    _cmd = 'gmsh'
    input_spec=GmshInputSpec
    output_spec=GmshOutputSpec

    def _list_outputs(self):
	outputs = self.output_spec().get()
	if isdefined(self.inputs.out_filename):
	    path, name, ext = split_filename(self.inputs.out_filename)
	    ext = ext.replace('.', '')
	    out_types = ['stl', 'msh', 'wrl', 'vrml', 'fs', 'off']
	    # Make sure that the output filename uses one of the possible file types
	    if any(ext == out_type.lower() for out_type in out_types):
			outputs['mesh_file'] = op.abspath(self.inputs.out_filename)
	    else:
			outputs['mesh_file'] = op.abspath(name + '.' + self.inputs.output_type)
	else:
	    outputs['mesh_file'] = op.abspath(self._gen_outfilename())
	return outputs

    def _gen_filename(self, name):
	if name is 'out_filename':
	    return self._gen_outfilename()
	else:
	    return None
    def _gen_outfilename(self):
	_, name , _ = split_filename(self.inputs.in_files[0])
	return name + '_gmsh.' + self.inputs.output_type
