"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 4.1.4.

Examples
--------
See the docstrings of the individual classes for examples.

"""

import os,shutil
import warnings

from nipype.interfaces.fsl.base import FSLCommand, FSLCommandInputSpec
from nipype.interfaces.base import Bunch, TraitedSpec, isdefined, File,Directory,\
    InputMultiPath
import enthought.traits.api as traits
warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

class DtiFitInputSpec(FSLCommandInputSpec):
    
    dwi = File(exists=True, desc = 'diffusion weighted image data file',
                  argstr='-k %s', position=0, mandatory=True)
    basename = traits.Str("dtifit_", desc = 'basename that all output files will start with',
                           argstr='-o %s', position=1, usedefault=True)
    mask = File(exists=True, desc = 'bet binary mask file',
                argstr='-m %s', position=2, mandatory=True)    
    bvecs = File(exists=True, desc = 'b vectors file',
                argstr='-r %s', position=3, mandatory=True)
    bvals = File(exists=True,desc = 'b values file',
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

class DtiFitOutputSpec(TraitedSpec):
    
    V1 = File(exists = True, desc = 'path/name of file with the 1st eigenvector')
    V2 = File(exists = True, desc = 'path/name of file with the 2nd eigenvector')
    V3 = File(exists = True, desc = 'path/name of file with the 3rd eigenvector')
    L1 = File(exists = True, desc = 'path/name of file with the 1st eigenvalue')
    L2 = File(exists = True, desc = 'path/name of file with the 2nd eigenvalue')
    L3 = File(exists = True, desc = 'path/name of file with the 3rd eigenvalue')
    MD = File(exists = True, desc = 'path/name of file with the mean diffusivity')
    FA = File(exists = True, desc = 'path/name of file with the fractional anisotropy')
    S0 = File(exists = True, desc = 'path/name of file with the raw T2 signal with no '+
              'diffusion weighting')    

class DtiFit(FSLCommand):
    """ Use FSL  dtifit command for fitting a diffusion tensor model at each voxel
        Example:
        >>> from nipype.interfaces import fsl
        >>> dti = fsl.DtiFit()
        >>> dti.inputs.dwi = data.nii.gz
        >>> dti.inputs.bvec = bvecs
        >>> dti.inputs.bval = bvals
        >>> dti.inputs.basename = TP
        >>> dti.inputs.mask = nodif_brain_mask.nii.gz
        >>> dti.cmdline
        'dtifit -k data.nii.gz -o TP -m nodif_brain_mask.nii.gz -r bvecs -b bvals'
    """
    _cmd = 'dtifit'
    input_spec = DtiFitInputSpec
    output_spec = DtiFitOutputSpec
        
    def _list_outputs(self):        
        outputs = self.output_spec().get()      
        for k in outputs.keys():
            if k not in ('outputtype','environ','args'):
                outputs[k] = self._gen_fname(self.inputs.basename,suffix = '_'+k)
        return outputs
    
class EddyCorrectInputSpec(FSLCommandInputSpec):
    infile = File(exists=True,desc = '4D input file',argstr='%s', position=0, mandatory=True)
    outfile = File(desc = '4D output file',argstr='%s', position=1, genfile=True)
    refnum = traits.Int(argstr='%d', position=2, desc='reference number',mandatory=True)

class EddyCorrectOutputSpec(TraitedSpec):
    outfile = File(exists=True, desc='path/name of 4D eddy corrected output file')

class EddyCorrect(FSLCommand):
    """ Use FSL eddy_correct command for correction of eddy current distortion
        Example:
        >>> from nipype.interfaces import fsl
        >>> eddyc = fsl.EddyCorrect(infile='/data.nii.gz',refnum=0)
        >>> print dti.cmdline
        'eddy_correct data.nii.gz data_edc.nii.gz 0'
    """
    _cmd = 'eddy_correct'
    input_spec = EddyCorrectInputSpec
    output_spec = EddyCorrectOutputSpec

    def _run_interface(self, runtime):
        if not isdefined(self.inputs.outfile):
            self.inputs.outfile = self._gen_fname(self.inputs.infile,suffix = '_edc')
        runtime = super(EddyCorrect, self)._run_interface(runtime)
        if runtime.stderr:
            runtime.returncode = 1
        return runtime

    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['outfile'] = self.inputs.outfile
        if not isdefined(outputs['outfile']):
            outputs['outfile'] = self._gen_fname(self.inputs.infile,suffix = '_edc')
        return outputs

    def _gen_filename(self, name):
        if name is 'outfile':
            return self._list_outputs()[name]
        else:
            return None

class BedpostxInputSpec(FSLCommandInputSpec):    
    dwi = File(exists=True, desc = 'diffusion weighted image data file',mandatory=True)
    mask = File(exists=True, desc = 'bet binary mask file',mandatory=True)    
    bvecs = File(exists=True, desc = 'b vectors file',mandatory=True)
    bvals = File(exists=True,desc = 'b values file',mandatory=True)
    bpxdirectory = Directory('bedpostx',argstr='%s',usedefault=True,
                             desc='the name for this subject''s bedpostx folder')
  
    fibres = traits.Int(1,argstr='-n %d', desc='number of fibres per voxel',usedefault=True)
    weight = traits.Float(1.00,argstr='-w %.2f', desc='ARD weight, more weight means less'+
                          ' secondary fibres per voxel',usedefault=True)
    burn_period = traits.Int(1000,argstr='-b %d', desc='burnin period',usedefault=True)
    jumps = traits.Int(1250,argstr='-j %d', desc='number of jumps',usedefault=True)
    sampling = traits.Int(25,argstr='-s %d', desc='sample every',usedefault=True)
    
class BedpostxOutputSpec(TraitedSpec):
    bpxoutdirectory = Directory(exists=True, field='dir', desc = 'path/name of directory with all '+
                             'bedpostx output files for this subject')
    xfmsdirectory = Directory(exists=True, field='dir', desc = 'path/name of directory with the '+
                              'tranformation matrices')
    merged_thsamples = traits.List(File, exists=True,
                                    desc='a list of path/name of 4D volume with samples from the distribution on theta')
    merged_phsamples = traits.List(File, exists=True,
                                    desc='a list of path/name of file with samples from the distribution on phi')
    merged_fsamples = traits.List(File, exists=True,
                                   desc='a list of path/name of 4D volume with samples from the distribution on'+
                            ' anisotropic volume fraction')
    mean_thsamples = traits.List(File, exists=True,
                                  desc='a list of path/name of 3D volume with mean of distribution on theta')
    mean_phsamples = traits.List(File, exists=True,
                                  desc='a list of path/name of 3D volume with mean of distribution on phi')
    mean_fsamples = traits.List(File, exists=True,
                                 desc='a list of path/name of 3D volume with mean of distribution on f anisotropy')
    dyads = traits.List(File, exists=True,  desc='a list of path/name of mean of PDD distribution in vector form')

    
class Bedpostx(FSLCommand):
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
    can_resume = True

    def _run_interface(self, runtime):
        
        #create the subject specific bpxdirectory           
        bpxdirectory = os.path.join(os.getcwd(),self.inputs.bpxdirectory)
        self.inputs.bpxdirectory = bpxdirectory
        if not os.path.exists(bpxdirectory):
            os.makedirs(bpxdirectory)
    
            # copy the dwi,bvals,bvecs, and mask files to that directory
            shutil.copyfile(self.inputs.mask,self._gen_fname('nodif_brain_mask',suffix='',cwd=self.inputs.bpxdirectory))
            shutil.copyfile(self.inputs.dwi,self._gen_fname('data',suffix='',cwd=self.inputs.bpxdirectory))
            shutil.copyfile(self.inputs.bvals,os.path.join(self.inputs.bpxdirectory,'bvals'))
            shutil.copyfile(self.inputs.bvecs,os.path.join(self.inputs.bpxdirectory,'bvecs'))

        return super(Bedpostx, self)._run_interface(runtime)

    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['bpxoutdirectory'] = os.path.join(os.getcwd(),self.inputs.bpxdirectory+'.bedpostX')
        outputs['xfmsdirectory'] = os.path.join(os.getcwd(),self.inputs.bpxdirectory+'.bedpostX','xfms')
  
        for k in outputs.keys():
            if k not in ('outputtype','environ','args','bpxoutdirectory','xfmsdirectory'):
                outputs[k]=[]
                
        for n in range(self.inputs.fibres):            
            outputs['merged_thsamples'].append(self._gen_fname('merged_th'+repr(n+1)+'samples',suffix='',cwd=outputs['bpxoutdirectory']))
            outputs['merged_phsamples'].append(self._gen_fname('merged_ph'+repr(n+1)+'samples',suffix='',cwd=outputs['bpxoutdirectory']))
            outputs['merged_fsamples'].append(self._gen_fname('merged_f'+repr(n+1)+'samples',suffix='',cwd=outputs['bpxoutdirectory']))            
            outputs['mean_thsamples'].append(self._gen_fname('mean_th'+repr(n+1)+'samples',suffix='',cwd=outputs['bpxoutdirectory']))
            outputs['mean_phsamples'].append(self._gen_fname('mean_ph'+repr(n+1)+'samples',suffix='',cwd=outputs['bpxoutdirectory']))
            outputs['mean_fsamples'].append(self._gen_fname('mean_f'+repr(n+1)+'samples',suffix='',cwd=outputs['bpxoutdirectory']))        
            outputs['dyads'].append(self._gen_fname('dyads'+repr(n+1),suffix='',cwd=outputs['bpxoutdirectory']))            
        return outputs


class Tbss1preprocInputSpec(FSLCommandInputSpec):
    imglist = traits.List(File, exists=True, mandatory=True,
                          desc = 'list with filenames of the FA images')
    inexp = traits.Str('*.nii.gz',desc='the file pattern to be given to this command '+
                       '(note: the extension of the files need to be changed if different from .nii.gz)',
                       argstr='%s',usedefault=True)
    
class Tbss1preprocOutputSpec(TraitedSpec):
    tbssdir = Directory(exists=True, field='dir',
                        desc='path/name of directory with FA images')

class Tbss1preproc(FSLCommand):
    """
        Use FSL Tbss1preproc for preparing your FA data in your TBSS working
        directory in the right format
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
        for n in self.inputs.imglist:
            shutil.copyfile(n,self._gen_fname(n,suffix=''))            
        runtime = super(Tbss1preproc, self)._run_interface(runtime)
        if runtime.stderr:
            runtime.returncode = 1             
        return runtime

    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['tbssdir'] = os.getcwd()            
        return outputs
        
