"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 4.1.4.

Examples
--------
See the docstrings of the individual classes for examples.

"""

import os
import warnings

from nipype.interfaces.fsl.base import NEW_FSLCommand, FSLTraitedSpec
from nipype.interfaces.base import Bunch, TraitedSpec, isdefined, File,\
    InputMultiPath,Directory
from nipype.utils.filemanip import fname_presuffix, filename_to_list
import enthought.traits.api as traits
warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

class DtifitInputSpec(FSLTraitedSpec):
    
    dwi = File(exists=True, desc = 'diffusion weighted image data file',
                  argstr='-k %s', position=0, mandatory=True)
    basename = traits.Str( desc = 'basename that all output files will start with',
                           argstr='-o %s', position=1, mandatory=True)
    mask = File(exists=True, desc = 'bet binary mask file',
                argstr='-m %s', position=2, mandatory=True)    
    bvec = File(exists=True, desc = 'b vectors file',
                argstr='-r %s', position=3, mandatory=True)
    bval = File(exists=True,desc = 'b values file',
                argstr='-b %s', position=4, mandatory=True)
    min_z = traits.Int(argstr='-z %d', desc='min z')
    max_z = traits.Int(argstr='-Z %d', desc='max z')
    min_y = traits.Int(argstr='-y %d', desc='min y')
    max_y = traits.Int(argstr='-Y %d', desc='max y')
    min_x = traits.Int(argstr='-x %d', desc='min x')
    max_x = traits.Int(argstr='-X %d', desc='max x')
    save =  traits.Bool(desc = 'save the elements of the tensor',
                        argstr='--save_tensor')
    sse =  traits.Bool(desc = 'output sum of squared errors', argstr='--sse')
    cni = File(exists=True, desc = 'input counfound regressors', argstr='-cni %s')
    littlebit =  traits.Bool(desc = 'only process small area of brain',
                             argstr='--littlebit')

class DtifitOutputSpec(FSLTraitedSpec):
    
    V1 = File(exists = True, desc = 'path/name of file with the 1st eigenvector')
    V2 = File(exists = True, desc = 'path/name of file with the 2nd eigenvector')
    V3 = File(exists = True, desc = 'path/name of file with the 3rd eigenvector')
    L1 = File(exists = True, desc = 'path/name of file with the 1st eigenvalue')
    L2 = File(exists = True, desc = 'path/name of file with the 2nd eigenvalue')
    L3 = File(exists = True, desc = 'path/name of file with the 3rd eigenvalue')
    MD = File(exists = True, desc = 'path/name of file with the mean diffusivity')
    FA = File(exists = True, desc = 'path/name of file with the fractional anisotropy')
    S0 = File(exists = True, desc = 'path/name of file with the raw T2 signal with no diffusion weighting')    

class Dtifit(NEW_FSLCommand):
    """ Use FSL  dtifit command for fitting a diffusion tensor model at each voxel
        Example:
        >>> from nipype.interfaces import fsl
        >>> dti = fsl.Dtifit()
        >>> dti.inputs.dwi = data.nii.gz
        >>> dti.inputs.bvec = bvecs
        >>> dti.inputs.bval = bvals
        >>> dti.inputs.basename = TP
        >>> dti.inputs.mask = nodif_brain_mask.nii.gz
        >>> dti.cmdline
        'dtifit -k data.nii.gz -o TP -m nodif_brain_mask.nii.gz -r bvecs -b bvals'
    """
    _cmd = 'dtifit'
    input_spec = DtifitInputSpec
    output_spec = DtifitOutputSpec
        
    def _list_outputs(self):        
        outputs = self.output_spec().get()
        pth,basename = os.path.split(self.inputs.basename)        
        for k in outputs.keys():
            if k not in ('outputtype','environ','args'):
                outputs[k] = self._gen_fname(basename,cwd=os.path.abspath(pth),
                                             suffix = '_'+k)
        return outputs

    def _gen_filename(self, name):
        if name in ('V1','V2','V3','L1','L2','L3','MD','FA','S0'):
            return self._list_outputs()[name]
        else:
            return None
    
class EddycorrectInputSpec(FSLTraitedSpec):
    infile = File(exists=True,desc = '4D input file',argstr='%s', position=0, mandatory=True)
    outfile = File(desc = '4D output file',argstr='%s', position=1, genfile=True)
    refnum = traits.Int(argstr='%d', position=2, desc='reference number',mandatory=True)

class EddycorrectOutputSpec(FSLTraitedSpec):
    outfile = File(exists=True, desc='path/name of 4D eddy corrected output file')

class Eddycorrect(NEW_FSLCommand):
    """ Use FSL eddy_correct command for correction of eddy current distortion
        Example:
        >>> from nipype.interfaces import fsl
        >>> eddyc = fsl.Eddycorrect(infile='/data.nii.gz',refnum=0)
        >>> print dti.cmdline
        'eddy_correct data.nii.gz data_edc.nii.gz 0'
    """
    _cmd = 'eddy_correct'
    input_spec = EddycorrectInputSpec
    output_spec = EddycorrectOutputSpec

    def _run_interface(self, runtime):
        runtime = super(Eddycorrect, self)._run_interface(runtime)
        if runtime.stderr:
            runtime.returncode = 1
        return runtime

    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['outfile'] = self.inputs.outfile
        if not isdefined(outputs['outfile']) and isdefined(self.inputs.infile):
            pth,basename = os.path.split(self.inputs.infile) 
            outputs['outfile'] = self._gen_fname(basename,cwd=os.path.abspath(pth),
                                                 suffix = '_edc')
        return outputs

    def _gen_filename(self, name):
        if name is 'outfile':
            return self._list_outputs()[name]
        else:
            return None

class BedpostxInputSpec(FSLTraitedSpec):
    bpxdirectory = Directory(exists=True, field='dir',
                             desc = 'directory with all bedpostx standard files: data, bvecs, '+
                             'bvals, nodif_brain_mask',
                             argstr='%s', position=0, mandatory=True)
    fibres = traits.Int(argstr='-n %d', desc='number of fibres per voxel, default 2')
    weight = traits.Float(argstr='-w %.2f', desc='ARD weight, more weight means less secondary fibres '+
                          'per voxel, default 1')
    burn_period = traits.Int(argstr='-b %d', desc='burnin period, default 1000')
    jumps = traits.Int(argstr='-j %d', desc='number of jumps, default 1250')
    sampling = traits.Int(argstr='-s %d', desc='sample every, default 25')
    
class BedpostxOutputSpec(FSLTraitedSpec):
    bpxdirectory = Directory(exists=True, field='dir', desc = 'path/name of directory with all '+
                             'bedpostx output files')
    xfmsdirectory = Directory(exists=True, field='dir', desc = 'path/name of directory with the '+
                              'tranformation matrices')
    merged_th1samples = File(exists=True, desc='path/name of 4D volume with samples from the distribution on theta')
    merged_ph1samples = File(exists=True, desc='path/name of file with samples from the distribution on phi')
    merged_f1samples = File(exists=True,desc='path/name of 4D volume with samples from the distribution on'+
                            ' anisotropic volume fraction')
    mean_th1samples = File(exists=True, desc='path/name of 3D volume with mean of distribution on theta')
    mean_ph1samples = File(exists=True, desc='path/name of 3D volume with mean of distribution on phi')
    mean_f1samples = File(exists=True, desc='path/name of 3D volume with mean of distribution on f anisotropy')
    dyads1 = File(exists=True, desc='path/name of mean of PDD distribution in vector form')
    nodif_brain = File(exists=True, desc='path/name of brain extracted version of nodif')
    nodif_brain_mask = File(exists=True, desc='path/name of binary mask created from nodif_brain')
    
class Bedpostx(NEW_FSLCommand):
    """ Use FSL  bedpostx command for local modelling of diffusion parameters
        Example:
        >>> from nipype.interfaces import fsl
        >>> bedp = fsl.Bedpostx(bpxdirectory='subjdir', fibres=1)
        >>> bedp.cmdline
        'bedpostx subjdir -n 1'
    """
    _cmd = 'bedpostx'
    input_spec = BedpostxInputSpec
    output_spec = BedpostxOutputSpec

    def _list_outputs(self):        
        outputs = self.output_spec().get()
        for k in outputs.keys():
            if k not in ('outputtype','environ','args'):
                if k is 'bpxdirectory':
                    outputs[k] = self.inputs.bpxdirectory
                elif k is 'xfmsdirectory':
                    outputs[k] = os.path.join(self.inputs.bpxdirectory,'xfms')
                else:
                    outputs[k] = self._gen_fname(k,cwd=os.path.abspath(self.inputs.bpxdirectory),suffix='')                 
        return outputs

    def _gen_filename(self, name):
        if name in ('merged_th1samples','merged_ph1samples','merged_f1samples',
                    'mean_th1samples','mean_ph1samples','mean_f1samples','dyads1',
                    'nodif_brain','nodif_brain_mask','bpxdirectory','xfmsdirectory'):
            return self._list_outputs()[name]
        else:
            return None

class Tbss1preprocInputSpec(FSLTraitedSpec):
    imglist = traits.List(traits.Str, desc = 'list with filenames of the FA images',
                          argstr='%s',mandatory=True)
    tbssdir = Directory(exists=True, field='dir',
                        desc='path/name of directory in which this command will be executed '+
                        '(note: directory must contain the FA images)',
                        mandatory=True)
    
class Tbss1preprocOutputSpec(FSLTraitedSpec):
    tbssdir = Directory(exists=True, field='dir',
                        desc='path/name of directory where this command was executed')

class Tbss1preproc(NEW_FSLCommand):
    """
        Use FSL Tbss1preproc for preparing your FA data in your TBSS working directory in the right format
        Example:
        >>> from nipype.interfaces import fsl
        >>> tbss1 = fsl.Tbss1preproc(imglist=[f1,f2,f3],tbssdir='/home')
        >>> tbss1.cmdline
        'tbss_1_preproc f1 f2 f3'
    """
    _cmd = 'tbss_1_preproc'
    input_spec = Tbss1preprocInputSpec
    output_spec = Tbss1preprocOutputSpec

    def _run_interface(self, runtime):        
        runtime.cwd = self.inputs.tbssdir
        return super(Tbss1preproc, self)._run_interface(runtime)

    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['tbssdir'] = self.inputs.tbssdir             
        return outputs

    def _gen_filename(self, name):
        if name is 'tbssdir':
            return self._list_outputs()[name]
        else:
            return None
        
class Tbss2regInputSpec(FSLTraitedSpec):
    tbssdir = Directory(exists=True, field='dir',
                        desc = 'path/name of directory containing the FA and origdata folders '+
                        'generated by tbss_1_preproc',
                        mandatory=True)
    _xor_inputs = ('FMRIB58FA', 'targetImg','findTarget')
    FMRIB58FA = traits.Bool(desc='use FMRIB58_FA_1mm as target for nonlinear registrations',
                            argstr='-T', xor=_xor_inputs)                            
    targetImg = traits.Str(desc='use given image as target for nonlinear registrations',
                           argstr='-t %s', xor=_xor_inputs)
    findTarget = traits.Bool(desc='find best target from all images in FA',
                             argstr='-n', xor=_xor_inputs)
    
class Tbss2regOutputSpec(FSLTraitedSpec):
    tbssdir = Directory(exists=True, field='dir',
                        desc='path/name of directory containing the FA and origdata folders '+
                        'generated by tbss_1_preproc')
   
class Tbss2reg(NEW_FSLCommand):
    """
        Use FSL Tbss2reg for applying nonlinear registration of all FA images into standard space
        Example:
        >>> from nipype.interfaces import fsl
        >>> tbss2 = fsl.Tbss2reg(tbssdir=os.getcwd(),FMRIB58FA=True)
        >>> tbss2.cmdline
        'tbss_2_reg -T'
    """
    _cmd = 'tbss_2_reg'
    input_spec = Tbss2regInputSpec
    output_spec = Tbss2regOutputSpec

    def _run_interface(self, runtime):        
        runtime.cwd = self.inputs.tbssdir
        return super(Tbss2reg, self)._run_interface(runtime)

    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['tbssdir'] = self.inputs.tbssdir             
        return outputs

    def _gen_filename(self, name):
        if name is 'tbssdir':
            return self._list_outputs()[name]
        else:
            return None

class Tbss3postregInputSpec(FSLTraitedSpec):
    tbssdir = Directory(exists=True, field='dir',
                        desc = 'path/name of directory containing the FA and origdata '+
                        'folders generated by tbss_1_preproc',
                        mandatory=True)
    _xor_inputs = ('subjectmean', 'FMRIB58FA')
    subjectmean = traits.Bool(desc='derive mean_FA and mean_FA_skeleton from mean of all subjects in study',
                              argstr='-S', xor=_xor_inputs)
    FMRIB58FA = traits.Bool(desc='use FMRIB58_FA and its skeleton instead of study-derived mean and skeleton',
                            argstr='-T', xor=_xor_inputs)
   
class Tbss3postregOutputSpec(FSLTraitedSpec):
    tbssdir = Directory(exists=True, field='dir',
                        desc='path/name of directory containing the FA, origdata, and '+
                        'stats folders generated by tbss_1_preproc and this command')
    all_FA = File(exists=True, desc='path/name of 4D volume with all FA images') 
    mean_FA_skeleton = File(exists=True, desc='path/name of 3D volume with mean FA skeleton')     
    mean_FA = File(exists=True, desc='path/name of 3D volume with mean FA image')
    
  
class Tbss3postreg(NEW_FSLCommand):
    """
        Use FSL Tbss3postreg for creating the mean FA image and skeletonise it
        Example:
        >>> from nipype.interfaces import fsl
        >>> tbss3 = fsl.Tbss3postreg(subjectmean=True)
        >>> tbss3.cmdline
        'tbss_3_postreg -S'
    """
    _cmd = 'tbss_3_postreg'
    input_spec = Tbss3postregInputSpec
    output_spec = Tbss3postregOutputSpec

    def _run_interface(self, runtime):        
        runtime.cwd = self.inputs.tbssdir
        return super(Tbss3postreg, self)._run_interface(runtime)
    
    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['tbssdir'] = self.inputs.tbssdir
        stats = os.path.join(self.inputs.tbssdir,'stats')
        outputs['all_FA'] = self._gen_fname('all_FA',
                                            cwd=os.path.abspath(stats),suffix='' )
        outputs['mean_FA_skeleton'] = self._gen_fname('mean_FA_skeleton',
                                                      cwd=os.path.abspath(stats),suffix='' )
        outputs['mean_FA'] = self._gen_fname('mean_FA',
                                             cwd=os.path.abspath(stats),suffix='' )        
        return outputs

    def _gen_filename(self, name):
        if name in ('all_FA','mean_FA_skeleton','mean_FA'):
            return self._list_outputs()[name]
        else:
            return None

class Tbss4prestatsInputSpec(FSLTraitedSpec):
    tbssdir = Directory(exists=True, field='dir',
                        desc = 'path/name of directory containing the FA, origdata, and '+
                        'stats folders generated by tbss_1_preproc and tbss_3_postreg',
                        mandatory=True)
    threshold = traits.Float(argstr='%.3f', desc='threshold value',mandatory=True)

class Tbss4prestatsOutputSpec(FSLTraitedSpec):
    all_FA_skeletonised = File(exists=True, desc='path/name of 4D volume with all FA images skeletonized')
    tbssdir = Directory(exists=True, field='dir',
                        desc = 'path/name of directory containing the FA, origdata, and stats '+
                        'folders generated by tbss_1_preproc and tbss_3_postreg')

class Tbss4prestats(NEW_FSLCommand):
    """
        Use FSL Tbss4prestats thresholds the mean FA skeleton image at the chosen threshold
        Example:
        >>> from nipype.interfaces import fsl
        >>> tbss4 = fsl.Tbss4prestats(threshold=0.3)
        >>> tbss4.cmdline
        'tbss_4_prestats 0.3'
    """
    _cmd = 'tbss_4_prestats'
    input_spec = Tbss4prestatsInputSpec
    output_spec = Tbss4prestatsOutputSpec

    def _run_interface(self, runtime):        
        runtime.cwd = self.inputs.tbssdir
        return super(Tbss4prestats, self)._run_interface(runtime)
   
    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['tbssdir'] = self.inputs.tbssdir
        stats = os.path.join(self.inputs.tbssdir,'stats')
        outputs['all_FA_skeletonised'] = self._gen_fname('all_FA_skeletonised',
                                                         cwd=os.path.abspath(stats),
                                                         suffix='' )
        return outputs

    def _gen_filename(self, name):
        if name in ('tbssdir','all_FA_skeletonised'):
            return self._list_outputs()[name]
        else:
            return None

class RandomiseInputSpec(FSLTraitedSpec):
    
    infile = File(exists=True,desc = '4D input file',argstr='-i %s', position=0, mandatory=True)
    basename = traits.Str(desc = 'the rootname that all generated files will have',
                          argstr='-o %s', position=1, mandatory=True)
    designmat = File(exists=True,desc = 'design matrix file',argstr='-d %s', position=2, mandatory=True)
    tcon = File(exists=True,desc = 't contrasts file',argstr='-t %s', position=3, mandatory=True)
    fcon = File(exists=True,desc = 'f contrasts file',argstr='-f %s')
    mask = File(exists=True,desc = 'mask image',argstr='-m %s')
    xblocklabels = File(exists=True,desc = 'exchangeability block labels file',argstr='-e %s')   
    demean = traits.Bool(desc = 'demean data temporally before model fitting', argstr='-D')
    onesamplegmean =  traits.Bool(desc = 'perform 1-sample group-mean test instead of generic permutation test',
                                  argstr='-l')
    showtotalperms = traits.Bool(desc = 'print out how many unique permutations would be generated and exit',
                                 argstr='-q')
    showinfoparmode = traits.Bool(desc = 'print out information required for parallel mode and exit',
                                  argstr='-Q')
    voxpvalues = traits.Bool(desc = 'output voxelwise (corrected and uncorrected) p-value images',
                            argstr='-x')
    tfce = traits.Bool(desc = 'carry out Threshold-Free Cluster Enhancement', argstr='-T')
    tfce2D = traits.Bool(desc = 'carry out Threshold-Free Cluster Enhancement with 2D optimisation',
                         argstr='--T2')
    fonly = traits.Bool(desc = 'calculate f-statistics only', argstr='--fonly')    
    rawstatsimgs = traits.Bool(desc = 'output raw ( unpermuted ) statistic images', argstr='-R')
    pvecndistfiles = traits.Bool(desc = 'output permutation vector and null distribution text files',
                                 argstr='-P')
    numperm = traits.Int(argstr='-n %d', desc='number of permutations (default 5000, set to 0 for exhaustive)')
    seed = traits.Int(argstr='--seed %d', desc='specific integer seed for random number generator')
    varsmooth = traits.Int(argstr='-v %d', desc='use variance smoothing (std is in mm)')   
    cthresh = traits.Float(argstr='-c %.2f', desc='carry out cluster-based thresholding')
    cmthresh = traits.Float(argstr='-C %.2f', desc='carry out cluster-mass-based thresholding')
    fcthresh = traits.Float(argstr='-F %.2f', desc='carry out f cluster thresholding')
    fcmthresh = traits.Float(argstr='-S %.2f', desc='carry out f cluster-mass thresholding')    
    tfce_H = traits.Float(argstr='--tfce_H %.2f', desc='TFCE height parameter (default=2)')
    tfce_E = traits.Float(argstr='--tfce_E %.2f', desc='TFCE extent parameter (default=0.5)')
    tfce_C = traits.Float(argstr='--tfce_C %.2f', desc='TFCE connectivity (6 or 26; default=6)')    
    vxl = traits.List(traits.Int,argstr='--vxl %d', desc='list of numbers indicating voxelwise EVs'+
                      'position in the design matrix (list order corresponds to files in vxf option)')
    vxf = traits.List(traits.Int,argstr='--vxf %d', desc='list of 4D images containing voxelwise EVs'+
                      '(list order corresponds to numbers in vxl option)')
             
class RandomiseOutputSpec(FSLTraitedSpec):
    tstat1file = File(exists=True,desc = 'tstat image corresponding to the first t contrast')  

class Randomise(NEW_FSLCommand):
    """
        FSL Randomise: feeds the 4D projected FA data into GLM modelling and thresholding
        in order to find voxels which correlate with your model
        Example:
        >>> from nipype.interfaces import fsl
        >>> rand = fsl.Randomise(infile='allFA',
                                 basename='tbss',
                                 tcon='design.con',
                                 designmat='design.mat')
        >>> rand.cmdline
        'randomise -i allFA -o tbss -t design.con -d design.mat'
    """
    _cmd = 'randomise'
    input_spec = RandomiseInputSpec
    output_spec = RandomiseOutputSpec
   
    def _list_outputs(self):        
        outputs = self.output_spec().get()        
        outputs['tstat1file'] = self._gen_fname(self.inputs.basename,suffix='_tstat1')
        return outputs

    def _gen_filename(self, name):
        if name is 'tstat1file':
            return self._list_outputs()[name]
        else:
            return None

class ProbtrackxInputSpec(FSLTraitedSpec):
    samplesbasename = traits.Str(desc = 'the rootname/basename for samples files',
                                 argstr='-s %s', position=0, mandatory=True)	
    mask	 = File(exists=True, desc='bet binary mask file in diffusion space',
                 argstr='-m %s', position=1, mandatory=True)
    seedfile = 	File(exists=True, desc='seed volume, or voxel, or ascii file with multiple'+
                     'volumes, or freesurfer label file',argstr='-x %s', position=2, mandatory=True)	
    mode	= traits.Str(desc='options: simple (single seed voxel), seedmask (mask of seed voxels),'+
                     'twomask_symm (two bet binary masks) ', argstr='--mode=%s')                             
    targetmasks	= File(exits=True,desc='file containing a list of target masks - '+
                       'required for seeds_to_targets classification', argstr='--targetmasks=%s')    
    mask2	=File(exists=True,desc='second bet binary mask (in diffusion space) in twomask_symm mode',
                argstr='--mask2=%s')
    waypoints	= File(exists=True, desc='waypoint mask or ascii list of waypoint masks - '+
                    'only keep paths going through ALL the masks',argstr='--waypoints=%s')
    network	= traits.Bool(desc='activate network mode - only keep paths going through '+
                         'at least one seed mask (required if multiple seed masks)',
                          argstr='--network')
    mesh = File(exists=True,desc='Freesurfer-type surface descriptor (in ascii format)',
                argstr='--mesh=%s')
    seedref	= File(exists=True, desc='reference vol to define seed space in '+
                   'simple mode - diffusion space assumed if absent',
                   argstr='--seedref=%s')
    outdir	= Directory(exists=True,desc='directory to put the final volumes in - '+
                      'code makes this directory - default is logdir',argstr='--dir=%s')
    forcedir	= traits.Bool(desc='use the actual directory name given - i.e. '+
                          'do not add + to make a new directory',argstr='--forcedir')
    showpd = traits.Bool(desc='outputs the distribution of paths',argstr='--opd')
    correctpd	= traits.Bool(desc='correct path distribution for the length of the pathways',
                            argstr='--pd')
    os2t	= traits.Bool(desc='Outputs seeds to targets',argstr='--os2t')
    pathsfile = File(desc='produces an output file (default is fdt_paths)',
                        argstr='--out=%s')
    avoidmp = File(exists=True, desc='reject pathways passing through locations given by this mask',
                   argstr='--avoid=%s')
    stopinmask = File(exists=True,argstr='--stop=%s',
                      desc='stop tracking at locations given by this mask file')	
    xfm = File(exists=True, argstr='--xfm=%s',
               desc='transformation matrix taking seed space to DTI space '+
                '(either FLIRT matrix or FNIRT warpfield) - default is identity')    
    invxfm = File( argstr='--invxfm=%s',desc='transformation matrix taking DTI space to seed'+
                    ' space (compulsory when using a warpfield for seeds_to_dti)')
    nsamples = traits.Int(argstr='--nsamples=%d',desc='number of samples - default=5000')
    nsteps = traits.Int(argstr='--nsteps=%d',desc='number of steps per sample - default=2000')
    distthresh = traits.Float(argstr='--distthresh=%.3f',desc='discards samples shorter than '+
                              'this threshold (in mm - default=0)')    
    cthresh = traits.Float(argstr='--cthr=%.3f',desc='curvature threshold - default=0.2')
    samrandp = traits.Bool(argstr='--sampvox',desc='sample random points within seed voxels')
    steplength = traits.Float(argstr='--steplength=%.3f',desc='steplength in mm - default=0.5')
    loopcheck = traits.Bool(argstr='--loopcheck',desc='perform loopchecks on paths -'+
                            ' slower, but allows lower curvature threshold')
    usef = traits.Bool(argstr='--usef',desc='use anisotropy to constrain tracking')
    randfib = traits.Bool(argstr='--randfib',desc='options: 0 - default, 1 - to randomly sample'+
                          ' initial fibres (with f > fibthresh), 2 - to sample in '+
                          'proportion fibres (with f>fibthresh) to f, 3 - to sample ALL '+
                          'populations at random (even if f<fibthresh)')
    fibst = traits.Int(argstr='--fibst=%d',desc='force a starting fibre for tracking - '+
                       'default=1, i.e. first fibre orientation. Only works if randfib==0')
    modeuler = traits.Bool(argstr='--modeuler',desc='use modified euler streamlining')
    rseed = traits.Bool(argstr='--rseed',desc='random seed')
    s2tastext = traits.Bool(argstr='--s2tastext',desc='output seed-to-target counts as a'+
                            ' text file (useful when seeding from a mesh)')

class ProbtrackxOutputSpec(FSLTraitedSpec):
    probtrackx = File(exists=True, desc='a text record of the command that was run')
    fdt_paths = File(exists=True, desc='a 3D image file containing the output '+
                     'connectivity distribution to the seed mask')
    waytotal = File(exists=True, desc='a text file containing a single number '+
                    'corresponding to the total number of generated tracts that '+
                    'have not been rejected by inclusion/exclusion mask criteria')
    
class Probtrackx(NEW_FSLCommand):

    """ Use FSL  probtrackx for tractography on bedpostx results
        Example:
        >>> from nipype.interfaces import fsl
        >>> pbx = Probtrackx( basename='subj1',
                            binaryMask='nodif_brain_mask',
                            seedFile='standard')
        >>> pbx.cmdline
        'probtrackx -s subj1 -m nodif_brain_mask -x standard'

    """
    _cmd = 'probtrackx'
    input_spec = ProbtrackxInputSpec
    output_spec = ProbtrackxOutputSpec
    
    def _list_outputs(self):        
        outputs = self.output_spec().get()
        if isdefined(self.inputs.outdir):
            outputs['probtrackx'] = self._gen_fname('probtrackx',cwd=self.inputs.outdir,
                                                    suffix='.log',change_ext=False)            
            outputs['waytotal'] = self._gen_fname('waytotal',cwd=self.inputs.outdir,
                                                  suffix='',change_ext=False)
            if isdefined(self.inputs.pathsfile):                
                outputs['fdt_paths'] = self._gen_fname(self.inputs.pathsfile,
                                                       cwd=self.inputs.outdir,suffix='')
            else:
                outputs['fdt_paths'] = self._gen_fname(self.inputs.pathsfile,
                                                       cwd=self.inputs.outdir,suffix='')
        else:
            outputs['probtrackx'] = self._gen_fname('probtrackx',suffix='.log',change_ext=False)
            outputs['waytotal'] = self._gen_fname('waytotal',suffix='',change_ext=False)
            if isdefined(self.inputs.pathsfile):
                outputs['fdt_paths'] = self._gen_fname(self.inputs.pathsfile,suffix='')
            else:
                outputs['fdt_paths'] = self._gen_fname('fdt_paths',suffix='')
                
        return outputs

    def _gen_filename(self, name):
        if name in ('probtrackx','waytotal','fdt_paths'):
            return self._list_outputs()[name]
        else:
            return None


class VecregInputSpec(FSLTraitedSpec):
    pass
class VecregOutputSpec(FSLTraitedSpec):
    pass
class Vecreg(NEW_FSLCommand):
    """Use FSL vecreg for registering vector data

    For complete details, see the `FDT Documentation
    <http://www.fmrib.ox.ac.uk/fsl/fdt/fdt_vecreg.html>`_

    """
    pass

##    opt_map = {'infile':            '-i %s',
##               'outfile':           '-o %s',
##               'refVolName':        '-r %s',
##               'verbose':           '-v',
##               'helpDoc':           '-h',
##               'tensor':            '--tensor',
##               'affineTmat':        '-t %s',
##               'warpFile':          '-w %s',
##               'interpolation':     '--interp %s',
##               'brainMask':         '-m %s'}
##
##    @property
##    def cmd(self):
##        """sets base command, immutable"""
##        return 'vecreg'
##
##    def inputs_help(self):
##        """Print command line documentation for Vecreg."""
##        print get_doc(self.cmd, self.opt_map, trap_error=False)
##
##    def _populate_inputs(self):
##        self.inputs = Bunch(infile=None,
##                            outfile=None,
##                            refVolName=None,
##                            verbose=None,
##                            helpDoc=None,
##                            tensor=None,
##                            affineTmat=None,
##                            warpFile=None,
##                            interpolation=None,
##                            brainMask=None,
##                            cwd=None)
##
##    def _parse_inputs(self):
##        """validate fsl vecreg options"""
##        allargs = super(Vecreg, self)._parse_inputs(skip=('infile', 'outfile',
##                                                         'refVolName', 'cwd'))
##
##        # Add source files to the args if they are specified
##        if self.inputs.infile:
##            allargs.insert(0, '-i ' + self.inputs.infile)
##        else:
##            raise AttributeError('vecreg needs an input file')
##
##        if self.inputs.outfile:
##            allargs.insert(1, '-o ' + self.inputs.outfile)
##        else:
##            outfile = self._gen_fname(self.inputs.infile,
##                                         cwd=self.inputs.cwd,
##                                         suffix='_vrg')
##            self.inputs.outfile = outfile
##            allargs.insert(1, '-o ' + outfile)
##
##        if self.inputs.refVolName:
##            allargs.insert(2, '-r ' + self.inputs.refVolName)
##        else:
##            raise AttributeError('vecreg needs a reference volume')
##
##        return allargs
##
##    def run(self, infile=None, outfile=None, refVolName=None, **inputs):
##        """Execute the command.
##
##        Examples
##        --------
##        >>> from nipype.interfaces import fsl
##        >>> vreg = fsl.Vecreg(infile='inf', outfile='infout', \
##                              refVolName='MNI152')
##        >>> vreg.cmdline
##        'vecreg -i inf -o infout -r MNI152'
##
##        """
##        if infile:
##            self.inputs.infile = infile
##
##        if outfile:
##            self.inputs.outfile = outfile
##
##        if refVolName:
##            self.inputs.refVolName = refVolName
##
##        self.inputs.update(**inputs)
##        return super(Vecreg, self).run()
##
##    def outputs(self):
##        """Returns a :class:`nipype.interfaces.base.Bunch` with outputs
##
##        Parameters
##        ----------
##        outfile : str
##            path/name of file of probtrackx image
##        """
##        outputs = Bunch(outfile=None)
##        return outputs
##
##    def aggregate_outputs(self):
##        outputs = self.outputs()
##        outputs.outfile = self._gen_fname(self.inputs.infile,
##                                             fname=self.inputs.outfile,
##                                             cwd=self.inputs.cwd,
##                                             suffix='_vrg',
##                                             check=True)
##        return outputs
##    aggregate_outputs.__doc__ = FSLCommand.aggregate_outputs.__doc__
##
##

