"""The freesurfer module provides basic functions for interfacing with freesurfer tools.

Currently these tools are supported:

     * Dicom2Nifti: using mri_convert
     * Resample: using mri_convert
     
Examples
--------
See the docstrings for the individual classes for 'working' examples.

"""
__docformat__ = 'restructuredtext'

import os
from glob import glob

from nipype.interfaces.base import Bunch
from nipype.utils.docparse import get_doc
from nipype.utils.filemanip import fname_presuffix, FileNotFoundError
from nipype.interfaces.io import FreeSurferSource
from nipype.interfaces.freesurfer import FSCommand

from nipype.interfaces.freesurfer.base import NEW_FSCommand, FSTraitedSpec
from nipype.interfaces.base import Bunch, TraitedSpec, File, traits
from nipype.utils.misc import isdefined

class Resample(FSCommand):
    """Use FreeSurfer mri_convert to up or down-sample image files

    Parameters
    ----------
    To see optional arguments
    Resample().inputs_help()


    Examples
    --------
    >>> from nipype.interfaces import freesurfer
    >>> resampler = freesurfer.Resample()
    >>> resampler.inputs.infile = 'infile.nii'
    >>> resampler.inputs.voxel_size = [2.1, 2.1, 2.1]
    >>> resampler.cmdline
    'mri_convert -i infile.nii -vs 2.10 2.10 2.10 -o infile_resample.nii'
    
   """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'mri_convert'

    def inputs_help(self):
        """Print command line documentation for bbregister."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    opt_map = {
        'infile':         '-i %s',
        'outfile':        '-o %s',
        'voxel_size':     '-vs %.2f %.2f %.2f', 
        'flags':           '%s'}
    
    def _parse_inputs(self):
        """validate fs bbregister options"""
        allargs = super(Resample, self)._parse_inputs()

        # Add outfile to the args if not specified
        if self.inputs.outfile is None:
            allargs.extend(['-o', fname_presuffix(self.inputs.infile,
                                                   suffix='_resample')])
        return allargs
    
    def outputs(self):
        """
        outfile: filename
            Smoothed input volume
        """
        return Bunch(outfile=None)

    def aggregate_outputs(self):
        outputs = self.outputs()
        if self.inputs.outfile is None:
            outfile = glob(fname_presuffix(self.inputs.infile,
                                           suffix='_resample'))
        if isinstance(self.inputs.outfile,str):
            outfile = glob(self.inputs.outfile)
        if not outfile:
            raise FileNotFoundError(outfile)
        outputs.outfile = outfile[0]
        return outputs

class ReconAll(FSCommand):
    """Use FreeSurfer recon-all to generate surfaces and parcellations of
    structural data from an anatomical image of a subject.

    Parameters
    ----------

    To see optional arguments
    ReconAll().inputs_help()


    Examples
    --------
    >>> from nipype.interfaces import freesurfer
    >>> reconall = freesurfer.ReconAll()
    >>> reconall.inputs.subject_id = 'foo'
    >>> reconall.inputs.all  = True
    >>> reconall.inputs.subjects_dir = '.'
    >>> reconall.inputs.T1file = 'structfile.nii'
    >>> reconall.cmdline
    'recon-all --i structfile.nii --all -subjid foo -sd .'
    
   """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'recon-all'

    def inputs_help(self):
        """Print command line documentation for bbregister."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    opt_map = {
        'subject_id':         '-subjid %s',
        'all':                '--all',
        'T1file':             '--i %s',
        'hemi':               '-hemi %s',
        'subjects_dir':       '-sd %s',
        'flags':              '%s'}
    
    def outputs(self):
        """
        See io.FreeSurferSource.outputs for the list of outputs returned
        """
        return FreeSurferSource().outputs()

    def aggregate_outputs(self):
        return FreeSurferSource(subject_id=self.inputs.subject_id,
                                subjects_dir=self.inputs.subjects_dir).aggregate_outputs()

class BBRegisterInputSpec(FSTraitedSpec):
    subject_id = traits.Str(argstr='--s %s', desc='freesurfer subject id',
                            mandatory=True)
    sourcefile = File(argstr='--mov %s', desc='source file to be registered',
                      mandatory=True)
    init_reg = traits.Either(traits.Enum('spm', 'fsl', 'header'),
                              File(exists=True),argstr = '',
                       desc='initialize registration spm, fsl, header or existing File',
                              mandatory=True,)
    contrast_type = traits.Enum('t1', 't2', argstr='--%s',
                                desc='contrast type of image', mandatory=True)
    outregfile = File(argstr='--reg %s', desc='output registration file',
                      genfile=True)
    outfile = traits.Either(traits.Bool, File, argstr='--o %s',
                            desc='output warped sourcefile either True or filename')
    flags = traits.Str(argstr='%s', desc='any additional flags')

class BBRegisterOutputSpec(TraitedSpec):
    outregfile = File(exists=True, desc='Output registration file')
    outfile = File(desc='Registered and resampled source file')