class Tbss2regInputSpec(FSLCommandInputSpec):
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
    
class Tbss2regOutputSpec(TraitedSpec):
    tbssdir = Directory(exists=True, field='dir',
                        desc='path/name of directory containing the FA and origdata folders '+
                        'generated by tbss_1_preproc')
   
class Tbss2reg(FSLCommand):
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

class Tbss3postregInputSpec(FSLCommandInputSpec):
    tbssdir = Directory(exists=True, field='dir',
                        desc = 'path/name of directory containing the FA and origdata '+
                        'folders generated by tbss_1_preproc',
                        mandatory=True)
    _xor_inputs = ('subjectmean', 'FMRIB58FA')
    subjectmean = traits.Bool(desc='derive mean_FA and mean_FA_skeleton from mean of all subjects in study',
                              argstr='-S', xor=_xor_inputs)
    FMRIB58FA = traits.Bool(desc='use FMRIB58_FA and its skeleton instead of study-derived mean and skeleton',
                            argstr='-T', xor=_xor_inputs)
   
class Tbss3postregOutputSpec(TraitedSpec):
    tbssdir = Directory(exists=True, field='dir',
                        desc='path/name of directory containing the FA, origdata, and '+
                        'stats folders generated by tbss_1_preproc and this command')
    all_FA = File(exists=True, desc='path/name of 4D volume with all FA images') 
    mean_FA_skeleton = File(exists=True, desc='path/name of 3D volume with mean FA skeleton')     
    mean_FA = File(exists=True, desc='path/name of 3D volume with mean FA image')    
  
