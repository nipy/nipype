# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 4.1.4.

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)
"""

import os, os.path as op
from glob import glob
import warnings
from shutil import rmtree

import numpy as np

from nipype.interfaces.fsl.base import (FSLCommand, FSLCommandInputSpec)
from nipype.interfaces.base import (load_template, File, traits, isdefined,
                                    TraitedSpec, BaseInterface, Directory,
                                    InputMultiPath, OutputMultiPath,
                                    BaseInterfaceInputSpec)
from nipype.utils.filemanip import (list_to_filename, filename_to_list,
                                    split_filename)
from nibabel import load

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

class FIRSTInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, mandatory=True, position=-2,
                  argstr='-i %s',
                  desc='input data file')
    out_file = File('segmented', usedefault=True, mandatory=True, position=-1,
                  argstr='-o %s',
                  desc='output data file')
    verbose = traits.Bool(argstr='-v', position=1,
        desc="Use verbose logging.")
    brain_extracted = traits.Bool(argstr='-b', position=2,
        desc="Input structural image is already brain-extracted")
    no_cleanup = traits.Bool(argstr='-d', position=3,
        desc="Input structural image is already brain-extracted")
    method = traits.Enum('auto','fast','none', argstr='-m', position=4,
        desc="Method must be one of auto, fast, none, or a numerical threshold value")
    method_as_numerical_threshold = traits.Float(argstr='-m', position=4,
        desc="Method must be one of auto, fast, none, or a numerical threshold value")
    list_of_specific_structures = traits.List(traits.Str, argstr='-s %s', sep=',',
        position=5, minlen=1, 
        desc='Runs only on the specified structures (e.g. L_Hipp)')
    affine_file = File(exists=True, position=6,
                  argstr='-a %s',
                  desc='Affine matrix to use (e.g. img2std.mat) (does not re-run registration)')

class FIRSTOutputSpec(TraitedSpec):
    vtk_surfaces = OutputMultiPath(File(exists=True),
          desc='VTK format meshes for each subcortical region')
    bvars = OutputMultiPath(File(exists=True),
          desc='bvars for each subcortical region')
    original_segmentations = File(exists=True,
          desc='4D image file containing a single image per segmented region')
    segmentation_file = File(exists=True,
          desc='4D image file containing a single image per segmented region')

class FIRST(FSLCommand):
    """Use FSL's run_first_all command to segment subcortical volumes

    Examples
    --------

    >>> from nipype.interfaces import fsl
    >>> first = fsl.FIRST()
    >>> first.inputs.in_file = 'struct.nii'
    >>> first.inputs.out_file = 'segmented.nii'
    >>> res = first.run() #doctest: +SKIP

    """

    _cmd = 'run_first_all'
    input_spec = FIRSTInputSpec
    output_spec = FIRSTOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        
        if isdefined(self.inputs.list_of_specific_structures):
            structures = self.inputs.list_of_specific_structures
        else:
            structures = ['L_Hipp', 'R_Hipp',
                          'L_Accu', 'R_Accu',
                          'L_Amyg', 'R_Amyg',
                          'L_Caud', 'R_Caud',
                          'L_Pall', 'R_Pall',
                          'L_Puta', 'R_Puta',
                          'L_Thal', 'R_Thal',
                          'BrStem']
        print structures
        outputs['original_segmentations'] = self._gen_fname('original_segmentations')
        outputs['segmentation_file'] = self._gen_fname('segmentation_file')
        outputs['vtk_surfaces'] = self._gen_mesh_names('vtk_surfaces', structures)
        outputs['bvars'] = self._gen_mesh_names('bvars', structures)
        return outputs
        
    def _gen_fname(self, name):
        print name
        if name == 'original_segmentations':
            path, name, ext = split_filename(self.inputs.out_file)
            return op.abspath(name + '_all_fast_origsegs.nii.gz')
        if name == 'segmentation_file':
            path, name, ext = split_filename(self.inputs.out_file)
            return op.abspath(name + '_all_fast_firstseg.nii.gz')
        return None

    def _gen_mesh_names(self, name, structures):
        print name
        path, prefix, ext = split_filename(self.inputs.out_file)
        if name == 'vtk_surfaces':
            vtks = list()
            for struct in structures:
                vtk =  prefix + '-' + struct + '_first.vtk'
                print vtk
            vtks.append(op.abspath(vtk))
            return vtks
        if name == 'bvars':
            bvars = list()
            for struct in structures:
                bvar = prefix + '-' + struct + '_first.bvars'
                print bvar
            bvars.append(op.abspath(bvar))
            return bvars
        return None