class BBRegister(NEW_FSCommand):
    """Use FreeSurfer bbregister to register a volume two a surface mesh

    This program performs within-subject, cross-modal registration using a
    boundary-based cost function. The registration is constrained to be 6
    DOF (rigid). It is required that you have an anatomical scan of the
    subject that has been analyzed in freesurfer.

    Parameters
    ----------

    To see optional arguments
    BBRegister().inputs_help()


    Examples
    --------
    >>> from nipype.interfaces.freesurfer import BBRegister
    >>> bbreg = BBRegister(subject_id='me', sourcefile='foo.nii', init_header=True, t2_contrast=True)
    >>> bbreg.cmdline
    'bbregister --init-header --mov foo.nii --s me --t2 --reg foo_bbreg_me.dat'

   """

    _cmd = 'bbregister'
    input_spec = BBRegisterInputSpec
    output_spec =  BBRegisterOutputSpec
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['outregfile'] = self.inputs.outregfile
        if not isdefined(self.inputs.outregfile) and self.inputs.sourcefile:
            outputs['outregfile'] = fname_presuffix(self.inputs.sourcefile,
                                         suffix='_bbreg_%s.dat'%self.inputs.subject_id,
                                         use_ext=False)
        outputs['outfile'] = self.inputs.outfile
        if isinstance(self.inputs.outfile, bool):
            outputs['outfile'] = fname_presuffix(self.inputs.sourcefile,suffix='_bbreg')
        return outputs

    def _format_arg(self, name, spec, value):
        if name == 'outfile':
            if isinstance(value, bool):
                fname = self._list_outputs()[name]
            else:
                fname = value
            return '--o %s' % fname
        if name == 'init_reg':
            if os.path.isfile(value):
                return '--init-reg %s' % value
            else:
                return '--init-%s' % value
        return super(BBRegister, self)._format_arg(name, spec, value)
    
    def _gen_filename(self, name):
        if name == 'outregfile':
            return self._list_outputs()[name]
        return None    

class ApplyVolTransform(FSCommand):
    """Use FreeSurfer mri_vol2vol to apply a transform.

    Parameters
    ----------
    To see optional arguments
    ApplyVolTransform().inputs_help()

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import ApplyVolTransform
    >>> applyreg = ApplyVolTransform(tkreg='me.dat', sourcefile='foo.nii', fstarg=True)
    >>> applyreg.cmdline
    'mri_vol2vol --fstarg --mov foo.nii --reg me.dat --o foo_warped.nii'

    """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'mri_vol2vol'

    def inputs_help(self):
        """Print command line documentation for mri_vol2vol."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    opt_map = {
        'sourcefile':         '--mov %s',
        'targfile':           '--targ %s',
        'outfile':            '--o %s',
        'fstarg':             '--fstarg',
        'tkreg':              '--reg %s',
        'fslreg':             '--fsl %s',
        'xfmreg':             '--xfm %s',
        'interp':             '--interp %s',
        'noresample':         '--no-resample',
        'inverse':            '--inv', 
        'flags':              '%s'}
    
    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='sourcefile', copy=False)]
        return info

    def _get_outfile(self):
        outfile = self.inputs.outfile
        if not outfile:
            outfile = fname_presuffix(self.inputs.sourcefile,
                                      suffix='_warped')
        return outfile
    
    def _parse_inputs(self):
        """validate fs bbregister options"""
        allargs = super(ApplyVolTransform, self)._parse_inputs(skip=('outfile'))
        outfile = self._get_outfile()
        if outfile:
            allargs.extend(['--o', outfile])
        return allargs
    
    def outputs(self):
        """
        outfile: filename
            Warped source file
        """
        return Bunch(outfile=None)

    def aggregate_outputs(self):
        outputs = self.outputs()
        outfile = self._get_outfile()
        if not glob(outfile):
            raise FileNotFoundError(outfile)
        outputs.outfile = outfile
        return outputs

class SmoothInputSpec(FSTraitedSpec):
    sourcefile= File(exists=True, desc='source volume',
                     argstr='--i %s',mandatory=True)
    regfile = File(desc='registers volume to surface anatomical ',
                   argstr='--reg %s', mandatory=True,
                   exists=True)
    outfile = File(desc='output volume', argstr='--o %s', genfile=True)
    projfrac_avg=traits.Tuple(traits.Float,traits.Float,traits.Float,
                              desc='average a long normal min max delta',
                              argstr='--projfrac-avg %s')
    projfrac = traits.Float(desc='project frac of thickness a long surface normal',
                          argstr='--projfrac %s')
    surface_fwhm = traits.Float(min=0,desc='surface FWHM in mm',argstr='--fwhm %d')
    vol_fwhm = traits.Float(min=0, argstr= '--vol-fwhm %d',
                            desc='volumesmoothing outside of surface')
    flags = traits.Str(desc='maps additional commands', argstr='%s')

class SmoothOutputSpec(FSTraitedSpec):
    outfile= File(exist=True,desc='smoothed input volume')	
         
class Smooth(NEW_FSCommand):
    """Use FreeSurfer mris_volsmooth to smooth a volume

    This function smoothes cortical regions on a surface and
    non-cortical regions in volume.

    Parameters
    ----------

    To see optional arguments
    Smooth().inputs_help()


    Examples
    --------
    >>> from nipype.interfaces.freesurfer import Smooth
    >>> smoothvol = Smooth(sourcefile='foo.nii', outfile = 'foo_out.nii', regfile='reg.dat', surface_fwhm=10, vol_fwhm=6)
    >>> smoothvol.cmdline
    'mris_volsmooth --o foo_out.nii --reg reg.dat --i foo.nii --fwhm 10 --vol-fwhm 6'
    
    """

    _cmd = 'mris_volsmooth'
    input_spec = SmoothInputSpec
    output_spec = SmoothOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['outfile'] = self.inputs.outfile
        if not isdefined(outputs['outfile']) and isdefined(self.inputs.sourcefile):
            outputs['outfile'] = self._gen_fname(self.inputs.sourcefile,
                                              suffix = '_smooth')
        return outputs

    def _gen_filename(self, name):
        if name == 'outfile':
            return self._list_outputs()[name]
        return None