class Tbss3postreg(FSLCommand):
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

class Tbss4prestatsInputSpec(FSLCommandInputSpec):
    tbssdir = Directory(exists=True, field='dir',
                        desc = 'path/name of directory containing the FA, origdata, and '+
                        'stats folders generated by tbss_1_preproc and tbss_3_postreg',
                        mandatory=True)
    threshold = traits.Float(argstr='%.3f', desc='threshold value',mandatory=True)

class Tbss4prestatsOutputSpec(TraitedSpec):
    all_FA_skeletonised = File(exists=True, desc='path/name of 4D volume with all FA images skeletonized')
    mean_FA_skeleton_mask = File(exists=True, desc='path/name of mean FA skeleton mask') 
    tbssdir = Directory(exists=True, field='dir',
                        desc = 'path/name of directory containing the FA, origdata, and stats '+
                        'folders generated by tbss_1_preproc and tbss_3_postreg')

class Tbss4prestats(FSLCommand):
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
        outputs['mean_FA_skeleton_mask'] = self._gen_fname('mean_FA_skeleton_mask',
                                                         cwd=os.path.abspath(stats),
                                                         suffix='' )
        return outputs

class RandomiseInputSpec(FSLCommandInputSpec):    
    infile = File(exists=True,desc = '4D input file',argstr='-i %s', position=0, mandatory=True)
    basename = traits.Str('tbss_',desc = 'the rootname that all generated files will have',
                          argstr='-o %s', position=1, usedefault=True)
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
             
