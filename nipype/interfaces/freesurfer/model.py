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

from nipype.utils.filemanip import fname_presuffix
from nipype.interfaces.freesurfer.base import FSCommand, FSTraitedSpec
from nipype.interfaces.base import (Bunch, TraitedSpec, File,
                                    traits, InputMultiPath)
from nipype.utils.misc import isdefined

class MrisPreprocInputSpec(FSTraitedSpec):
    outfile = File(argstr='--out %s', genfile=True,
                   desc='output filename')
    target = traits.Str(argstr='--target %s', mandatory=True,
                         desc='target subject name')
    hemi = traits.Enum('lh', 'rh', argstr='--hemi %s',
                       mandatory=True,
                       desc='hemisphere for source and target')
    surfmeasure = traits.Str(argstr='--meas %s',
                             xor = ('surfmeasure', 'surfmeasfile', 'surfarea'),
                desc='Use subject/surf/hemi.surfmeasure as input')
    surfarea = traits.Str(argstr='--area %s',
                          xor = ('surfmeasure', 'surfmeasfile', 'surfarea'),
       desc='Extract vertex area from subject/surf/hemi.surfname to use as input.')
    subjects = traits.List(argstr='--s %s...',
                           xor = ('subjects', 'fsgdfile', 'subjectfile'),
                   desc='subjects from who measures are calculated')
    fsgdfile = File(exists=True, argstr='--fsgd %s',
                    xor = ('subjects', 'fsgdfile', 'subjectfile'),
                    desc='specify subjects using fsgd file')
    subjectfile = File(exists=True, argstr='--f %s',
                    xor = ('subjects', 'fsgdfile', 'subjectfile'),
                    desc='file specifying subjects separated by white space')
    surfmeasfile = InputMultiPath(File(exists=True), argstr='--is %s...',
                           xor = ('surfmeasure', 'surfmeasfile', 'surfarea'),
          desc='file alternative to surfmeas, still requires list of subjects')
    srcfmt = traits.Str(argstr='--srcfmt %s', desc='source format')
    surfdir = traits.Str(argstr='--surfdir %s',
                         desc='alternative directory (instead of surf)')
    volmeasfile = InputMultiPath(traits.Tuple(File(exists=True),File(exists=True)),
                                 argstr='--iv %s %s...',
                         desc = 'list of volume measure and reg file tuples')
    projfrac = traits.Float(argstr='--projfrac %s',
                            desc='projection fraction for vol2surf')
    fwhm = traits.Float(argstr='--fwhm %f',
                        xor = ('fwhm', 'niters'),
                        desc='smooth by fwhm mm on the target surface') 
    fwhmsrc = traits.Float(argstr='--fwhm-src %f',
                        xor = ('fwhmsrc', 'niterssrc'),
                        desc='smooth by fwhm mm on the source surface')
    niters = traits.Int(argstr='--niters %d',
                        xor = ('fwhm', 'niters'),
                        desc='niters : smooth by niters on the target surface')
    niterssrc = traits.Int(argstr='--niterssrc %d',
                        xor = ('fwhmsrc', 'niterssrc'),
                        desc='niters : smooth by niters on the source surface')
    smoothcortexonly = traits.Bool(argstr='--smooth-cortex-only',
                       desc='only smooth cortex (ie, exclude medial wall)')

class MrisPreprocOutputSpec(TraitedSpec):
    outfile = File(exists=True, desc='concatenated output file')
    
class MrisPreproc(FSCommand):
    """Use FreeSurfer mris_preproc to prepare a group of contrasts for
    a second level analysis
    
    Examples
    --------
    """

    _cmd = 'mris_preproc'
    input_spec = MrisPreprocInputSpec
    output_spec = MrisPreprocOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outfile = self.inputs.outfile
        if not isdefined(outfile):
            outputs['outfile'] = fname_presuffix(self.inputs.infile,
                                                 newpath=os.getcwd(),
                                                 suffix='_concat.mgz',
                                                 use_ext=False)
        return outputs
    
    def _gen_filename(self, name):
        if name == 'outfile':
            return self._list_outputs()[name]
        return None    

