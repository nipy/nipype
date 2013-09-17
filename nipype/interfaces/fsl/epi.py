# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 5.0.4.

Examples
--------
See the docstrings of the individual classes for examples.

"""

import os
from glob import glob
import warnings

import numpy as np

from nipype.interfaces.fsl.base import FSLCommand, FSLCommandInputSpec, Info
from nipype.interfaces.base import (traits, TraitedSpec, OutputMultiPath, File,
                                    isdefined)


from nipype.utils.filemanip import load_json, save_json, split_filename, fname_presuffix

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class PrepareFieldmapInputSpec(FSLCommandInputSpec):
    scanner = traits.String('SIEMENS', argstr='%s', position=1, desc='must be SIEMENS', usedefault=True)
    in_phase = File( exists=True, argstr='%s', position=2, mandatory=True,
                     desc='Phase difference map, in SIEMENS format range from 0-4096 or 0-8192 )' )
    in_magnitude = File(exists=True, argstr='%s', position=3, mandatory=True,
                        desc='Magnitude difference map, brain extracted')
    delta_TE = traits.Float(2.46, usedefault=True, mandatory=True, argstr='%f', position=-2,
                            desc='echo time difference of the fielmap sequence in ms. (usually 2.46ms in Siemens)')
                            
    nocheck = traits.Bool(False, position=-1, argstr='--nocheck',usedefault=True,
                          desc='do not perform sanity checks for image size/range/dimensions')
    out_fieldmap = File( argstr='%s', position=5, desc='output name for prepared fieldmap' )


class PrepareFieldmapOutputSpec( TraitedSpec ):
    out_fieldmap = File( exists=True, desc='output name for prepared fieldmap' )

class PrepareFieldmap(FSLCommand):
    """ Interface for the fsl_prepare_fieldmap script (FSL 5.0)

    Prepares a fieldmap suitable for FEAT from SIEMENS data - saves output in rad/s format
    e.g. fsl_prepare_fieldmap SIEMENS images_3_gre_field_mapping images_4_gre_field_mapping fmap_rads 2.65


    Examples
    --------
    >>> prepare = PrepareFieldmap()
    >>> prepare.inputs.in_phase = "phase.nii"
    >>> prepare.inputs.in_magnitude = "magnitude.nii"
    >>> res = prepare.run() # doctest: +SKIP


    """
    _cmd = 'fsl_prepare_fieldmap'
    input_spec = PrepareFieldmapInputSpec
    output_spec = PrepareFieldmapOutputSpec

    def _parse_inputs( self, skip=None ):
        if skip is None:
            skip = []
        
        if not isdefined(self.inputs.out_fieldmap ):
            self.inputs.out_fieldmap = self._gen_fname(
                self.inputs.in_phase, suffix='_fslprepared' )

        if not isdefined(self.inputs.nocheck ) or not self.inputs.nocheck:
            skip += ['nocheck']

        return super(PrepareFieldmap, self)._parse_inputs(skip=skip)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_fieldmap'] = self.inputs.out_fieldmap
        return outputs



class TOPUPInputSpec( FSLCommandInputSpec ):
    in_file = File( exists=True, mandatory=True, desc='name of 4D file with images', argstr='--imain %s' )
    encoding_file = File( exists=True, mandatory=True, desc='name of text file with PE directions/times', argstr='--datain %s' )
    out_base = File( desc='base-name of output files (spline coefficients (Hz) and movement parameters)', argstr='--out %s' )
    out_field = File( argstr='--fout %s', desc='name of image file with field (Hz)' )
    out_corrected = File( argstr='--iout %s', desc='name of 4D image file with unwarped images' )
    out_logfile = File( argstr='--logout %s', desc='name of log-file' )
    warp_res = traits.Float( 10.0, argstr='--warpres %f', desc='(approximate) resolution (in mm) of warp basis for the different sub-sampling levels' )
    subsamp = traits.Int( 1, argstr='--subsamp %d', desc='sub-sampling scheme, default 1' )
    fwhm = traits.Float( 8.0, argstr='--fwhm %f', desc='FWHM (in mm) of gaussian smoothing kernel' )
    config = traits.String('b02b0.cnf', desc='Name of config file specifying command line arguments', argstr='--config %s', usedefault=True )
    max_iter = traits.Int( 5, argstr='--miter %d', desc='max # of non-linear iterations')
    #lambda	Weight of regularisation, default depending on --ssqlambda and --regmod switches. See user documetation.
    #ssqlambda	If set (=1), lambda is weighted by current ssq, default 1
    #regmod	Model for regularisation of warp-field [membrane_energy bending_energy], default bending_energy
    estmov = traits.Enum( 1, 0, desc='estimate movements if set', argstr='--estmov %d' )
    minmet = traits.Enum( 0, 1, desc='Minimisation method 0=Levenberg-Marquardt, 1=Scaled Conjugate Gradient', argstr='--minmet %d' )
    splineorder = traits.Int( 3, argstr='--splineorder %d', desc='order of spline, 2->Qadratic spline, 3->Cubic spline' )
    numprec = traits.Enum( 'double', 'float', argstr='--numprec %s', desc='Precision for representing Hessian, double or float.' )
    interp = traits.Enum( 'spline', 'linear' , argstr='--interp %s', desc='Image interpolation model, linear or spline.' )
    scale = traits.Enum( 0, 1, argstr='--scale %d', desc='If set (=1), the images are individually scaled to a common mean' )
    regrid = traits.Enum( 1, 0, argstr='--regrid %d', desc='If set (=1), the calculations are done in a different grid' )

class TOPUPOutputSpec( TraitedSpec ):
    out_fieldcoef = File( exists=True, desc='file containing the field coefficients' )
    out_movpar = File( exists=True, desc='movpar.txt output file' )

    out_topup = File( desc='basename for the <out_base>_fieldcoef.nii.gz and <out_base>_movpar.txt files' )
    out_field = File( desc='name of image file with field (Hz)' )
    out_corrected = File( desc='name of 4D image file with unwarped images' )
    out_logfile = File( desc='name of log-file' )

class TOPUP( FSLCommand ):
    """ Interface for FSL topup, a tool for estimating and correcting susceptibility induced distortions
        Reference: http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/TOPUP
        Example: http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/topup/ExampleTopupFollowedByApplytopup

        topup --imain=<some 4D image> --datain=<text file> --config=<text file with parameters> --coutname=my_field


        Examples
        --------
        >>> topup = TOPUP()
        >>> topup.inputs.in_file = "b0_b0rev.nii"
        >>> topup.inputs.encoding_file = "topup_encoding.txt"
        >>> res = topup.run() # doctest: +SKIP

    """
    _cmd = 'topup'
    input_spec = TOPUPInputSpec
    output_spec = TOPUPOutputSpec

    def _parse_inputs( self, skip=None ):
        if skip is None:
            skip = []
        
        if not isdefined(self.inputs.out_base ):
            self.inputs.out_base = os.path.abspath( './nipype_topup' )

        return super(TOPUP, self)._parse_inputs(skip=skip)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_topup'] = self.inputs.out_base
        outputs['out_fieldcoef'] = '%s_%s.nii.gz' % (self.inputs.out_base, 'fieldcoef' )
        outputs['out_movpar'] = '%s_%s.txt' % (self.inputs.out_base, 'movpar' )

        if isdefined( self.inputs.out_field ):
            outputs['out_field'] = self.inputs.out_field
        else:
            outputs['out_field'] = None

        if isdefined( self.inputs.out_corrected ):
            outputs['out_corrected'] = self.inputs.out_corrected
        else:
            outputs['out_corrected'] = None

        if isdefined( self.inputs.out_logfile ):
            outputs['out_logfile'] = self.inputs.out_logfile
        else:
            outputs['out_logfile'] = None

        return outputs
 
# class ApplyTOPUPInputSpec( FSLCommandInputSpec ):
# 	in_file = File( exists=True, mandatory=True, desc='name of 4D file with images', argstr='--imain %s' )
# 	encoding_file = File( exists=True, mandatory=True, desc='name of text file with PE directions/times', argstr='--datain %s' )
#     in_index = traits.List( argstr='-x %s', mandatory=True, desc='comma separated list of indicies into --datain of the input image (to be corrected)' )
#     in_topup = File( mandatory=True, desc='basename of field/movements (from topup)', argstr='-t %s' )
#     
#     out_base = File( desc='basename for output (warped) image', argstr='-o %s' )
#     method = traits.Enum( ('jac','lsr'), argstr='-m %s', desc='use jacobian modulation (jac) or least-squares resampling (lsr)' )
#     interp = traits.Enum( ('trilinear','spline'), argstr='-n %s', desc='interpolation method' )
#     datatype = traits.Enum( ('char', 'short', 'int', 'float', 'double' ), argstr='-d %s', desc='force output data type' )
# 
# 
# class ApplyTOPUPOutputSpec( TraitedSpec ):
#     out_corrected = File( argstr='--iout %s', desc='name of 4D image file with unwarped images' )
#     out_logfile = File( argstr='--logout %s', desc='name of log-file' )
# 
# class ApplyTOPUP( FSLCommand ):
#     """ Interface for FSL topup, a tool for estimating and correcting susceptibility induced distortions
#         Reference: http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/topup/ApplytopupUsersGuide
#         Example: http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/topup/ExampleTopupFollowedByApplytopup
# 
#         topup --imain=<some 4D image> --datain=<text file> --config=<text file with parameters> --coutname=my_field
# 
# 
#         Examples
#         --------
#         >>> applytopup = ApplyTOPUP()
#         >>> applytopup.inputs.in_file = "dwi_combined.nii"
#         >>> applytopup.inputs.encoding_file = "encoding.txt"
#         >>> applytopup.inputs.in_index = 1,2
#         >>> applytopup.inputs.in_topup = "my_topup_results"
#         >>> res = applytopup.run() # doctest: +SKIP
# 
#     """
#     _cmd = 'topup'
#     input_spec = ApplyTOPUPInputSpec
#     output_spec = ApplyTOPUPOutputSpec
# 
#     def _list_outputs(self):
#         outputs = self.output_spec().get()
# 
#         return outputs
# 
# 
# 
# 


