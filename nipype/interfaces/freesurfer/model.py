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
from nipype.utils.filemanip import (fname_presuffix, filename_to_list,
                                    FileNotFoundError)
from nipype.interfaces.freesurfer import FSCommand

from nipype.interfaces.freesurfer.base import NEW_FSCommand, FSTraitedSpec
from nipype.interfaces.base import (Bunch, TraitedSpec, File, traits,
                                    Directory, InputMultiPath)
from nipype.utils.misc import isdefined

class SurfConcat(FSCommand):
    """Use FreeSurfer mris_preproc to prepare a group of contrasts for
    a second level analysis
    
    Parameters
    ----------

    To see optional arguments
    SurfConcat().inputs_help()


    Examples
    --------
   """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'mris_preproc'

    def inputs_help(self):
        """Print command line documentation for mris_preproc."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    opt_map = {
        'target':             '--target %s',
        'hemi':               '--hemi %s',
        'outfile':            '--out %s',
        'outprefix':          None,
        'volimages':          '--iv %s',
        'volregs':            '--iv %s',
        'flags':              '%s'}

    def _get_outfile(self):
        outfile = self.inputs.outfile
        if not outfile:
            if self.inputs.outprefix:
                outfile = os.path.join(os.getcwd(),'_'.join((self.inputs.outprefix,
                                                           self.inputs.target,
                                                           '.'.join((self.inputs.hemi,'mgh')))))
            else:
                outfile = os.path.join(os.getcwd(),'_'.join((self.inputs.target,
                                                           '.'.join((self.inputs.hemi,'mgh')))))
        return outfile
        
    def _parse_inputs(self):
        """validate fs surfconcat options"""
        allargs = super(SurfConcat, self)._parse_inputs(skip=('outprefix','volimages','volregs'))
        allargs.extend(['--out', self._get_outfile()])
        for i,volimg in enumerate(self.inputs.volimages):
            allargs.extend(['--iv', volimg, self.inputs.volregs[i]])
        return allargs
    
    def outputs(self):
        """
        outfile: filename
            Concatenated volume
        """
        return Bunch(outfile=None,
                     hemi=None)

    def aggregate_outputs(self):
        outputs = self.outputs()
        outputs.hemi = self.inputs.hemi
        outfile = self._get_outfile()
        if not glob(outfile):
            raise FileNotFoundError(outfile)
        outputs.outfile = outfile
        return outputs

    
class GlmFit(FSCommand):
    """Use FreeSurfer mri_glmfit to prepare a group of contrasts for
    a second level analysis
    
    Parameters
    ----------

    To see optional arguments
    SurfConcat().inputs_help()


    Examples
    --------
   """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'mri_glmfit'

    def inputs_help(self):
        """Print command line documentation for mris_preproc."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    opt_map = {
        'surf':               '--surf %s',
        'hemi':               '%s',
        'outdir':             '--glmdir %s',
        'funcimage':          '--y %s',
        'onesample':          '--osgm',
        'design':             '--X %s',
        'groupfile':          '--fsgd %s',
        'flags':              '%s'}

    def _parse_inputs(self):
        """validate fs onesamplettest options"""
        allargs = super(GlmFit, self)._parse_inputs(skip=('surf','hemi','outdir',))

        # Add outfile to the args if not specified
        allargs.extend(['--surf',self.inputs.surf,self.inputs.hemi])
        if self.inputs.outdir is None:
            outdir = os.getcwd()
            allargs.extend(['--glmdir', outdir])
        return allargs
    
    def outputs(self):
        """
        """
        return Bunch()

    def aggregate_outputs(self):
        return self.outputs()
        
class OneSampleTTest(GlmFit):
    opt_map = {
        'surf':               '--surf %s',
        'hemi':               '%s',
        'outdir':             '--glmdir %s',
        'funcimage':          '--y %s',
        'flags':              '%s'}
    
    def _parse_inputs(self):
        """validate fs onesamplettest options"""
        allargs = super(OneSampleTTest, self)._parse_inputs()
        allargs.extend(['--osgm'])
        return allargs

