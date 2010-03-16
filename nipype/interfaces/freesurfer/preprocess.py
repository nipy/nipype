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

class BBRegister(FSCommand):
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

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'bbregister'


    def inputs_help(self):
        """Print command line documentation for bbregister."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    opt_map = {
        'subject_id':         '--s %s',
        'sourcefile':         '--mov %s',
        'init_spm':           '--init-spm',
        'init_fsl':           '--init-fsl',
        'init_header':        '--init-header',
        'init_reg':           '--init-reg %s',
        't1_contrast':        '--t1',
        't2_contrast':        '--t2',
        'outregfile':         '--reg %s',
        'outfile':            '--o %s',
        'flags':              '%s'}
    
    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='sourcefile',copy=False)]
        return info

    def _get_outfiles(self):
        outregfile = self.inputs.outregfile
        if not self.inputs.outregfile and self.inputs.sourcefile:
            outregfile = fname_presuffix(self.inputs.sourcefile,
                                         suffix='_bbreg_%s.dat'%self.inputs.subject_id,
                                         use_ext=False)
        outfile = self.inputs.outfile
        if self.inputs.outfile == True:
            outfile = fname_presuffix(self.inputs.sourcefile,suffix='_bbreg')
        return (outregfile, outfile)
    
    def _parse_inputs(self):
        """validate fs bbregister options"""
        allargs = super(BBRegister, self)._parse_inputs(skip=('outfile', 'outregfile'))
        outregfile, outfile = self._get_outfiles()
        allargs.extend(['--reg',outregfile])
        if outfile:
            allargs.extend(['--o',outfile])
        return allargs
    
    def outputs(self):
        """
        outregfile: filename
            Output registration file
        outfile: filename
            Registered and resampled source file
        """
        outputs = Bunch(outregfile=None,
                        outfile=None)
        return outputs

    def aggregate_outputs(self):
        outputs = self.outputs()
        outregfile, outfile = self._get_outfiles()
        if not glob(outregfile):
            raise FileNotFoundError(outregfile)
        outputs.outregfile = outregfile
        if outfile:
            if not glob(outfile):
                raise FileNotFoundError(outfile)
            outputs.outfile = outfile
        return outputs

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

        
class Smooth(FSCommand):
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

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'mris_volsmooth'

    def inputs_help(self):
        """Print command line documentation for mris_volsmooth."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    opt_map = {
        'sourcefile':         '--i %s',
        'regfile':            '--reg %s',
        'outfile':            '--o %s',
        'surface_fwhm':       '--fwhm %d',
        'vol_fwhm':           '--vol-fwhm %d',
        'flags':              '%s'}
    
    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='sourcefile',copy=False)]
        return info

    def _get_outfile(self):
        outfile = self.inputs.outfile
        if not outfile:
            outfile = fname_presuffix(self.inputs.sourcefile,
                                      newpath=os.getcwd(),
                                      suffix='_surfsmooth')
        return outfile
    
    def _parse_inputs(self):
        """validate fs bbregister options"""
        allargs = super(Smooth, self)._parse_inputs(skip=('outfile'))
        allargs.extend(['--o', self._get_outfile()])
        return allargs
    
    def outputs(self):
        """
        outfile: filename
            Smoothed input volume
        """
        return Bunch(outfile=None)

    def aggregate_outputs(self):
        outputs = self.outputs()
        outfile = self._get_outfile()
        if not glob(outfile):
            raise FileNotFoundError(outfile)
        outputs.outfile = outfile
        return outputs