class RandomiseOutputSpec(TraitedSpec):
    tstat1file = File(exists=True,desc = 'path/name of tstat image corresponding to the first t contrast')  

class Randomise(FSLCommand):
    """
        FSL Randomise: feeds the 4D projected FA data into GLM modelling and thresholding
        in order to find voxels which correlate with your model
        Example:
        >>> from nipype.interfaces import fsl
        >>> rand = fsl.Randomise(infile='allFA',
                                 mask = 'all_FA_skeleton_mask'
                                 tcon='design.con',
                                 designmat='design.mat')
        >>> rand.cmdline
        'randomise -i allFA -o tbss -t design.con -d design.mat -m all_FA_skeleton_mask'
    """
    _cmd = 'randomise'
    input_spec = RandomiseInputSpec
    output_spec = RandomiseOutputSpec
   
    def _list_outputs(self):        
        outputs = self.output_spec().get()        
        outputs['tstat1file'] = self._gen_fname(self.inputs.basename,suffix='_tstat1')
        return outputs

class ProbtrackxInputSpec(FSLCommandInputSpec):
    samplesbasename = traits.Str(desc = 'the rootname/basename for samples files',argstr='-s %s')
    bpxdirectory = Directory(exists=True, field='dir', desc = 'path/name of directory with all '+
                             'bedpostx output files',mandatory=True)
    mask	 = File(exists=True, desc='bet binary mask file in diffusion space',
                 argstr='-m %s', mandatory=True)
    seedfile = 	File(exists=True, desc='seed volume, or voxel, or ascii file with multiple'+
                     'volumes, or freesurfer label file',argstr='-x %s', mandatory=True)	
    mode	= traits.Str(desc='options: simple (single seed voxel), seedmask (mask of seed voxels),'+
                     'twomask_symm (two bet binary masks) ', argstr='--mode=%s')                             
    targetmasks	= InputMultiPath(File(exits=True),desc='list of target masks - '+
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
    outdir	= Directory(os.getcwd(),exists=True,argstr='--dir=%s',usedefault=True,
                       desc='directory to put the final volumes in')
    forcedir	= traits.Bool(desc='use the actual directory name given - i.e. '+
                          'do not add + to make a new directory',argstr='--forcedir')
    opd = traits.Bool(desc='outputs path distributions',argstr='--opd')
    correctpd	= traits.Bool(desc='correct path distribution for the length of the pathways',
                            argstr='--pd')
    os2t	= traits.Bool(desc='Outputs seeds to targets',argstr='--os2t')
    pathsfile = File('nipype_fdtpaths',usedefault=True,argstr='--out=%s',
                     desc='produces an output file (default is fdt_paths)')
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

class ProbtrackxOutputSpec(TraitedSpec):
    probtrackx = File(exists=True, desc='path/name of a text record of the command that was run')
    fdt_paths = File(exists=True, desc='path/name of a 3D image file containing the output '+
                     'connectivity distribution to the seed mask')
    waytotal = File(exists=True, desc='path/name of a text file containing a single number '+
                    'corresponding to the total number of generated tracts that '+
                    'have not been rejected by inclusion/exclusion mask criteria')
    targets = traits.List(File,exists=True,desc='a list with all generated seeds_to_target files')
    
class Probtrackx(FSLCommand):

    """ Use FSL  probtrackx for tractography on bedpostx results
        Example:
        >>> from nipype.interfaces import fsl
        >>> pbx = fsl.Probtrackx(samplesbasename='merged', mask='nodif_brain_mask.nii.gz',
                     seedfile='MASK_average_thal_right.nii.gz', mode='seedmask',
                     xfm='standard2diff.mat', nsamples=3, nsteps=10, forcedir=True, opd=True, os2t=True,
                     outdir='dtiout', targetmasks = ['THAL2CTX_right/targets_MASK1.nii','THAL2CTX_right/targets_MASK2.nii'],
                     pathsfile='nipype_fdtpaths')
        >>> pbx.cmdline
        'probtrackx --forcedir -m nodif_brain_mask.nii.gz --mode=seedmask
        --nsamples=3 --nsteps=10 --opd --os2t --dir=dtiout --out=nipype_fdtpaths
        -s merged -x MASK_average_thal_right.nii.gz
        --targetmasks=/THAL2CTX_right/targets.txt --xfm=standard2diff.mat'
    """
    _cmd = 'probtrackx'
    input_spec = ProbtrackxInputSpec
    output_spec = ProbtrackxOutputSpec

    def _run_interface(self, runtime):
        if not isdefined(self.inputs.samplesbasename):
            self.inputs.samplesbasename = os.path.join(self.inputs.bpxdirectory,'merged')
            
        return super(Probtrackx, self)._run_interface(runtime)
    
    def _format_arg(self, name, spec, value):
        if name == 'targetmasks':
            fname = "targets.txt"
            f = open(fname,"w")
            for target in value:
                f.write("%s\n"%target)
            f.close()
            return super(Probtrackx, self)._format_arg(name, spec, [fname])
        else:
            return super(Probtrackx, self)._format_arg(name, spec, value)
    
    def _list_outputs(self):        
        outputs = self.output_spec().get()        
        outputs['probtrackx'] = self._gen_fname('probtrackx',cwd=self.inputs.outdir,
                                                suffix='.log',change_ext=False)            
        outputs['waytotal'] = self._gen_fname('waytotal',cwd=self.inputs.outdir,
                                              suffix='',change_ext=False)                        
        outputs['fdt_paths'] = self._gen_fname(self.inputs.pathsfile,
                                               cwd=self.inputs.outdir,suffix='')
      
        # handle seeds-to-target output files 
        if isdefined(self.inputs.targetmasks):
            outputs['targets']=[]
            for target in self.inputs.targetmasks:
                outputs['targets'].append(self._gen_fname('seeds_to_'+os.path.split(target)[1],
                                                          cwd=self.inputs.outdir,suffix=''))        
        return outputs

class VecregInputSpec(FSLCommandInputSpec):    
    infile = File(exists=True,argstr='-i %s',desc='filename for input vector or tensor field',
                  mandatory=True)    
    outfile = File(argstr='-o %s',desc='filename for output registered vector or tensor field',
                   genfile=True)
    refvol = File(exists=True,argstr='-r %s',desc='filename for reference (target) volume',
                  mandatory=True)    
    affinemat = File(exists=True,argstr='-t %s',desc='filename for affine transformation matrix')
    warpfield = File(exists=True,argstr='-w %s',desc='filename for 4D warp field for nonlinear registration')
    rotmat = File(exists=True,argstr='--rotmat=%s',desc='filename for secondary affine matrix'+
                  'if set, this will be used for the rotation of the vector/tensor field')
    rotwarp = File(exists=True,argstr='--rotwarp=%s',desc='filename for secondary warp field'+
                   'if set, this will be used for the rotation of the vector/tensor field') 
    interp = traits.Str(argstr='--interp=%s',desc='interpolation method : '+
                        'nearestneighbour, trilinear (default), sinc or spline')
    mask = File(exists=True,argstr='-m %s',desc='brain mask in input space')
    refmask = File(exists=True,argstr='--refmask=%s',desc='brain mask in output space '+
                   '(useful for speed up of nonlinear reg)')

class VecregOutputSpec(TraitedSpec):
    outfile = File(exists=True,desc='path/name of filename for the registered vector or tensor field')
    
class Vecreg(FSLCommand):
    """Use FSL vecreg for registering vector data
    For complete details, see the `FDT Documentation
    <http://www.fmrib.ox.ac.uk/fsl/fdt/fdt_vecreg.html>`_
    Example:
    >>> from nipype.interfaces import fsl
    >>> vreg = fsl.Vecreg(infile='dyads1.nii.gz',
                 affinemat='diff2standard.mat',
                 refvol='/usr/share/fsl/data/standard/MNI152_T1_2mm.nii.gz')
    >>> print vreg.cmdline
    'vecreg -t diff2standard.mat -i dyads1.nii.gz -o dyads1_vreg.nii.gz
    -r /usr/share/fsl/data/standard/MNI152_T1_2mm.nii.gz'
    """
    _cmd = 'vecreg'
    input_spec = VecregInputSpec
    output_spec = VecregOutputSpec

    def _run_interface(self, runtime):        
        if not isdefined(self.inputs.outfile):
            pth,basename = os.path.split(self.inputs.infile) 
            self.inputs.outfile = self._gen_fname(basename,cwd=os.path.abspath(pth),
                                                 suffix = '_vreg')
        return super(Vecreg, self)._run_interface(runtime)
    
    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['outfile'] = self.inputs.outfile
        if not isdefined(outputs['outfile']) and isdefined(self.inputs.infile):
            pth,basename = os.path.split(self.inputs.infile) 
            outputs['outfile'] = self._gen_fname(basename,cwd=os.path.abspath(pth),
                                                 suffix = '_vreg')
        return outputs

    def _gen_filename(self, name):
        if name is 'outfile':
            return self._list_outputs()[name]
        else:
            return None    

class ProjthreshInputSpec(FSLCommandInputSpec):
    infiles = traits.List(File,exists=True,argstr='%s',desc='a list of input volumes',
                          mandatory=True,position=0)
    threshold = traits.Int(argstr='%d',desc='threshold indicating minimum '+
                           'number of seed voxels entering this mask region',
                           mandatory=True,position=1)
    
class ProjthreshOuputSpec(TraitedSpec):
    outfiles = traits.List(File,exists=True,desc='path/name of output volume after thresholding')
    
class Projthresh(FSLCommand):
    """Use FSL proj_thresh for thresholding some outputs of probtrack
        For complete details, see the `FDT Documentation
        <http://www.fmrib.ox.ac.uk/fsl/fdt/fdt_thresh.html>`_
        Example:
        >>> from nipype.interfaces import fsl
        >>> ldir = glob('seeds_to_M*')
        >>> pThresh = fsl.Projthresh(infiles=ldir,threshold=3)
        >>> pThresh.cmdline
        'proj_thresh seeds_to_M1 seeds_to_M2 3000'

    """ 
    _cmd = 'proj_thresh'
    input_spec = ProjthreshInputSpec
    output_spec = ProjthreshOuputSpec

    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['outfiles'] = []
        for name in self.inputs.infiles:
            cwd,basename = os.path.split(name)
            outputs['outfiles'].append(self._gen_fname(basename,cwd=cwd,suffix='_proj_seg_thr_'+
                                                       repr(self.inputs.threshold)))            
        return outputs

class FindthebiggestInputSpec(FSLCommandInputSpec):
    infiles = traits.List(File,exists=True,argstr='%s',desc='a list of input volumes or a singleMatrixFile',
                          position=0,mandatory=True)
    labelfile = File(exists=True,argstr='%s',desc='label file')
    outfile = File(argstr='%s',desc='file with the resulting segmentation',position=-1,genfile=True)   
    
class FindthebiggestOutputSpec(TraitedSpec):
    outfile = File(exists=True,argstr='%s',desc='output file indexed in order of input files')
    
class FindTheBiggest(FSLCommand):
    """Use FSL find_the_biggest for performing hard segmentation on
       the outputs of connectivity-based thresholding in probtrack.
       For complete details, see the `FDT
       Documentation. <http://www.fmrib.ox.ac.uk/fsl/fdt/fdt_biggest.html>`_
       Example:
        >>> from nipype.interfaces import fsl
        >>> ldir = glob('seeds_to_M*')
        >>> fBig = fsl.FindTheBiggest(infiles=ldir, outfile='biggestSegmentation')
        >>> fBig.cmdline
        'find_the_biggest  seeds_to_M1 seeds_to_M2 biggestSegmentation'      

    """    
    _cmd='find_the_biggest'
    input_spec = FindthebiggestInputSpec
    output_spec = FindthebiggestOutputSpec
    
    def _run_interface(self, runtime):        
        if not isdefined(self.inputs.outfile):
            self.inputs.outfile = self._gen_fname('biggestSegmentation',suffix='')
        return super(FindTheBiggest, self)._run_interface(runtime)
    
    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['outfile'] = self.inputs.outfile
        if not isdefined(outputs['outfile']):
            outputs['outfile'] = self._gen_fname('biggestSegmentation',suffix = '')
        return outputs

    def _gen_filename(self, name):
        if name is 'outfile':
            return self._list_outputs()[name]
        else:
            return None