class SurfConcat(MrisPreproc):
    pass

class GlmFitInputSpec(FSTraitedSpec):
    hemi = traits.Str(desc='im not sure what hemi does ',
        argstr='%s')
    surf=traits.Str(desc='subject hemi',argstr='--surf %s')

    glmdir = traits.Str(argstr='--glmdir %s', desc='save outputs to dir')
    infile = File(desc='input file', argstr='--y %s', mandatory=True,
                  copyfile=False)
    _design_xor = ('fsgd', 'design', 'onesample')
    fsgd = traits.Tuple(File(exists=True),traits.Enum('doss', 'dods'),
                        argstr='--fsgd %s %s', xor= _design_xor,
                        desc='freesurfer descriptor file')
    design = File(exists=True, argstr='--X %s', xor= _design_xor,
                  desc='design matrix file')
    contrast = InputMultiPath(File(exists=True), argstr='--C %s...',
                              desc='contrast file')
    
    onesample = traits.Bool(argstr='--osgm',
                            xor=('onesample', 'fsgd', 'design', 'contrast'),
                            desc='construct X and C as a one-sample group mean')
    nocontrastsok = traits.Bool(argstr='--no-contrasts-ok',
                                desc='do not fail if no contrasts specified')
    pervoxelreg = InputMultiPath(File(exists=True), argstr='--pvr %s...',
                                 desc='per-voxel regressors')
    selfreg = traits.Tuple(traits.Int, traits.Int, traits.Int,
                           argstr='--selfreg %d %d %d',
                           desc='self-regressor from index col row slice')
    weightedls = File(exists=True, argstr='--wls %s',
                      xor = ('weightfile', 'weightinv', 'weightsqrt'), 
                      desc='weighted least squares')
    fixedfxvar = File(exists=True, argstr='--yffxvar %s',
                      desc='for fixed effects analysis')
    fixedfxdof = traits.Int(argstr='--ffxdof %d',
                            xor=('fixedfxdof','fixedfxdoffile'),
                            desc='dof for fixed effects analysis')
    fixedfxdoffile = File(argstr='--ffxdofdat %d',
                          xor=('fixedfxdof','fixedfxdoffile'),
                          desc='text file with dof for fixed effects analysis')
    weightfile = File(exists=True, xor = ('weightedls', 'weightfile'),
                      desc='weight for each input at each voxel')
    weightinv = traits.Bool(argstr='--w-inv', desc='invert weights',
                            xor = ('weightedls', 'weightinv'))
    weightsqrt = traits.Bool(argstr='--w-sqrt', desc='sqrt of weights',
                            xor = ('weightedls', 'weightsqrt'))
    fwhm = traits.Float(min=0, argstr='--fwhm %f',
                        desc='smooth input by fwhm')
    varfwhm = traits.Float(min=0, argstr='--var-fwhm %f',
                        desc='smooth variance by fwhm')
    nomasksmooth = traits.Bool(argstr='--no-mask-smooth',
                               desc='do not mask when smoothing')
    noestfwhm = traits.Bool(argstr='--no-est-fwhm',
                            desc='turn off FWHM output estimation')
    maskfile = File(exists=True, argstr='--mask %s', desc='binary mask')
    labelfile = File(exists=True, argstr='--label %s',
                     xor=('labelfile','cortex'),
                     desc='use label as mask, surfaces only')
    cortex = traits.Bool(argstr='--cortex',
                         xor=('labelfile','cortex'),
                         desc='use subjects ?h.cortex.label as label')
    invertmask = traits.Bool(argstr='--mask-inv',
                             desc='invert mask')
    prune = traits.Bool(argstr='--prune',
       desc='remove voxels that do not have a non-zero value at each frame (def)')
    noprune = traits.Bool(argstr='--no-prune',
                          xor = ('noprune', 'prunethresh'),
                          desc='do not prune')
    prunethresh = traits.Float(argstr='--prune_thr %f',
                               xor = ('noprune', 'prunethresh'),
                               desc='prune threshold. Default is FLT_MIN')
    logy = traits.Bool(argstr='--logy',
                       desc='compute natural log of y prior to analysis')
    saveestimate = traits.Bool(argstr='--yhat-save',
                               desc='save signal estimate (yhat)')
    saveresidual = traits.Bool(argstr='--eres-save',
                               desc='save residual error (eres)')
    saverescorrmtx = traits.Bool(argstr='--eres-scm',
       desc='save residual error spatial correlation matrix (eres.scm). Big!')
    surf = traits.Tuple(traits.Str, traits.Enum('lh', 'rh'),
                        traits.Enum('white','pial','smoothwm','inflated'),
                        desc='needed for some flags (uses white by default)')
    simulation = traits.Tuple(traits.Enum('perm','mc-full','mc-z'),
                              traits.Int(min=1), traits.Float, traits.Str,
                              argstr='--sim %s %d %f %s',
                              desc='nulltype nsim thresh csdbasename')
    simsign = traits.Enum('abs', 'pos', 'neg', argstr='--sim-sign %s',
                          desc='abs, pos, or neg')
    uniform = traits.Tuple(traits.Float, traits.Float,
                           argstr='--uniform %f %f',
                      desc='use uniform distribution instead of gaussian')
    pca = traits.Bool(argstr='--pca',
                      desc='perform pca/svd analysis on residual')
    calcAR1 = traits.Bool(argstr='--tar1',
                          desc='compute and save temporal AR1 of residual')
    savecond = traits.Bool(argstr='--save-cond',
            desc='flag to save design matrix condition at each voxel')
    voxdump = traits.Tuple(traits.Int, traits.Int, traits.Int,
                           argstr='--voxdump %d %d %d',
                           desc='dump voxel GLM and exit')
    seed = traits.Int(argstr='--seed %d', desc='used for synthesizing noise')
    synth = traits.Bool(argstr='--synth', desc='replace input with gaussian')
    resynthtest = traits.Int(argstr='--resynthtest %d', desc='test GLM by resynthsis')
    profile = traits.Int(argstr='--profile %d', desc='niters : test speed')
    forceperm = traits.Bool(argstr='--perm-force',
              desc='force perumtation test, even when design matrix is not orthog')
    diag = traits.Int('--diag %d', desc='Gdiag_no : set diagnositc level')
    diagcluster = traits.Bool(argstr='--diag-cluster',
                            desc='save sig volume and exit from first sim loop')
    debug = traits.Bool(argstr='--debug', desc='turn on debugging')
    checkopts = traits.Bool(argstr='--checkopts',
                            desc="don't run anything, just check options and exit")
    allowsubjrep = traits.Bool(argstr='--allowsubjrep',
      desc='allow subject names to repeat in the fsgd file (must appear before --fsgd')
    illcond = traits.Bool(argstr='--illcond',
                 desc='allow ill-conditioned design matrices')
    simdonefile = File(argstr='--sim-done %s',
                   desc='create file when simulation finished')
    
