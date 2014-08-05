# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    The gif module provides higher-level interfaces to some of the operations
    that can be performed with the niftyseggif (seg_gif) command-line program.
"""
import os
import numpy as np
from nibabel import load
import os.path as op
import warnings
import glob

from nipype.interfaces.niftyseg.base import NIFTYSEGCommandInputSpec, NIFTYSEGCommand
from nipype.interfaces.base import (TraitedSpec, File, Directory, traits, InputMultiPath,
                                    isdefined)


warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

class GifInputSpec(NIFTYSEGCommandInputSpec):
    
    in_file = File(argstr='-in %s', exists=True, mandatory=True,
                desc='Input target image filename')
    
    database_file = File(argstr='-db %s', exists=True, 
                         mandatory=True,
                         desc='Path to database <XML> file')    

    cpp_dir = Directory(exists=True, mandatory=True, argstr='-cpp %s', 
                        desc='Folder to read/store cpp files.')

    mask_file = File(exists=True, argstr='-mask %s', 
                     desc='Mask over the input image [default: none]')

    out_dir = Directory(exists=True, argstr='-out %s', 
                        desc='Output folder [default: ./]')

    
    lssd_ker = traits.Float(argstr = '-lssd_ker %f',
                            desc='SSD kernel stdev in voxels (mm if negative) [-2.5]')
    ldef_ker = traits.Float(argstr = '-ldef_ker %f',
                            desc='DEF kernel stdev in voxels (mm if negative) [-2.5]')
    lncc_ker = traits.Float(argstr = '-lncc_ker %f',
                            desc='NCC kernel stdev in voxels (mm if negative) [-2.5]')
    t1dti_ker = traits.Float(argstr = '-t1dti_ker %f',
                             desc='T1DTI kernel stdev in voxels (mm if negative) [-2.5]')
    lssd_weig = traits.Float(argstr = '-lssd_weig %f',
                             desc='SSD distance weight <float> [0.0]')
    ldef_weig = traits.Float(argstr = '-ldef_weig %f',
                             desc='DEF distance weight <float> [0.0]')
    lncc_weig = traits.Float(argstr = '-lncc_weig %f',
                             desc='NCC distance weight <float> [1.0]')
    t1dti_weig = traits.Float(argstr = '-t1dti_weig %f',
                              desc='T1DTI distance weight <float> [0.0]')
    temper = traits.Float(argstr = '-temper %f',
                          desc='Kernel emperature <float> [0.15]')
    sort_beta = traits.Float(argstr = '-sort_beta %f',
                             desc='The beta scaling factor (defined in xml) [0.5]')
    sort_numb = traits.Int(argstr = '-sort_numb %d', 
                           desc='The number of elements in the sort (defined in xml) [7]')
    regNMI = traits.Bool(argstr = 'regNMI',
                         desc='Ust NMI as a registration similarity, instead of LNCC')
    regBE = traits.Float(argstr = '-regBE %f',
                         desc='Bending energy value for the registration [0.005]')
    regJL = traits.Float(argstr = '-regJL %f',
                         desc='Jacobian log value for the registration [0.0001]')
    regSL = traits.Bool(argstr = '-regSL',
                         desc='Skip the second Level non-rigid registration')
    

class GifOutputSpec(TraitedSpec):

    out_dir    = Directory(desc='Output folder [default: ./]')    
    parc_file  = File(genfile=True, desc='Parcellation file')
    geo_file   = File(genfile=True, desc='Geodesic distance file')
    prior_file = File(genfile=True, desc='Prior file')
    synth_file = File(genfile=True, desc='Synthetic file')

class Gif(NIFTYSEGCommand):


    """

    GIF Propagation :
    Usage -> seg_GIF <mandatory> <options>
    
    
    * * * * * * * * * * * Mandatory * * * * * * * * * * * * * * * * * * * * * * *
    
    -in <filename>	| Input target image filename
    -db <XML>   	| Path to database <XML> file
    -cpp <cpp_path>	| Folder to read/store cpp files.
    
    * * * * * * * * * * * General Options * * * * * * * * * * * * * * * * * * * *
    
    -mask <filename>	| Mask over the input image
    -out <path> 	| Output folder [./]

    Examples
    --------
    from nipype.interfaces.niftyseg import Gif
    seggif = Gif()
    seggif.inputs.in_file = "T1.nii.gz"
    seggif.inputs.database_file = "db.xml"
    seggif.inputs.cpp_dir = "cpps"
    seggif.inputs.out_dir = "outputs"
    seggif.cmdline
    seg_GIF -in T1.nii.gz -cpp cpps -out outputs

    """

    _cmd = 'seg_GIF'
    input_spec = GifInputSpec  
    output_spec = GifOutputSpec

    def _get_basename_without_extension(self, in_file):
        ret = os.path.basename(in_file)
        ret = ret.replace('.nii.gz', '')
        ret = ret.replace('.nii', '')
        return ret
        
    def _find_file_from_patterns(directory, begin_pattern, end_pattern):
        list_of_files = glob.glob(directory + os.sep + begin_pattern + '*' + end_pattern)
        if len(list_of_files) != 1:
            return None
        else:
            return list_of_files[0]

    def _list_outputs(self):
        outputs = self.output_spec().get()

        if isdefined(self.inputs.out_dir) and self.inputs.out_dir:
            outputs['out_dir'] = os.path.abspath(self.inputs.out_dir)
        else:
            outputs['out_dir'] = os.getcwd()
 
        basename = self._get_basename_without_extension(self.inputs.in_file)
        
        outputs['parc_file']   = self._find_file_from_patterns(outputs['out_dir'], basename, 'Parcellation.nii.gz')
        outputs['geo_file']    = self._find_file_from_patterns(outputs['out_dir'], basename, 'geo.nii.gz')
        outputs['prior_file']  = self._find_file_from_patterns(outputs['out_dir'], basename, 'prior.nii.gz')        
        outputs['synth_file']  = self._find_file_from_patterns(outputs['out_dir'], basename, 'synth.nii.gz')
        
#        outputs['parc_file']   = os.path.join (outputs['out_dir'], basename + '_labels_Parcellation.nii.gz')
#        outputs['geo_file']    = os.path.join (outputs['out_dir'], basename + '_labels_geo.nii.gz')
#        outputs['prior_file']  = os.path.join (outputs['out_dir'], basename + '_labels_prior.nii.gz')        

        return outputs
        
