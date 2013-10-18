from nipype.interfaces.base import (CommandLine, CommandLineInputSpec,
				    traits, TraitedSpec, isdefined,
				    File)
import os, os.path as op
from nipype.utils.filemanip import split_filename

class GetDPInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr="%s", position=1, mandatory=True)

    ## Processing options
    mesh_file = File(exists=True, argstr="-msh %s", desc="Read mesh (in Gmsh .msh format) from file")
    adapatation_constraint_file = File(exists=True, argstr="-adapt %s", desc="Read adaptation constraints from file")
    results_file = File(exists=True, argstr="-res %s", desc="Load processing results from file(s)")

    preprocessing_type = traits.String(argstr="-pre %s", desc="Pre-processing")
    run_processing = traits.Bool(argstr='-cal', desc="Run processing")
    postprocessing_type = traits.String(argstr="-post %s", desc="Post-processing")
    save_results_separately = traits.Bool(argstr='-split', desc="Save processing results in separate files")
    restart_processing = traits.Bool(argstr='-restart', desc="Resume processing from where it stopped")

    #Worth keeping?
    solve = traits.String(argstr="-solve %s", desc="Solve (same as -pre 'Resolution' -cal)")

    output_name = traits.String("getdp", argstr="-name %s", usedefault=True, 
      desc="Generic file name")

    maximum_interpolation_order = traits.Int(argstr='-order %d',
      desc="Restrict maximum interpolation order")

    ## Linear solver options
    binary_output_files = traits.Bool(argstr='-bin', desc="Create binary output files")
    mesh_based_output_files = traits.Bool(argstr='-v2', desc="Create mesh-based Gmsh output files when possible")

    out_filename = File(genfile=True, argstr="-o %s", desc='The output filename for the fixed mesh file')

class GetDPOutputSpec(TraitedSpec):
    mesh_file = File(exists=True, desc='The output mesh file')

class GetDP(CommandLine):
    """
    GetDP, a General environment for the treatment of Discrete Problems
    Copyright (C) 1997-2012 P. Dular, C. Geuzaine

    .. seealso::

    Gmsh

    Example
    -------

    >>> from nipype.interfaces.getdp import GetDP
    >>> solve = GetDP()
    >>> solve.inputs.in_file = 'lh-pial.pre'
    >>> solve.run()                                    # doctest: +SKIP
    """
    _cmd = 'getdp'
    input_spec=GetDPInputSpec
    output_spec=GetDPOutputSpec

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
      	_, name , _ = split_filename(self.inputs.in_file1)
      	if self.inputs.save_as_freesurfer_mesh or self.inputs.output_type == 'fs':
      	    self.inputs.output_type = 'fs'
      	    self.inputs.save_as_freesurfer_mesh = True
      	if self.inputs.save_as_stl or self.inputs.output_type == 'stl':
      	    self.inputs.output_type = 'stl'
      	    self.inputs.save_as_stl = True
      	if self.inputs.save_as_vmrl or self.inputs.output_type == 'vmrl':
      	    self.inputs.output_type = 'vmrl'
      	    self.inputs.save_as_vmrl = True
      	return name + '_fixed.' + self.inputs.output_type