class GlmFit(FSCommand):
    """Use FreeSurfer mri_glmfit to prepare a group of contrasts for
    a second level analysis
    
    Examples
    --------
    """

    _cmd = 'mri_glmfit'
    input_spec = GlmFitInputSpec
        
class OneSampleTTest(GlmFit):

    def __init__(self, **kwargs):
        super(OneSampleTTest, self).__init__(**kwargs)
        self.inputs.onesample = True

class BinarizeInputSpec(FSTraitedSpec):
    infile = File(exists=True, argstr='--i %s', mandatory=True,
                  copyfile=False, desc='input volume')
    min = traits.Float(argstr='--min %f',
                       desc='min thresh')
    max = traits.Float(argstr='--max %f',
                       desc='max thresh')
    rmin = traits.Float(argstr='--rmin %f',
                        desc='compute min based on rmin*globalmean')
    rmax = traits.Float(argstr='--rmax %f',
                        desc='compute max based on rmax*globalmean')
    match = traits.List(traits.Int, argstr='--match %d...',
                        desc='match instead of threshold')
    wm = traits.Bool(argstr='--wm',
         desc='set match vals to 2 and 41 (aseg for cerebral WM)')
    ventricles = traits.Bool(argstr='--ventricles',
         desc='set match vals those for aseg ventricles+choroid (not 4th)')
    wmvcsf = traits.Bool(argstr='--wm+vcsf',
          desc='WM and ventricular CSF, including choroid (not 4th)')
    outfile = File(argstr='--o %s', genfile=True,
                  desc='output volume')
    countfile = traits.Either(traits.Bool, File,
                              argstr='--count %s',
                  desc='save number of hits in ascii file (hits,ntotvox,pct)')
    binval = traits.Int(argstr='--binval %d',
                        desc='set vox within thresh to val (default is 1)')
    binvalnot = traits.Int(argstr='--binvalnot %d',
                        desc='set vox outside range to val (default is 0)')
    invert = traits.Bool(argstr='--inv',
                         desc='set binval=0, binvalnot=1')
    frameno = traits.Int(argstr='--frame %s',
                         desc='use 0-based frame of input (default is 0)')
    mergevol = File(exists=True, argstr='--merge %s',
                    desc='merge with mergevol') 
    maskvol = File(exists=True, argstr='--mask maskvol',
                   desc='must be within mask')
    maskthresh = traits.Float(argstr='--mask-thresh %f',
                    desc='set thresh for mask')
    abs = traits.Bool(argstr='--abs',
                      desc='take abs of invol first (ie, make unsigned)')
    bincol = traits.Bool(argstr='--bincol',
                desc='set binarized voxel value to its column number')
    zeroedges = traits.Bool(argstr='--zero-edges',
                            desc='zero the edge voxels')
    zerosliceedge = traits.Bool(argstr='--zero-slice-edges',
                       desc='zero the edge slice voxels')
    dilate = traits.Int(argstr='--dilate %d',
                        desc='niters: dilate binarization in 3D')
    erode = traits.Int(argstr='--erode  %d',
                       desc='nerode: erode binarization in 3D (after any dilation)')
    erode2d = traits.Int(argstr='--erode2d %d',
                         desc='nerode2d: erode binarization in 2D (after any 3D erosion)')