class EPIDeWarpInputSpec(FSLCommandInputSpec):
    mag_file = File(exists=True,
                    desc='Magnitude file',
                    argstr='--mag %s', position=0, mandatory=True)
    dph_file = File(exists=True,
                    desc='Phase file assumed to be scaled from 0 to 4095',
                    argstr='--dph %s', mandatory=True)
    exf_file = File(exists=True,
                    desc='example func volume (or use epi)',
                    argstr='--exf %s', mandatory=False)
    epi_file = File(exists=True,
                    desc='EPI volume to unwarp',
                    argstr='--epi %s', mandatory=False)
    tediff = traits.Float(2.46, usedefault=True,
                          desc='difference in B0 field map TEs',
                          argstr='--tediff %s')
    esp = traits.Float(0.58, desc='EPI echo spacing',
                       argstr='--esp %s', usedefault=True)
    sigma = traits.Int(2, usedefault=True, argstr='--sigma %s',
                       desc="2D spatial gaussing smoothing \
                       stdev (default = 2mm)")
    vsm = traits.String(genfile=True, desc='voxel shift map',
                        argstr='--vsm %s')
    exfdw = traits.String(desc='dewarped example func volume', genfile=True,
                          argstr='--exfdw %s')
    epidw = traits.String(desc='dewarped epi volume', genfile=False,
                          argstr='--epidw %s')
    tmpdir = traits.String(genfile=True, desc='tmpdir',
                           argstr='--tmpdir %s')
    nocleanup = traits.Bool(True, usedefault=True, desc='no cleanup',
                            argstr='--nocleanup')
    cleanup = traits.Bool(desc='cleanup',
                          argstr='--cleanup')



