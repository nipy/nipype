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

class SegStatsInputSpec(FSTraitedSpec):
    _xor_inputs = ('segvol', 'annot', 'surflabel')
    segvol = File(exists=True, argstr='--seg %s', xor=_xor_inputs,
                  mandatory=True, desc='segmentation volume path')
    annot = traits.Tuple(traits.Str,traits.Enum('lh','rh'),traits.Str,
                         argstr='--annot %s %s %s', xor=_xor_inputs,
                         mandatory=True,
                         desc='subject hemi parc : use surface parcellation')
    surflabel = traits.Tuple(traits.Str,traits.Enum('lh','rh'),traits.Str,
                             argstr='--slabel %s %s %s', xor=_xor_inputs,
                             mandatory=True,
                             desc='subject hemi label : use surface label')
    sumfile = File(argstr='--sum %s', genfile=True,
                   desc='Segmentation stats summary table file')
    parvol = File(exists=True, argstr='--pv %f',
                  desc='Compensate for partial voluming')
    invol = File(exists=True, argstr='--i %s',
                 desc='Use the segmentation to report stats on this volume')
    frame = traits.Int(argstr='--frame %d',
                       desc='Report stats on nth frame of input volume')
    multiply = traits.Float(argstr='--mul %f', desc='multiply input by val')
    calcsnr = traits.Bool(argstr='--snr', desc='save mean/std as extra column in output table')
    calcpower = traits.Enum('sqr','sqrt',argstr='--%s',
                          desc='Compute either the sqr or the sqrt of the input')
    _ctab_inputs = ('ctab', 'ctabdefault', 'ctabgca')
    ctab = File(exists=True, argstr='--ctab %s', xor=_ctab_inputs,
                desc='color table file with seg id names')
    ctabdefault = traits.Bool(argstr='--ctab-default', xor=_ctab_inputs,
                desc='use $FREESURFER_HOME/FreeSurferColorLUT.txt')
    ctabgca = File(exists=True, argstr='--ctab-gca %s', xor=_ctab_inputs,
                desc='get color table from GCA (CMA)')
    segid = traits.List(argstr='--id %d...',desc='Manually specify segmentation ids')
    excludeid = traits.Int(argstr='--excludeid %d',desc='Exclude seg id from report')
    excludectxgmwm = traits.Bool(argstr='--excl-ctxgmwm',
                                 desc='exclude cortical gray and white matter')
    surfwm = traits.Bool(argstr='--surf-wm-vol',desc='Compute wm volume from surf')
    surfctx = traits.Bool(argstr='--surf-ctx-vol',desc='Compute cortex volume from surf')
    nonempty = traits.Bool(argstr='--nonempty',desc='Only report nonempty segmentations')
    maskvol = File(exists=True, argstr='--mask %s',
                   desc='Mask volume (same size as seg')
    maskthresh = traits.Float(argstr='--maskthresh %f',
                              desc='binarize mask with this threshold <0.5>')
    masksign = traits.Enum('abs','pos','neg','--masksign %s',
                           desc='Sign for mask threshold: pos, neg, or abs')
    maskframe = traits.Int('--maskframe %d',
                           desc='Mask with this (0 based) frame of the mask volume')
    maskinvert = traits.Bool(argstr='--maskinvert', desc='Invert binarized mask volume')
    maskerode = traits.Int(argstr='--maskerode %d', desc='Erode mask by some amount')
    brainvol = traits.Enum('brain-vol-from-seg','brainmask','--%s',
         desc='Compute brain volume either with ``brainmask`` or ``brain-vol-from-seg``')
    etiv = traits.Bool(argstr='--etiv',desc='Compute ICV from talairach transform')
    etivonly = traits.Enum('etiv','old-etiv','--%s-only',
                           desc='Compute etiv and exit.  Use ``etiv`` or ``old-etiv``')
    avgwftxt = traits.Either(traits.Bool, File, argstr='--avgwf %s',
                             desc='Save average waveform into file (bool or filename)')
    avgwfvol = traits.Either(traits.Bool, File, argstr='--avgwfvol %s',
                             desc='Save as binary volume (bool or filename)')
    sfavg = traits.Either(traits.Bool, File, argstr='--sfavg %s',
                          desc='Save mean across space and time')
    vox = traits.List(traits.Int, argstr='--vox %s',
                     desc='Replace seg with all 0s except at C R S (three int inputs)')

class SegStatsOutputSpec(TraitedSpec):
    sumfile = File(exists=True,desc='Segmentation summary statistics table')
    avgwftxt = File(desc='Text file with functional statistics averaged over segs')
    avgwfvol = File(desc='Volume with functional statistics averaged over segs')
    sfavg = File(desc='Text file with func statistics averaged over segs and framss')


class SegStats(NEW_FSCommand):
    """Use FreeSurfer mri_segstats for ROI analysis

    Examples
    --------
    >>> import nipype.interfaces.freesurfer as fs
    >>> ss = fs.SegStats()
    >>> ss.inputs.annot = ('PWS04', 'lh', 'aparc')
    >>> ss.inputs.environ['SUBJECTS_DIR'] = '/somepath/FSDATA'
    >>> ss.inputs.avgwftxt = True
    >>> ss.cmdline
    'mri_segstats --annot PWS04 lh aparc --avgwf ./PWS04_lh_aparc_avgwf.txt --sum ./summary.stats'
    
    """

    _cmd = 'mri_segstats'
    input_spec = SegStatsInputSpec
    output_spec = SegStatsOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['sumfile'] = self.inputs.sumfile
        if not isdefined(outputs['sumfile']):
            outputs['sumfile'] = os.path.join(os.getcwd(), 'summary.stats')
        suffices =dict(avgwftxt='_avgwf.txt', avgwfvol='_avgwf.nii.gz',
                     sfavg='sfavg.txt')
        if isdefined(self.inputs.segvol):
            _, src = os.path.split(self.inputs.segvol)
        if isdefined(self.inputs.annot):
            src = '_'.join(self.inputs.annot)
        if isdefined(self.inputs.surflabel):
            src = '_'.join(self.inputs.surflabel)
        for name, suffix in suffices.items():
            value = getattr(self.inputs, name)
            if isdefined(value):
                if isinstance(value, bool):
                    outputs[name] = fname_presuffix(src, suffix=suffix,
                                                    newpath=os.getcwd(),
                                                    use_ext=False)
                else:
                    outputs[name] = value
        return outputs

    def _format_arg(self, name, spec, value):
        if name in ['avgwftxt', 'avgwfvol', 'sfavg']:
            if isinstance(value, bool):
                fname = self._list_outputs()[name]
            else:
                fname = value
            return spec.argstr % fname
        return super(SegStats, self)._format_arg(name, spec, value)
    
    def _gen_filename(self, name):
        if name == 'sumfile':
            return self._list_outputs()[name]
        return None    

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