class BinarizeOutputSpec(TraitedSpec):
    outfile = File(exists=True, desc='binarized output volume')
    countfile = File(desc='ascii file containing number of hits')
    
class Binarize(FSCommand):
    """Use FreeSurfer mri_binarize to threshold an input volume

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import Threshold
    >>> binvol = Threshold(infile='foo.nii', min=10, outfile='foo_out.nii')
    >>> binvol.cmdline
    'mri_binarize --i foo.nii --min 10.000000 --o foo_out.nii'
    
   """

    _cmd = 'mri_binarize'
    input_spec = BinarizeInputSpec
    output_spec = BinarizeOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outfile = self.inputs.outfile
        if not isdefined(outfile):
            outputs['outfile'] = fname_presuffix(self.inputs.infile,
                                            newpath=os.getcwd(),
                                            suffix='_thresh')
        value = self.inputs.countfile
        if isdefined(value):
            if isinstance(value, bool):
                outputs['countfile'] = fname_presuffix(self.inputs.infile,
                                                       suffix='_count.txt',
                                                       newpath=os.getcwd(),
                                                       use_ext=False)
        return outputs

    def _format_arg(self, name, spec, value):
        if name == 'countfile':
            if isinstance(value, bool):
                fname = self._list_outputs()[name]
            else:
                fname = value
            return spec.argstr % fname
        return super(Binarize, self)._format_arg(name, spec, value)
    
    def _gen_filename(self, name):
        if name == 'outfile':
            return self._list_outputs()[name]
        return None    

class Threshold(Binarize):
    pass
    