class EPIDeWarpOutputSpec(TraitedSpec):
    unwarped_file = File(desc="unwarped epi file")
    vsm_file = File(desc="voxel shift map")
    exfdw = File(desc="dewarped functional volume example")
    exf_mask = File(desc="Mask from example functional volume")


class EPIDeWarp(FSLCommand):
    """Wraps fieldmap unwarping script from Freesurfer's epidewarp.fsl_

    Examples
    --------
    >>> dewarp = EPIDeWarp()
    >>> dewarp.inputs.epi_file = "functional.nii"
    >>> dewarp.inputs.mag_file = "magnitude.nii"
    >>> dewarp.inputs.dph_file = "phase.nii"
    >>> res = dewarp.run() # doctest: +SKIP

    References
    ----------
    _epidewarp.fsl: http://surfer.nmr.mgh.harvard.edu/fswiki/epidewarp.fsl

    """

    _cmd = 'epidewarp.fsl'
    input_spec = EPIDeWarpInputSpec
    output_spec = EPIDeWarpOutputSpec

    def _gen_filename(self, name):
        if name == 'exfdw':
            if isdefined(self.inputs.exf_file):
                return self._gen_fname(self.inputs.exf_file,
                                       suffix="_exfdw")
            else:
                return self._gen_fname("exfdw")
        if name == 'epidw':
            if isdefined(self.inputs.epi_file):
                return self._gen_fname(self.inputs.epi_file,
                                       suffix="_epidw")
        if name == 'vsm':
            return self._gen_fname('vsm')
        if name == 'tmpdir':
            return os.path.join(os.getcwd(), 'temp')
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.exfdw):
            outputs['exfdw'] = self._gen_filename('exfdw')
        else:
            outputs['exfdw'] = self.inputs.exfdw
        if isdefined(self.inputs.epi_file):
            if isdefined(self.inputs.epidw):
                outputs['unwarped_file'] = self.inputs.epidw
            else:
                outputs['unwarped_file'] = self._gen_filename('epidw')
        if not isdefined(self.inputs.vsm):
            outputs['vsm_file'] = self._gen_filename('vsm')
        else:
            outputs['vsm_file'] = self._gen_fname(self.inputs.vsm)
        if not isdefined(self.inputs.tmpdir):
            outputs[
                'exf_mask'] = self._gen_fname(cwd=self._gen_filename('tmpdir'),
                                              basename='maskexf')
        else:
            outputs['exf_mask'] = self._gen_fname(cwd=self.inputs.tmpdir,
                                                  basename='maskexf')
        return outputs


