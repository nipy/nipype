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

import os,shutil
import warnings

from nipype.interfaces.fsl.base import FSLCommand, FSLCommandInputSpec
from nipype.interfaces.base import Bunch, TraitedSpec, isdefined, File,Directory,\
    InputMultiPath
import enthought.traits.api as traits
warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

class DTIFitInputSpec(FSLCommandInputSpec):
    
    dwi = File(exists=True, desc = 'diffusion weighted image data file',
                  argstr='-k %s', position=0, mandatory=True)
    base_name = traits.Str("dtifit_", desc = 'base_name that all output files will start with',
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
    little_bit =  traits.Bool(desc = 'only process small area of brain',
                             argstr='--littlebit')

class DTIFitOutputSpec(TraitedSpec):
    
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

class DTIFit(FSLCommand):
    """ Use FSL  dtifit command for fitting a diffusion tensor model at each
    voxel
    
    Example
    -------
    
    >>> from nipype.interfaces import fsl
    >>> dti = fsl.DTIFit()
    >>> dti.inputs.dwi = 'diffusion.nii'
    >>> dti.inputs.bvecs = 'bvecs'
    >>> dti.inputs.bvals = 'bvals'
    >>> dti.inputs.base_name = 'TP'
    >>> dti.inputs.mask = 'mask.nii'
    >>> dti.cmdline
    'dtifit -k diffusion.nii -o TP -m mask.nii -r bvecs -b bvals'
    
    """
    
    _cmd = 'dtifit'
    input_spec = DTIFitInputSpec
    output_spec = DTIFitOutputSpec
        
    def _list_outputs(self):        
        outputs = self.output_spec().get()      
        for k in outputs.keys():
            if k not in ('outputtype','environ','args'):
                outputs[k] = self._gen_fname(self.inputs.base_name,suffix = '_'+k)
        return outputs
    
class EddyCorrectInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True,desc = '4D input file',argstr='%s', position=0, mandatory=True)
    out_file = File(desc = '4D output file',argstr='%s', position=1, genfile=True)
    ref_num = traits.Int(argstr='%d', position=2, desc='reference number',mandatory=True)

class EddyCorrectOutputSpec(TraitedSpec):
    eddy_corrected = File(exists=True, desc='path/name of 4D eddy corrected output file')

class EddyCorrect(FSLCommand):
    """ Use FSL eddy_correct command for correction of eddy current distortion
    
    Example
    -------
    
    >>> from nipype.interfaces import fsl
    >>> eddyc = fsl.EddyCorrect(in_file='diffusion.nii',out_file="diffusion_edc.nii", ref_num=0)
    >>> eddyc.cmdline
    'eddy_correct diffusion.nii diffusion_edc.nii 0'
    
    """
    _cmd = 'eddy_correct'
    input_spec = EddyCorrectInputSpec
    output_spec = EddyCorrectOutputSpec

    def _run_interface(self, runtime):
        if not isdefined(self.inputs.out_file):
            self.inputs.out_file = self._gen_fname(self.inputs.in_file,suffix = '_edc')
        runtime = super(EddyCorrect, self)._run_interface(runtime)
        if runtime.stderr:
            runtime.returncode = 1
        return runtime

    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['eddy_corrected'] = self.inputs.out_file
        if not isdefined(outputs['eddy_corrected']):
            outputs['eddy_corrected'] = self._gen_fname(self.inputs.in_file,suffix = '_edc')
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._list_outputs()['eddy_corrected']
        else:
            return None

class BEDPOSTXInputSpec(FSLCommandInputSpec):    
    dwi = File(exists=True, desc = 'diffusion weighted image data file',mandatory=True)
    mask = File(exists=True, desc = 'bet binary mask file',mandatory=True)    
    bvecs = File(exists=True, desc = 'b vectors file',mandatory=True)
    bvals = File(exists=True,desc = 'b values file',mandatory=True)
    bpx_directory = Directory('bedpostx',argstr='%s',usedefault=True,
                             desc='the name for this subject''s bedpostx folder')
  
    fibres = traits.Int(1,argstr='-n %d', desc='number of fibres per voxel')
    weight = traits.Float(1.00,argstr='-w %.2f', desc='ARD weight, more weight means less'+
                          ' secondary fibres per voxel')
    burn_period = traits.Int(1000,argstr='-b %d', desc='burnin period')
    jumps = traits.Int(1250,argstr='-j %d', desc='number of jumps')
    sampling = traits.Int(25,argstr='-s %d', desc='sample every')
    