class ConcatenateInputSpec(FSTraitedSpec):
    invol = InputMultiPath(File(exists=True),
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

class Concatenate(FSCommand):
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


class SegStats(FSCommand):
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

class Label2VolInputSpec(FSTraitedSpec):
    labelfile = InputMultiPath(File(exists=True), argstr='--label %s...',
                   xor = ('labelfile', 'annotfile', 'segfile', 'aparcaseg'),
                               copyfile=False,
                               mandatory=True,
                               desc='list of label files')
    annotfile = File(exists=True, argstr='--annot %s',
                     xor = ('labelfile', 'annotfile', 'segfile', 'aparcaseg'),
                     requires = ('subjectid', 'hemi'),
                     mandatory=True,
                     copyfile=False,
                     desc='surface annotation file')
    segfile = File(exists=True, argstr='--seg %s',
                   xor = ('labelfile', 'annotfile', 'segfile', 'aparcaseg'),
                   mandatory=True,
                   copyfile=False,
                   desc='segmentation file')
    aparcaseg = traits.Bool(argstr='--aparc+aseg',
                            xor = ('labelfile', 'annotfile', 'segfile', 'aparcaseg'),
                            mandatory=True,
                            desc='use aparc+aseg.mgz in subjectdir as seg')
    template = File(exists=True, argstr='--temp %s', mandatory=True,
                    desc='output template volume')
    regmatfile = File(exists=True, argstr='--reg %s',
                      xor = ('regmatfile', 'regheader', 'identity'),
                 desc='tkregister style matrix VolXYZ = R*LabelXYZ')
    regheader = File(exists=True, argstr='--regheader %s',
                      xor = ('regmatfile', 'regheader', 'identity'),
                     desc= 'label template volume')
    identity = traits.Bool(argstr='--identity',
                           xor = ('regmatfile', 'regheader', 'identity'),
                           desc='set R=I')
    invertmtx = traits.Bool(argstr='--invertmtx',
                            desc='Invert the registration matrix')
    fillthresh = traits.Range(0., 1., argstr='--fillthresh %.f',
                              desc='thresh : between 0 and 1')
    labvoxvol = traits.Float(argstr='--labvoxvol %f',
                             desc='volume of each label point (def 1mm3)')
    proj = traits.Tuple(traits.Enum('abs','frac'), traits.Float,
                        traits.Float, traits.Float,
                        argstr='--proj %s %f %f %f',
                        requries = ('subjectid', 'hemi'),
                        desc='project along surface normal')
    subjectid = traits.Str(argstr='--subject %s',
                           desc='subject id')
    hemi = traits.Enum('lh', 'rh', argstr='--hemi %s',
                       desc='hemisphere to use lh or rh')
    surface = traits.Str(argstr='--surf %s',
                         desc='use surface instead of white')
    outfile = File(argstr='--o %s', genfile=True,
                          desc='output volume')
    hitvolid = File(argstr='--hits %s',
                           desc='each frame is nhits for a label')
    labelstat = File(argstr='--label-stat %s',
                    desc='map the label stats field into the vol')
    nativevox2ras = traits.Bool(argstr='--native-vox2ras',
               desc='use native vox2ras xform instead of  tkregister-style')

class Label2VolOutputSpec(TraitedSpec):
    outfile = File(exists=True, desc='output volume')

class Label2Vol(FSCommand):
    """Make a binary volume from a Freesurfer label

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import Label2Vol
    >>> binvol = Label2Vol(label='foo.label', templatevol='bar.nii', regmat='foo_reg.dat',fillthresh=0.5,outvol='foo_out.nii')
    >>> binvol.cmdline
    'mri_label2vol --fillthresh 0.500000 --label foo.label --o foo_out.nii --reg foo_reg.dat --temp bar.nii'
    
   """

    _cmd = 'mri_label2vol'
    input_spec = Label2VolInputSpec
    output_spec = Label2VolOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outfile = self.inputs.outfile
        if not isdefined(outfile):
            for key in ['labelfile', 'annotfile', 'segfile']:
                if isdefined(self.inputs.labelfile):
                    _, src = os.path.split(getattr(self.inputs, key))
            if isdefined(self.inputs.aparcaaseg):
                src = 'aparc+aseg.mgz'
            outfile = fname_presuffix(src, suffix='_vol.nii.gz',
                                      newpath=os.getcwd(),
                                      use_ext=False)
        outputs['outfile'] = outfile
        return outputs

    def _gen_filename(self, name):
        if name == 'outfile':
            return self._list_outputs()[name]
        return None