class ProjthreshInputSpec(FSLTraitedSpec):
    pass
class ProjthreshOuputSpec(FSLTraitedSpec):
    pass
class Projthresh(NEW_FSLCommand):
    """Use FSL proj_thresh for thresholding some outputs of probtrack

        For complete details, see the `FDT Documentation
        <http://www.fmrib.ox.ac.uk/fsl/fdt/fdt_thresh.html>`_

    """
    pass

##    opt_map = {}
##
##    @property
##    def cmd(self):
##        """sets base command, immutable"""
##        return 'proj_thresh'
##
##    def inputs_help(self):
##        """Print command line documentation for Proj_thresh."""
##        print get_doc(self.cmd, self.opt_map, trap_error=False)
##
##    def _populate_inputs(self):
##        self.inputs = Bunch(volumes=None, threshold=None, cwd=None)
##
##    def _parse_inputs(self):
##        """validate fsl Proj_thresh options"""
##        allargs = []
##
##        if self.inputs.volumes:
##            for vol in self.inputs.volumes:
##                allargs.append(vol)
##        else:
##            raise AttributeError('proj_thresh needs input volumes')
##
##        if self.inputs.threshold:
##            allargs.append(repr(self.inputs.threshold))
##        else:
##            raise AttributeError('proj_thresh needs a threshold value')
##
##        return allargs
##
##    def run(self, volumes=None, threshold=None, **inputs):
##        """Execute the command.
##
##        Examples
##        --------
##        >>> from nipype.interfaces import fsl
##        >>> pThresh = fsl.ProjThresh(volumes = ['seeds_to_M1', 'seeds_to_M2'], \
##                                     threshold = 3)
##        >>> pThresh.cmdline
##        'proj_thresh seeds_to_M1 seeds_to_M2 3'
##
##        """
##
##        if volumes is not None:
##            self.inputs.volumes = filename_to_list(volumes)
##
##        if threshold is not None:
##            self.inputs.threshold = threshold
##
##        self.inputs.update(**inputs)
##        return super(ProjThresh, self).run()
##
##    def outputs(self):
##        """Returns a :class:`nipype.interfaces.base.Bunch` with outputs
##
##        Parameters
##        ----------
##        outfile : str
##            path/name of file of probtrackx image
##        """
##        outputs = Bunch(outfile=None)
##        return outputs
##
##    def aggregate_outputs(self):
##        outputs = self.outputs()
##        outputs.outfile = []
##
##        for files in self.inputs.volumes:
##            outputs.outfile.append(self._glob(files + '_proj_seg_thr_*'))
##
##        return outputs
##    aggregate_outputs.__doc__ = FSLCommand.aggregate_outputs.__doc__
##
##