class Threshold(FSCommand):
    """Use FreeSurfer mri_binarize to threshold an input volume

    Parameters
    ----------

    To see optional arguments
    Threshold().inputs_help()


    Examples
    --------
    >>> from nipype.interfaces.freesurfer import Threshold
    >>> binvol = Threshold(infile='foo.nii', min=10, outfile='foo_out.nii')
    >>> binvol.cmdline
    'mri_binarize --i foo.nii --min 10.000000 --o foo_out.nii'
    
   """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'mri_binarize'


    def inputs_help(self):
        """Print command line documentation for mri_binarize."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    opt_map = {'abs': '--abs',
               'bincol': '--bincol',
               'binval': '--binval %f',
               'binvalnot': '--binvalnot %f',
               'count': '--count %s',
               'dilate': '--dilate %d',
               'erode': '--erode %d',
               'erode2d': '--erode2d %d',
               'frame': '--frame %d',
               'infile': '--i %s',
               'inv': '--inv',
               'mask': '--mask %s',
               'mask-thresh': '--mask-thresh %f',
               'match': '--match %d',
               'max': '--max %f',
               'merge': '--merge %s',
               'min': '--min %f',
               'outfile': '--o %s',
               'rmax': '--rmax %f',
               'rmin': '--rmin %f',
               'ventricles': '--ventricles',
               'wm': '--wm',
               'wm+vcsf': '--wm+vcsf',
               'zero-edges': '--zero-edges',
               'zero-slice-edges': '--zero-slice-edges',
               'flags' : '%s'}
    
    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='infile',copy=False)]
        return info

    def _get_outfile(self):
        outfile = self.inputs.outfile
        if not outfile and self.inputs.infile:
            outfile = fname_presuffix(self.inputs.infile,
                                      suffix='_out',
                                      newpath=os.getcwd())
        return outfile
            
    def _parse_inputs(self):
        """validate fs bbregister options"""
        allargs = super(Threshold, self)._parse_inputs(skip=('outfile'))
        allargs.extend(['--o',self._get_outfile()])
        return allargs
    
    def outputs(self):
        """
        outfile: filename
            thresholded output file
        """
        outputs = Bunch(outfile=None)
        return outputs

    def aggregate_outputs(self):
        outputs = self.outputs()
        outfile = self._get_outfile()
        if not glob(outfile):
            raise FileNotFoundError(outfile)
        outputs.outfile = outfile
        return outputs

class ConcatenateInputSpec(FSTraitedSpec):
    invol = InputMultiPath(exists=True,
                 desc = 'Individual volumes to be concatenated',
                 argstr='--i %s...',mandatory=True)
    outvol = File('concat_output.nii.gz', desc = 'Output volume', argstr='--o %s',
                  usedefault=True)
    sign = traits.Enum('abs','pos','neg', argstr='--%s',
          desc = 'Take only pos or neg voxles from input, or take abs')
    stats = traits.Enum('sum','var','std','max','min', 'mean', argstr='--%s',
          desc = 'Compute the sum, var, std, max, min or mean of the input volumes')
    pairedstats = traits.Enum('sum','avg','diff', 'diff-norm','diff-norm1',
                              'diff-norm2', argstr='--paired-%s',
                              desc = 'Compute paired sum, avg, or diff')
    gmean = traits.Int(argstr='--gmean %d',
                       desc = 'create matrix to average Ng groups, Nper=Ntot/Ng')
    meandivn = traits.Bool(argstr='--mean-div-n',
                           desc='compute mean/nframes (good for var)')
    multiplyby = traits.Float(argstr='--mul %f',
          desc = 'Multiply input volume by some amount')
    addval = traits.Float(argstr='--add %f',
                          desc = 'Add some amount to the input volume')
    multiplymatrix = File(exists=True, argstr='--mtx %s',
          desc = 'Multiply input by an ascii matrix in file')
    combine = traits.Bool(argstr='--combine',
          desc = 'Combine non-zero values into single frame volume')
    keepdtype = traits.Bool(argstr='--keep-datatype',
          desc = 'Keep voxelwise precision type (default is float')
    maxbonfcor = traits.Bool(argstr='--max-bonfcor',
          desc = 'Compute max and bonferroni correct (assumes -log10(ps))')
    maxindex = traits.Bool(argstr='--max-index',
          desc = 'Compute the index of max voxel in concatenated volumes')
    mask = File(exists=True, argstr='--mask %s', desc = 'Mask input with a volume')
    vote = traits.Bool(argstr='--vote',
          desc = 'Most frequent value at each voxel and fraction of occurances')
    sort = traits.Bool(argstr='--sort',
          desc = 'Sort each voxel by ascending frame value')

class ConcatenateOutputSpec(TraitedSpec):
    outvol = File(exists=True,
                  desc='Path/name of the output volume')

class Concatenate(NEW_FSCommand):
    """Use Freesurfer mri_concat to combine several input volumes
    into one output volume.  Can concatenate by frames, or compute
    a variety of statistics on the input volumes.

    Examples
    --------

    Combine two input volumes into one volume with two frames

    >>> concat = fs.Concatenate()
    >>> concat.inputs.infile = ['foo.nii,goo.nii']
    >>> concat.inputs.outfile 'bar.nii'

    """

    _cmd = 'mri_concat'
    input_spec = ConcatenateInputSpec
    output_spec = ConcatenateOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['outvol'] = self.inputs.outvol
        return outputs

class SegStats(FSCommand):
    """Use FreeSurfer mri_segstats for ROI analysis

    Parameters
    ----------

    To see optional arguments
    SegStats().inputs_help()


    Examples
    --------
    >>> from nipype.interfaces.freesurfer import SegStats
    >>> segstat = SegStats(segvol='seg.nii', invol='foo.nii', segid=18, sumfile='foo_sum.txt')
    >>> segstat.cmdline
    'mri_segstats --i foo.nii --seg seg.nii --id 18 --sum foo_sum.txt'
    
   """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'mri_segstats'


    def inputs_help(self):
        """Print command line documentation for mri_segstats."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    opt_map = {'segvol': '--seg %s',
               'annot': '--annot %s %s %s',
               'slabel': '--slabel %s %s %s',
               'sumfile': '--sum %s',
               'parvol': '--pv %s',
               'invol': '--i %s',
               'frame': '--frame %f',
               'square': '--sqr',
               'squareroot': '--sqrt',
               'multiply': '--mul %f',
               'savemeanstd': '--snr',
               'colortable': '--ctab %s',
               'ctab_default': '--ctab-default',
               'ctab_gca': '--ctab-gca',
               'segid': '--id %s',
               'excludeid': '--excludeid %s',
               'excl_ctxgmwm': '--excl-ctxgmwm',
               'surf_wm_vol': '--surf-wm-vol',
               'surf_ctx_vol': '--surf-ctx-vol',
               'nonempty': '--nonempty',
               'maskvol': '--mask %s',
               'maskthresh': '--maskthresh %f',
               'masksign': '--masksign %s',
               'maskframe': '--maskframe %f',
               'maskinvert': '--maskinvert',
               'maskerode' : '--maskerode %f',
               'brain_vol_from_seg': '--brain-vol-from-seg',
               'brainmask': '--brainmask',
               'talicv': '--etiv',
               'talicv_only': '--etiv-only',
               'avgwftxt': '--avgwf %s',
               'avgwfvol': '--avgwfvol %s',
               'savgmsf' : '--sfavg %s',		
               'vox': '--vox %d %d %d',
               'flags': '%s'}
    
    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='invol',copy=False)]
        return info
    
    def _parse_inputs(self):
        """validate fs mri_segstats options"""
        allargs = super(SegStats, self)._parse_inputs(skip=('sumfile','segid','avgwftxt','avgwfvol'))

        # Add invol to the args if they are specified
        if self.inputs.segid:
            if isinstance(self.inputs.segid,list):
                for id in self.inputs.segid:
                    allargs.extend(['--id', str(id)])
            else:
                allargs.extend(['--id', str(self.inputs.segid)])
        if self.inputs.invol:
            if isinstance(self.inputs.sumfile,str):
                allargs.extend(['--sum',self.inputs.sumfile])
            else:
                allargs.extend(['--sum',fname_presuffix(self.inputs.invol,
                                                          suffix='_summary.txt',
                                                          use_ext=False,
                                                          newpath=os.getcwd())])
        if self.inputs.avgwftxt and self.inputs.invol:
            if isinstance(self.inputs.avgwftxt,str):
                allargs.extend(['--avgwf',self.inputs.avgwftxt])
            else:
                allargs.extend(['--avgwf',fname_presuffix(self.inputs.invol,
                                                          suffix='_avgwf.txt',
                                                          use_ext=False,
                                                          newpath=os.getcwd())])
        if self.inputs.avgwfvol and self.inputs.invol:
            if isinstance(self.inputs.avgwfvol,str):
                allargs.extend(['--avgwfvol',self.inputs.avgwfvol])
            else:
                allargs.extend(['--avgwfvol',fname_presuffix(self.inputs.invol,
                                                          suffix='_avgwfvol.nii.gz',
                                                          use_ext=False,
                                                          newpath=os.getcwd())])
        return allargs
    
    def outputs(self):
        """
        outfile: filename
              output file
        """
        outputs = Bunch(sumfile=None,
                        avgwffile=None,
                        avgwfvol=None)
        return outputs

    def aggregate_outputs(self):
        outputs = self.outputs()
        return outputs