class BEDPOSTXOutputSpec(TraitedSpec):
    bpx_out_directory = Directory(exists=True, field='dir', desc = 'path/name of directory with all '+
                             'bedpostx output files for this subject')
    xfms_directory = Directory(exists=True, field='dir', desc = 'path/name of directory with the '+
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

    
class BEDPOSTX(FSLCommand):
    """ Use FSL  bedpostx command for local modelling of diffusion parameters
    
    Example
    -------
    
    >>> from nipype.interfaces import fsl
    >>> bedp = fsl.BEDPOSTX(bpx_directory='subjdir', bvecs='bvecs', bvals='bvals', dwi='diffusion.nii', \
    mask='mask.nii', fibres=1)
    >>> bedp.cmdline
    'bedpostx subjdir -n 1'
    
    """
    
    _cmd = 'bedpostx'
    input_spec = BEDPOSTXInputSpec
    output_spec = BEDPOSTXOutputSpec
    can_resume = True

    def _run_interface(self, runtime):
        
        #create the subject specific bpx_directory           
        bpx_directory = os.path.join(os.getcwd(),self.inputs.bpx_directory)
        self.inputs.bpx_directory = bpx_directory
        if not os.path.exists(bpx_directory):
            os.makedirs(bpx_directory)
    
            # copy the dwi,bvals,bvecs, and mask files to that directory
            shutil.copyfile(self.inputs.mask,self._gen_fname('nodif_brain_mask',suffix='',cwd=self.inputs.bpx_directory))
            shutil.copyfile(self.inputs.dwi,self._gen_fname('data',suffix='',cwd=self.inputs.bpx_directory))
            shutil.copyfile(self.inputs.bvals,os.path.join(self.inputs.bpx_directory,'bvals'))
            shutil.copyfile(self.inputs.bvecs,os.path.join(self.inputs.bpx_directory,'bvecs'))

        return super(BEDPOSTX, self)._run_interface(runtime)

    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['bpx_out_directory'] = os.path.join(os.getcwd(),self.inputs.bpx_directory+'.bedpostX')
        outputs['xfms_directory'] = os.path.join(os.getcwd(),self.inputs.bpx_directory+'.bedpostX','xfms')
  
        for k in outputs.keys():
            if k not in ('outputtype','environ','args','bpx_out_directory','xfms_directory'):
                outputs[k]=[]
                
        for n in range(self.inputs.fibres):            
            outputs['merged_thsamples'].append(self._gen_fname('merged_th'+repr(n+1)+'samples',suffix='',cwd=outputs['bpx_out_directory']))
            outputs['merged_phsamples'].append(self._gen_fname('merged_ph'+repr(n+1)+'samples',suffix='',cwd=outputs['bpx_out_directory']))
            outputs['merged_fsamples'].append(self._gen_fname('merged_f'+repr(n+1)+'samples',suffix='',cwd=outputs['bpx_out_directory']))            
            outputs['mean_thsamples'].append(self._gen_fname('mean_th'+repr(n+1)+'samples',suffix='',cwd=outputs['bpx_out_directory']))
            outputs['mean_phsamples'].append(self._gen_fname('mean_ph'+repr(n+1)+'samples',suffix='',cwd=outputs['bpx_out_directory']))
            outputs['mean_fsamples'].append(self._gen_fname('mean_f'+repr(n+1)+'samples',suffix='',cwd=outputs['bpx_out_directory']))        
            outputs['dyads'].append(self._gen_fname('dyads'+repr(n+1),suffix='',cwd=outputs['bpx_out_directory']))            
        return outputs


class TBSS1PreprocInputSpec(FSLCommandInputSpec):
    img_list = traits.List(File(exists=True), mandatory=True,
                          desc = 'list with filenames of the FA images', sep = " ", argstr="%s")
    
class TBSS1PreprocOutputSpec(TraitedSpec):
    tbss_dir = Directory(exists=True, field='dir',
                        desc='path/name of directory with FA images')

class TBSS1Preproc(FSLCommand):
    """XXX UNSTABLE DO NOT USE
    
    Use FSL TBSS1Preproc for preparing your FA data in your TBSS working
    directory in the right format
        
    Example
    -------
    >>> import nipype.interfaces.fsl.dti as fsl
    >>> tbss1 = fsl.TBSS1Preproc(img_list=['functional.nii','functional2.nii','functional3.nii'])
    >>> tbss1.cmdline
    'tbss_1_preproc functional.nii functional2.nii functional3.nii'
    
    """
    
    _cmd = 'tbss_1_preproc'
    input_spec = TBSS1PreprocInputSpec
    output_spec = TBSS1PreprocOutputSpec

    def _run_interface(self, runtime):        
        for n in self.inputs.img_list:
            shutil.copyfile(n,os.path.basename(n))            
        runtime = super(TBSS1Preproc, self)._run_interface(runtime)
        if runtime.stderr:
            runtime.returncode = 1             
        return runtime

    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['tbss_dir'] = os.getcwd()            
        return outputs
    
    def _format_arg(self, name, spec, value):
        if name == "img_list":
            new_list = [os.path.basename(fname) for fname in self.inputs.img_list]
            return super(TBSS1Preproc, self)._format_arg("img_list", spec, new_list)
        return super(TBSS1Preproc, self)._format_arg(name, spec, value)
        
class TBSS2RegInputSpec(FSLCommandInputSpec):
    tbss_dir = Directory(exists=True, field='dir',
                        desc = 'path/name of directory containing the FA and origdata folders '+
                        'generated by tbss_1_preproc',
                        mandatory=True)
    _xor_inputs = ('FMRIB58FA', 'target_img','find_target')
    FMRIB58FA = traits.Bool(desc='use FMRIB58_FA_1mm as target for nonlinear registrations',
                            argstr='-T', xor=_xor_inputs)                            
    target_img = traits.Str(desc='use given image as target for nonlinear registrations',
                           argstr='-t %s', xor=_xor_inputs)
    find_target = traits.Bool(desc='find best target from all images in FA',
                             argstr='-n', xor=_xor_inputs)
    
class TBSS2RegOutputSpec(TraitedSpec):
    tbss_dir = Directory(exists=True, field='dir',
                        desc='path/name of directory containing the FA and origdata folders '+
                        'generated by tbss_1_preproc')
   
class TBSS2Reg(FSLCommand):
    """ XXX UNSTABLE DO NOT USE
    
    Use FSL TBSS2Reg for applying nonlinear registration of all FA images
    into standard space
    
    Example
    -------
    
    >>> import nipype.interfaces.fsl.dti as fsl
    >>> tbss2 = fsl.TBSS2Reg(tbss_dir=os.getcwd(),FMRIB58FA=True)
    >>> tbss2.cmdline
    'tbss_2_reg -T'
    
    """
    
    _cmd = 'tbss_2_reg'
    input_spec = TBSS2RegInputSpec
    output_spec = TBSS2RegOutputSpec

    def _run_interface(self, runtime):        
        runtime.cwd = self.inputs.tbss_dir
        return super(TBSS2Reg, self)._run_interface(runtime)

    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['tbss_dir'] = self.inputs.tbss_dir             
        return outputs

class TBSS3PostregInputSpec(FSLCommandInputSpec):
    tbss_dir = Directory(exists=True, field='dir',
                        desc = 'path/name of directory containing the FA and origdata '+
                        'folders generated by tbss_1_preproc',
                        mandatory=True)
    _xor_inputs = ('subject_mean', 'FMRIB58FA')
    subject_mean = traits.Bool(desc='derive mean_FA and mean_FA_skeleton from mean of all subjects in study',
                              argstr='-S', xor=_xor_inputs)
    FMRIB58FA = traits.Bool(desc='use FMRIB58_FA and its skeleton instead of study-derived mean and skeleton',
                            argstr='-T', xor=_xor_inputs)
   
class TBSS3PostregOutputSpec(TraitedSpec):
    tbss_dir = Directory(exists=True, field='dir',
                        desc='path/name of directory containing the FA, origdata, and '+
                        'stats folders generated by tbss_1_preproc and this command')
    all_FA = File(exists=True, desc='path/name of 4D volume with all FA images') 
    mean_FA_skeleton = File(exists=True, desc='path/name of 3D volume with mean FA skeleton')     
    mean_FA = File(exists=True, desc='path/name of 3D volume with mean FA image')    
  
class TBSS3Postreg(FSLCommand):
    """ XXX UNSTABLE DO NOT USE

    Use FSL TBSS3Postreg for creating the mean FA image and skeletonise it

    Example
    -------
    
    >>> import nipype.interfaces.fsl.dti as  fsl
    >>> tbss3 = fsl.TBSS3Postreg(subject_mean=True, tbss_dir='tbss_dir')
    >>> tbss3.cmdline
    'tbss_3_postreg -S'
    
    """
    
    _cmd = 'tbss_3_postreg'
    input_spec = TBSS3PostregInputSpec
    output_spec = TBSS3PostregOutputSpec
    
    def _run_interface(self, runtime):        
        runtime.cwd = self.inputs.tbss_dir
        runtime = super(TBSS3Postreg, self)._run_interface(runtime)
        if runtime.stderr:
            runtime.returncode = 1
        return runtime
    
    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['tbss_dir'] = self.inputs.tbss_dir
        stats = os.path.join(self.inputs.tbss_dir,'stats')
        outputs['all_FA'] = self._gen_fname('all_FA',
                                            cwd=os.path.abspath(stats),suffix='' )
        outputs['mean_FA_skeleton'] = self._gen_fname('mean_FA_skeleton',
                                                      cwd=os.path.abspath(stats),suffix='' )
        outputs['mean_FA'] = self._gen_fname('mean_FA',
                                             cwd=os.path.abspath(stats),suffix='' )        
        return outputs

class TBSS4PrestatsInputSpec(FSLCommandInputSpec):
    tbss_dir = Directory(exists=True, field='dir',
                        desc = 'path/name of directory containing the FA, origdata, and '+
                        'stats folders generated by tbss_1_preproc and tbss_3_postreg',
                        mandatory=True)
    threshold = traits.Float(argstr='%.3f', desc='threshold value',mandatory=True)

class TBSS4PrestatsOutputSpec(TraitedSpec):
    all_FA_skeletonised = File(exists=True, desc='path/name of 4D volume with all FA images skeletonized')
    mean_FA_skeleton_mask = File(exists=True, desc='path/name of mean FA skeleton mask') 
    tbss_dir = Directory(exists=True, field='dir',
                        desc = 'path/name of directory containing the FA, origdata, and stats '+
                        'folders generated by tbss_1_preproc and tbss_3_postreg')

class TBSS4Prestats(FSLCommand):
    """XXX UNSTABLE DO NOT USE

    Use FSL TBSS4Prestats thresholds the mean FA skeleton image at the
    chosen threshold
    
    Example
    -------
    
    >>> import nipype.interfaces.fsl.dti as fsl
    >>> tbss4 = fsl.TBSS4Prestats(threshold=0.3, tbss_dir="tbss_dir")
    >>> tbss4.cmdline
    'tbss_4_prestats 0.300'
    """
    
    _cmd = 'tbss_4_prestats'
    input_spec = TBSS4PrestatsInputSpec
    output_spec = TBSS4PrestatsOutputSpec

    def _run_interface(self, runtime):        
        runtime.cwd = self.inputs.tbss_dir
        return super(TBSS4Prestats, self)._run_interface(runtime)
   
    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['tbss_dir'] = self.inputs.tbss_dir
        stats = os.path.join(self.inputs.tbss_dir,'stats')
        outputs['all_FA_skeletonised'] = self._gen_fname('all_FA_skeletonised',
                                                         cwd=os.path.abspath(stats),
                                                         suffix='' )
        outputs['mean_FA_skeleton_mask'] = self._gen_fname('mean_FA_skeleton_mask',
                                                         cwd=os.path.abspath(stats),
                                                         suffix='' )
        return outputs

class RandomiseInputSpec(FSLCommandInputSpec):    
    in_file = File(exists=True,desc = '4D input file',argstr='-i %s', position=0, mandatory=True)
    base_name = traits.Str('tbss_',desc = 'the rootname that all generated files will have',
                          argstr='-o %s', position=1, usedefault=True)
    design_mat = File(exists=True,desc = 'design matrix file',argstr='-d %s', position=2, mandatory=True)
    tcon = File(exists=True,desc = 't contrasts file',argstr='-t %s', position=3, mandatory=True)
    fcon = File(exists=True,desc = 'f contrasts file',argstr='-f %s')
    mask = File(exists=True,desc = 'mask image',argstr='-m %s')
    x_block_labels = File(exists=True,desc = 'exchangeability block labels file',argstr='-e %s')   
    demean = traits.Bool(desc = 'demean data temporally before model fitting', argstr='-D')
    one_sample_group_mean =  traits.Bool(desc = 'perform 1-sample group-mean test instead of generic permutation test',
                                  argstr='-l')
    show_total_perms = traits.Bool(desc = 'print out how many unique permutations would be generated and exit',
                                 argstr='-q')
    show_info_parallel_mode = traits.Bool(desc = 'print out information required for parallel mode and exit',
                                  argstr='-Q')
    vox_p_values = traits.Bool(desc = 'output voxelwise (corrected and uncorrected) p-value images',
                            argstr='-x')
    tfce = traits.Bool(desc = 'carry out Threshold-Free Cluster Enhancement', argstr='-T')
    tfce2D = traits.Bool(desc = 'carry out Threshold-Free Cluster Enhancement with 2D optimisation',
                         argstr='--T2')
    f_only = traits.Bool(desc = 'calculate f-statistics only', argstr='--f_only')    
    raw_stats_imgs = traits.Bool(desc = 'output raw ( unpermuted ) statistic images', argstr='-R')
    p_vec_n_dist_files = traits.Bool(desc = 'output permutation vector and null distribution text files',
                                 argstr='-P')
    num_perm = traits.Int(argstr='-n %d', desc='number of permutations (default 5000, set to 0 for exhaustive)')
    seed = traits.Int(argstr='--seed %d', desc='specific integer seed for random number generator')
    var_smooth = traits.Int(argstr='-v %d', desc='use variance smoothing (std is in mm)')   
    c_thresh = traits.Float(argstr='-c %.2f', desc='carry out cluster-based thresholding')
    cm_thresh = traits.Float(argstr='-C %.2f', desc='carry out cluster-mass-based thresholding')
    f_c_thresh = traits.Float(argstr='-F %.2f', desc='carry out f cluster thresholding')
    f_cm_thresh = traits.Float(argstr='-S %.2f', desc='carry out f cluster-mass thresholding')    
    tfce_H = traits.Float(argstr='--tfce_H %.2f', desc='TFCE height parameter (default=2)')
    tfce_E = traits.Float(argstr='--tfce_E %.2f', desc='TFCE extent parameter (default=0.5)')
    tfce_C = traits.Float(argstr='--tfce_C %.2f', desc='TFCE connectivity (6 or 26; default=6)')    
    vxl = traits.List(traits.Int,argstr='--vxl %d', desc='list of numbers indicating voxelwise EVs'+
                      'position in the design matrix (list order corresponds to files in vxf option)')
    vxf = traits.List(traits.Int,argstr='--vxf %d', desc='list of 4D images containing voxelwise EVs'+
                      '(list order corresponds to numbers in vxl option)')
             
class RandomiseOutputSpec(TraitedSpec):
    tstat1_file = File(exists=True,desc = 'path/name of tstat image corresponding to the first t contrast')  

class Randomise(FSLCommand):
    """XXX UNSTABLE DO NOT USE

    FSL Randomise: feeds the 4D projected FA data into GLM
    modelling and thresholding
    in order to find voxels which correlate with your model
        
    Example
    -------
    >>> import nipype.interfaces.fsl.dti as fsl
    >>> rand = fsl.Randomise(in_file='allFA.nii', \
    mask = 'mask.nii', \
    tcon='design.con', \
    design_mat='design.mat')
    >>> rand.cmdline
    'randomise -i allFA.nii -o tbss_ -d design.mat -t design.con -m mask.nii'
    
    """
    
    _cmd = 'randomise'
    input_spec = RandomiseInputSpec
    output_spec = RandomiseOutputSpec
   
    def _list_outputs(self):        
        outputs = self.output_spec().get()        
        outputs['tstat1_file'] = self._gen_fname(self.inputs.base_name,suffix='_tstat1')
        return outputs

class ProbTrackXInputSpec(FSLCommandInputSpec):
    samplesbase_name = traits.Str(desc = 'the rootname/base_name for samples files',argstr='-s %s')
    bpx_directory = Directory(exists=True, field='dir', desc = 'path/name of directory with all '+
                             'bedpostx output files',mandatory=True)
    mask	 = File(exists=True, desc='bet binary mask file in diffusion space',
                 argstr='-m %s', mandatory=True)
    seed_file = 	File(exists=True, desc='seed volume, or voxel, or ascii file with multiple'+
                     'volumes, or freesurfer label file',argstr='-x %s', mandatory=True)	
    mode	= traits.Str(desc='options: simple (single seed voxel), seedmask (mask of seed voxels),'+
                     'twomask_symm (two bet binary masks) ', argstr='--mode=%s')                             
    target_masks	= InputMultiPath(File(exits=True),desc='list of target masks - '+
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
    seed_ref	= File(exists=True, desc='reference vol to define seed space in '+
                   'simple mode - diffusion space assumed if absent',
                   argstr='--seedref=%s')
    out_dir	= Directory(os.getcwd(),exists=True,argstr='--dir=%s',usedefault=True,
                       desc='directory to put the final volumes in')
    force_dir	= traits.Bool(desc='use the actual directory name given - i.e. '+
                          'do not add + to make a new directory',argstr='--forcedir')
    opd = traits.Bool(desc='outputs path distributions',argstr='--opd')
    correct_path_distribution	= traits.Bool(desc='correct path distribution for the length of the pathways',
                            argstr='--pd')
    os2t	= traits.Bool(desc='Outputs seeds to targets',argstr='--os2t')
    paths_file = File('nipype_fdtpaths',usedefault=True,argstr='--out=%s',
                     desc='produces an output file (default is fdt_paths)')
    avoid_mp = File(exists=True, desc='reject pathways passing through locations given by this mask',
                   argstr='--avoid=%s')
    stop_mask = File(exists=True,argstr='--stop=%s',
                      desc='stop tracking at locations given by this mask file')	
    xfm = File(exists=True, argstr='--xfm=%s',
               desc='transformation matrix taking seed space to DTI space '+
                '(either FLIRT matrix or FNIRT warp_field) - default is identity')    
    inv_xfm = File( argstr='--invxfm=%s',desc='transformation matrix taking DTI space to seed'+
                    ' space (compulsory when using a warp_field for seeds_to_dti)')
    n_samples = traits.Int(argstr='--nsamples=%d',desc='number of samples - default=5000')
    n_steps = traits.Int(argstr='--nsteps=%d',desc='number of steps per sample - default=2000')
    dist_thresh = traits.Float(argstr='--distthresh=%.3f',desc='discards samples shorter than '+
                              'this threshold (in mm - default=0)')    
    c_thresh = traits.Float(argstr='--cthr=%.3f',desc='curvature threshold - default=0.2')
    sample_random_points = traits.Bool(argstr='--sampvox',desc='sample random points within seed voxels')
    step_length = traits.Float(argstr='--steplength=%.3f',desc='step_length in mm - default=0.5')
    loop_check = traits.Bool(argstr='--loopcheck',desc='perform loop_checks on paths -'+
                            ' slower, but allows lower curvature threshold')
    use_anisotropy = traits.Bool(argstr='--usef',desc='use anisotropy to constrain tracking')
    rand_fib = traits.Enum(0,1,2,3,argstr='--randfib %d',desc='options: 0 - default, 1 - to randomly sample'+
                          ' initial fibres (with f > fibthresh), 2 - to sample in '+
                          'proportion fibres (with f>fibthresh) to f, 3 - to sample ALL '+
                          'populations at random (even if f<fibthresh)')
    fibst = traits.Int(argstr='--fibst=%d',desc='force a starting fibre for tracking - '+
                       'default=1, i.e. first fibre orientation. Only works if randfib==0')
    mod_euler = traits.Bool(argstr='--modeuler',desc='use modified euler streamlining')
    random_seed = traits.Bool(argstr='--rseed',desc='random seed')
    s2tastext = traits.Bool(argstr='--s2tastext',desc='output seed-to-target counts as a'+
                            ' text file (useful when seeding from a mesh)')

class ProbTrackXOutputSpec(TraitedSpec):
    log = File(exists=True, desc='path/name of a text record of the command that was run')
    fdt_paths = File(exists=True, desc='path/name of a 3D image file containing the output '+
                     'connectivity distribution to the seed mask')
    way_total = File(exists=True, desc='path/name of a text file containing a single number '+
                    'corresponding to the total number of generated tracts that '+
                    'have not been rejected by inclusion/exclusion mask criteria')
    targets = traits.List(File,exists=True,desc='a list with all generated seeds_to_target files')
    
class ProbTrackX(FSLCommand):
    """ Use FSL  probtrackx for tractography on bedpostx results
    
    Examples
    --------
    
    >>> from nipype.interfaces import fsl
    >>> pbx = fsl.ProbTrackX(samplesbase_name='merged', mask='mask.nii', \
    seed_file='MASK_average_thal_right.nii', mode='seedmask', \
    xfm='trans.mat', n_samples=3, n_steps=10, force_dir=True, opd=True, os2t=True, \
    bpx_directory='bedpostxout', target_masks = ['targets_MASK1.nii','targets_MASK2.nii'], \
    paths_file='nipype_fdtpaths', out_dir='.')
    >>> pbx.cmdline
    'probtrackx --forcedir -m mask.nii --mode=seedmask --nsamples=3 --nsteps=10 --opd --os2t --dir=. --out=nipype_fdtpaths -s merged -x MASK_average_thal_right.nii --targetmasks=targets.txt --xfm=trans.mat'

    """
    
    _cmd = 'probtrackx'
    input_spec = ProbTrackXInputSpec
    output_spec = ProbTrackXOutputSpec

    def _run_interface(self, runtime):
        if not isdefined(self.inputs.samplesbase_name):
            self.inputs.samplesbase_name = os.path.join(self.inputs.bpx_directory,'merged')
            
        if isdefined(self.inputs.target_masks):
            f = open("targets.txt","w")
            for target in self.inputs.target_masks:
                f.write("%s\n"%target)
            f.close()
            
        return super(ProbTrackX, self)._run_interface(runtime)
    
    def _format_arg(self, name, spec, value):
        if name == 'target_masks' and isdefined(value):
            fname = "targets.txt"
            
            return super(ProbTrackX, self)._format_arg(name, spec, [fname])
        else:
            return super(ProbTrackX, self)._format_arg(name, spec, value)
    
    def _list_outputs(self):        
        outputs = self.output_spec().get()        
        outputs['log'] = self._gen_fname('probtrackx',cwd=self.inputs.out_dir,
                                                suffix='.log',change_ext=False)            
        outputs['way_total'] = self._gen_fname('waytotal',cwd=self.inputs.out_dir,
                                              suffix='',change_ext=False)                        
        outputs['fdt_paths'] = self._gen_fname(self.inputs.paths_file,
                                               cwd=self.inputs.out_dir,suffix='')
      
        # handle seeds-to-target output files 
        if isdefined(self.inputs.target_masks):
            outputs['targets']=[]
            for target in self.inputs.target_masks:
                outputs['targets'].append(self._gen_fname('seeds_to_'+os.path.split(target)[1],
                                                          cwd=self.inputs.out_dir,suffix=''))        
        return outputs

class VecRegInputSpec(FSLCommandInputSpec):    
    in_file = File(exists=True,argstr='-i %s',desc='filename for input vector or tensor field',
                  mandatory=True)    
    out_file = File(argstr='-o %s',desc='filename for output registered vector or tensor field',
                   genfile=True)
    ref_vol = File(exists=True,argstr='-r %s',desc='filename for reference (target) volume',
                  mandatory=True)    
    affine_mat = File(exists=True,argstr='-t %s',desc='filename for affine transformation matrix')
    warp_field = File(exists=True,argstr='-w %s',desc='filename for 4D warp field for nonlinear registration')
    rotation_mat = File(exists=True,argstr='--rotmat=%s',desc='filename for secondary affine matrix'+
                  'if set, this will be used for the rotation of the vector/tensor field')
    rotation_warp = File(exists=True,argstr='--rotwarp=%s',desc='filename for secondary warp field'+
                   'if set, this will be used for the rotation of the vector/tensor field') 
    interpolation = traits.Enum("nearestneighbour", "trilinear", "sinc", "spline",argstr='--interp=%s',desc='interpolation method : '+
                        'nearestneighbour, trilinear (default), sinc or spline')
    mask = File(exists=True,argstr='-m %s',desc='brain mask in input space')
    ref_mask = File(exists=True,argstr='--refmask=%s',desc='brain mask in output space '+
                   '(useful for speed up of nonlinear reg)')

class VecRegOutputSpec(TraitedSpec):
    out_file = File(exists=True,desc='path/name of filename for the registered vector or tensor field')
    
class VecReg(FSLCommand):
    """Use FSL vecreg for registering vector data
    For complete details, see the `FDT Documentation
    <http://www.fmrib.ox.ac.uk/fsl/fdt/fdt_vecreg.html>`_
    
    Example
    -------
    
    >>> from nipype.interfaces import fsl
    >>> vreg = fsl.VecReg(in_file='diffusion.nii', \
                 affine_mat='trans.mat', \
                 ref_vol='mni.nii', \
                 out_file='diffusion_vreg.nii')
    >>> vreg.cmdline
    'vecreg -t trans.mat -i diffusion.nii -o diffusion_vreg.nii -r mni.nii'

    """
    
    _cmd = 'vecreg'
    input_spec = VecRegInputSpec
    output_spec = VecRegOutputSpec

    def _run_interface(self, runtime):        
        if not isdefined(self.inputs.out_file):
            pth,base_name = os.path.split(self.inputs.in_file) 
            self.inputs.out_file = self._gen_fname(base_name,cwd=os.path.abspath(pth),
                                                 suffix = '_vreg')
        return super(VecReg, self)._run_interface(runtime)
    
    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(outputs['out_file']) and isdefined(self.inputs.in_file):
            pth,base_name = os.path.split(self.inputs.in_file) 
            outputs['out_file'] = self._gen_fname(base_name,cwd=os.path.abspath(pth),
                                                 suffix = '_vreg')
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._list_outputs()[name]
        else:
            return None    

class ProjThreshInputSpec(FSLCommandInputSpec):
    in_files = traits.List(File,exists=True,argstr='%s',desc='a list of input volumes',
                          mandatory=True,position=0)
    threshold = traits.Int(argstr='%d',desc='threshold indicating minimum '+
                           'number of seed voxels entering this mask region',
                           mandatory=True,position=1)
    
class ProjThreshOuputSpec(TraitedSpec):
    out_files = traits.List(File,exists=True,desc='path/name of output volume after thresholding')
    
class ProjThresh(FSLCommand):
    """Use FSL proj_thresh for thresholding some outputs of probtrack
    For complete details, see the `FDT Documentation
    <http://www.fmrib.ox.ac.uk/fsl/fdt/fdt_thresh.html>`_
    
    Example
    -------
    
    >>> from nipype.interfaces import fsl
    >>> ldir = ['seeds_to_M1.nii', 'seeds_to_M2.nii']
    >>> pThresh = fsl.ProjThresh(in_files=ldir,threshold=3)
    >>> pThresh.cmdline
    'proj_thresh seeds_to_M1.nii seeds_to_M2.nii 3'

    """
    
    _cmd = 'proj_thresh'
    input_spec = ProjThreshInputSpec
    output_spec = ProjThreshOuputSpec

    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['out_files'] = []
        for name in self.inputs.in_files:
            cwd,base_name = os.path.split(name)
            outputs['out_files'].append(self._gen_fname(base_name,cwd=cwd,suffix='_proj_seg_thr_'+
                                                       repr(self.inputs.threshold)))            
        return outputs

class FindTheBiggestInputSpec(FSLCommandInputSpec):
    in_files = traits.List(File,exists=True,argstr='%s',desc='a list of input volumes or a singleMatrixFile',
                          position=0,mandatory=True)
    out_file = File(argstr='%s',desc='file with the resulting segmentation',position=2,genfile=True)   
    
class FindTheBiggestOutputSpec(TraitedSpec):
    out_file = File(exists=True,argstr='%s',desc='output file indexed in order of input files')
    
class FindTheBiggest(FSLCommand):
    """
    Use FSL find_the_biggest for performing hard segmentation on
    the outputs of connectivity-based thresholding in probtrack.
    For complete details, see the `FDT
    Documentation. <http://www.fmrib.ox.ac.uk/fsl/fdt/fdt_biggest.html>`_
    
    Example
    -------
    
    >>> from nipype.interfaces import fsl
    >>> ldir = ['seeds_to_M1.nii', 'seeds_to_M2.nii']
    >>> fBig = fsl.FindTheBiggest(in_files=ldir, out_file='biggestSegmentation')
    >>> fBig.cmdline
    'find_the_biggest seeds_to_M1.nii seeds_to_M2.nii biggestSegmentation'

    """
    
    _cmd='find_the_biggest'
    input_spec = FindTheBiggestInputSpec
    output_spec = FindTheBiggestOutputSpec
    
    def _run_interface(self, runtime):        
        if not isdefined(self.inputs.out_file):
            self.inputs.out_file = self._gen_fname('biggestSegmentation',suffix='')
        return super(FindTheBiggest, self)._run_interface(runtime)
    
    def _list_outputs(self):        
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(outputs['out_file']):
            outputs['out_file'] = self._gen_fname('biggestSegmentation',suffix = '')
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._list_outputs()[name]
        else:
            return None