class SigLossInputSpec(FSLCommandInputSpec):
    in_file = File(mandatory=True,
                   exists=True,
                   argstr='-i %s',
                   desc='b0 fieldmap file')
    out_file = File(argstr='-s %s',
                    desc='output signal loss estimate file',
                    genfile=True)
    
    mask_file = File(exists=True,
                     argstr='-m %s',
                     desc='brain mask file')
    echo_time = traits.Float(argstr='--te=%f',
                             desc='echo time in seconds')
    slice_direction = traits.Enum('x','y','z',
                                  argstr='-d %s',
                                  desc='slicing direction')
class SigLossOuputSpec(TraitedSpec):
    out_file = File(exists=True,
                    desc='signal loss estimate file')

class SigLoss(FSLCommand):
    """Estimates signal loss from a field map (in rad/s)

    Examples
    --------
    >>> sigloss = SigLoss()
    >>> sigloss.inputs.in_file = "phase.nii"
    >>> sigloss.inputs.echo_time = 0.03
    >>> res = sigloss.run() # doctest: +SKIP
    """
    input_spec = SigLossInputSpec
    output_spec = SigLossOuputSpec
    _cmd = 'sigloss'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(outputs['out_file']) and isdefined(self.inputs.in_file):
            outputs['out_file']=self._gen_fname(self.inputs.in_file,
                                                suffix='_sigloss')
        return outputs
    
    def _gen_filename(self, name):
        if name=='out_file':
            return self._list_outputs()['out_file']
        return None
    
class EddyCorrectInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, desc='4D input file', argstr='%s', position=0, mandatory=True)
    out_file = File(desc='4D output file', argstr='%s', position=1, genfile=True, hash_files=False)
    ref_num = traits.Int(argstr='%d', position=2, desc='reference number', mandatory=True)


class EddyCorrectOutputSpec(TraitedSpec):
    eddy_corrected = File(exists=True, desc='path/name of 4D eddy corrected output file')


class EddyCorrect(FSLCommand):
    """  Deprecated! Please use create_eddy_correct_pipeline instead

    Example
    -------

    >>> from nipype.interfaces import fsl
    >>> eddyc = fsl.EddyCorrect(in_file='diffusion.nii', out_file="diffusion_edc.nii", ref_num=0)
    >>> eddyc.cmdline
    'eddy_correct diffusion.nii diffusion_edc.nii 0'

    """
    _cmd = 'eddy_correct'
    input_spec = EddyCorrectInputSpec
    output_spec = EddyCorrectOutputSpec

    def __init__(self, **inputs):
        warnings.warn("Deprecated: Please use create_eddy_correct_pipeline instead", DeprecationWarning)
        return super(EddyCorrect, self).__init__(**inputs)

    def _run_interface(self, runtime):
        if not isdefined(self.inputs.out_file):
            self.inputs.out_file = self._gen_fname(self.inputs.in_file, suffix='_edc')
        runtime = super(EddyCorrect, self)._run_interface(runtime)
        if runtime.stderr:
            self.raise_exception(runtime)
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['eddy_corrected'] = self.inputs.out_file
        if not isdefined(outputs['eddy_corrected']):
            outputs['eddy_corrected'] = self._gen_fname(self.inputs.in_file, suffix='_edc')
        outputs['eddy_corrected'] = os.path.abspath(outputs['eddy_corrected'])
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._list_outputs()['eddy_corrected']
        else:
            return None