class Label2Vol(FSCommand):
    """Make a binary volume from a Freesurfer label

    Parameters
    ----------

    To see optional arguments
    Label2Vol().inputs_help()


    Examples
    --------
    >>> from nipype.interfaces.freesurfer import Label2Vol
    >>> binvol = Label2Vol(label='foo.label', templatevol='bar.nii', regmat='foo_reg.dat',fillthresh=0.5,outvol='foo_out.nii')
    >>> binvol.cmdline
    'mri_label2vol --fillthresh 0.500000 --label foo.label --o foo_out.nii --reg foo_reg.dat --temp bar.nii'
    
   """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'mri_label2vol'


    def inputs_help(self):
        """Print command line documentation for mri_label2vol."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    opt_map = {'label': '--label %s',
               'annotfile': '--annot %s',
               'segpath': '--seg %s',
               'aparc+aseg': '--aparc+aseg',
               'templatevol': '--temp %s',
               'regmat': '--reg %s',
               'volid': '--regheader %s',
               'identity': '--identity',
               'invertmtx': '--invertmtx',
               'fillthresh': '--fillthresh %f',
               'voxvol': '--labvoxvol %s',
               'proj': '--proj %s %f %f %f',
               'subjectid': '--subject %s',
               'hemi': '--hemi %s',
               'outvol': '--o %s',
               'hitvolid': '--hits %f',
               'statvol': '--label-stat %s',
               'native-vox2ras': '--native-vox2ras'
               }
    
    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='infile',copy=False)]
        return info

    def _get_outfile(self):
        outfile = self.inputs.outvol
        if not outfile:
            if isinstance(self.inputs.label,list):
                label = self.inputs.label[0]
            else:
                label = self.inputs.label
            outfile = fname_presuffix(label,
                                      suffix='_vol.nii',
                                      use_ext=False,
                                      newpath=os.getcwd())
        return outfile
        
    def _parse_inputs(self):
        """validate fs mri_label2vol options"""
        allargs = super(Label2Vol, self)._parse_inputs(skip=('label','outvol'))

        # Add invol to the args if they are specified
        if self.inputs.label:
            if isinstance(self.inputs.label,list):
                for id in self.inputs.label:
                    allargs.extend(['--label', str(id)])
            else:
                allargs.extend(['--label', str(self.inputs.label)])
        allargs.extend(['--o', self._get_outfile()])
        
        return allargs
    
    def outputs(self):
        """
        outfile: filename
              output file
        """
        outputs = Bunch(outfile=None)
        return outputs

    def aggregate_outputs(self):
        outputs = self.outputs()
        outfile = self._get_outfile()
        if not glob(outfile):
            raise FileNotFoundError(outfile)
        outputs.outfile = outfile
        return outputs