class FindthebiggestInputSpec(FSLTraitedSpec):
    pass
class FindthebiggestOutputSpec(FSLTraitedSpec):
    pass
class Findthebiggest(NEW_FSLCommand):
    """Use FSL find_the_biggest for performing hard segmentation on
       the outputs of connectivity-based thresholding in probtrack.

       For complete details, see the `FDT
       Documentation. <http://www.fmrib.ox.ac.uk/fsl/fdt/fdt_biggest.html>`_

    """
    pass

##    opt_map = {}
##
##    @property
##    def cmd(self):
##        """sets base command, immutable"""
##        return 'find_the_biggest'
##
##    def inputs_help(self):
##        """Print command line documentation for Find_the_biggest."""
##        print get_doc(self.cmd, self.opt_map, trap_error=False)
##
##    def _populate_inputs(self):
##        self.inputs = Bunch(infiles=None,
##                            outfile=None)
##
##    def _parse_inputs(self):
##        """validate fsl Find_the_biggest options"""
##        allargs = []
##        if self.inputs.infiles:
##            allargs.insert(0, self.inputs.infiles)
##        if self.inputs.outfile:
##            allargs.insert(1, self.inputs.outfile)
##        else:
##            outfile = self._gen_fname(self.inputs.infiles,
##                                         fname=self.inputs.outfile,
##                                         suffix='_fbg')
##            allargs.insert(1, outfile)
##
##        return allargs
##
##    def run(self, infiles=None, outfile=None, **inputs):
##        """Execute the command.
##
##        Examples
##        --------
##        >>> from nipype.interfaces import fsl
##        >>> fBig = fsl.FindTheBiggest(infiles='all*', outfile='biggestOut')
##        >>> fBig.cmdline
##        'find_the_biggest all* biggestOut'
##
##        """
##        if infiles:
##            self.inputs.infiles = infiles
##        if not self.inputs.infiles:
##            raise AttributeError('find_the_biggest requires input file(s)')
##        if outfile:
##            self.inputs.outfile = outfile
##        return super(FindTheBiggest, self).run()
##
##    def outputs(self):
##        """Returns a :class:`nipype.interfaces.base.Bunch` with outputs
##
##        Parameters
##        ----------
##        outfile : str
##            path/name of file of probtrackx image
##        """
##        outputs = Bunch(outfile=None)
##        return outputs
##
##    def aggregate_outputs(self):
##        outputs = self.outputs()
##        outputs.outfile = self._gen_fname(self.inputs.infile,
##                                             fname=self.inputs.outfile,
##                                             suffix='_fbg',
##                                             check=True)
##
##        return outputs
##    
##    aggregate_outputs.__doc__ = FSLCommand.aggregate_outputs.__doc__
