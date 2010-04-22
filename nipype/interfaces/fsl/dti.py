"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 4.1.4.

Examples
--------
See the docstrings of the individual classes for examples.

"""

import os
import re
import subprocess
from glob import glob
import warnings

from nipype.interfaces.fsl.base import FSLCommand
from nipype.interfaces.fsl.base import NEW_FSLCommand, FSLTraitedSpec
from nipype.interfaces.base import Bunch, TraitedSpec, isdefined, File,\
    InputMultiPath,Directory

from nipype.utils.filemanip import fname_presuffix, filename_to_list
from nipype.utils.docparse import get_doc

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
    outfile = File(exists=True,desc = '4D output file',argstr='%s', position=1, genfile=True)
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
                             desc = 'directory with all bedpostx standard files: data, bvecs, bvals, nodif_brain_mask',
                             argstr='%s', position=0, mandatory=True)
    fibres = traits.Int(argstr='-n %d', desc='number of fibres per voxel, default 2')
    weight = traits.Float(argstr='-w %.2f', desc='ARD weight, more weight means less secondary fibres per voxel, default 1')
    burn_period = traits.Int(argstr='-b %d', desc='burnin period, default 1000')
    jumps = traits.Int(argstr='-j %d', desc='number of jumps, default 1250')
    sampling = traits.Int(argstr='-s %d', desc='sample every, default 25')
    
class BedpostxOutputSpec(FSLTraitedSpec):
    bpxdirectory = Directory(exists=True, field='dir', desc = 'path/name of directory with all bedpostx output files')
    xfmsdirectory = Directory(exists=True, field='dir', desc = 'path/name of directory with the tranformation matrices')
    merged_th1samples = File(exists=True, desc='path/name of 4D volume with samples from the distribution on theta')
    merged_ph1samples = File(exists=True, desc='path/name of file with samples from the distribution on phi')
    merged_f1samples = File(exists=True,desc='path/name of 4D volume with samples from the distribution on anisotropic volume fraction')
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
        >>> bedp = fsl.Bedpostx(directory='subjdir', fibres=1)
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
                        desc='path/name of directory in which this command will be executed (note: directory must contain the FA images)',
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
                        desc = 'path/name of directory containing the FA and origdata folders generated by tbss_1_preproc',
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
                        desc='path/name of directory containing the FA and origdata folders generated by tbss_1_preproc')
   
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
                        desc = 'path/name of directory containing the FA and origdata folders generated by tbss_1_preproc',
                        mandatory=True)
    _xor_inputs = ('subjectmean', 'FMRIB58FA')
    subjectmean = traits.Bool(desc='derive mean_FA and mean_FA_skeleton from mean of all subjects in study',
                              argstr='-S', xor=_xor_inputs)
    FMRIB58FA = traits.Bool(desc='use FMRIB58_FA and its skeleton instead of study-derived mean and skeleton',
                            argstr='-T', xor=_xor_inputs)
   
class Tbss3postregOutputSpec(FSLTraitedSpec):
    tbssdir = Directory(exists=True, field='dir',
                        desc='path/name of directory containing the FA, origdata, and stats folders generated by tbss_1_preproc and this command')
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
                        desc = 'path/name of directory containing the FA, origdata, and stats folders generated by tbss_1_preproc and tbss_3_postreg',
                        mandatory=True)
    threshold = traits.Float(argstr='%.3f', desc='threshold value',mandatory=True)

class Tbss4prestatsOutputSpec(FSLTraitedSpec):
    all_FA_skeletonised = File(exists=True, desc='path/name of 4D volume with all FA images skeletonized')
    tbssdir = Directory(exists=True, field='dir',
                        desc = 'path/name of directory containing the FA, origdata, and stats folders generated by tbss_1_preproc and tbss_3_postreg')

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


#----------------------------------------------------------------------------------------------------------------
## randomise -i all_FA_skeletonised -o tbss -m mean_FA_skeleton_mask -d design.mat -t design.con -n 500 --T2 -V
class Randomise(FSLCommand):
    """
        FSL Randomise: feeds the 4D projected FA data into GLM modelling and thresholding
        in order to find voxels which correlate with your model
    """
    opt_map = {'input_4D':                           '-i %s',
              'output_rootname':                    '-o %s',
              'demean_data':                        '-D',
              'one_sample_gmean':                   '-1',
              'mask_image':                         '-m %s',
              'design_matrix':                      '-d %s',
              't_contrast':                         '-t %s',
              'f_contrast':                         '-f %s',
              'xchange_block_labels':               '-e %s',
              'print_unique_perm':                  '-q',
              'print_info_parallelMode':            '-Q',
              'num_permutations':                   '-n %d',
              'vox_pvalus':                         '-x',
              'fstats_only':                        '--fonly',
              'thresh_free_cluster':                '-T',
              'thresh_free_cluster_2Dopt':          '--T2',
              'cluster_thresholding':               '-c %0.2f',
              'cluster_mass_thresholding':          '-C %0.2f',
              'fcluster_thresholding':              '-F %0.2f',
              'fcluster_mass_thresholding':         '-S %0.2f',
              'variance_smoothing':                 '-v %0.2f',
              'diagnostics_off':                    '--quiet',
              'output_raw':                         '-R',
              'output_perm_vect':                   '-P',
              'int_seed':                           '--seed %d',
              'TFCE_height_param':                  '--tfce_H %0.2f',
              'TFCE_extent_param':                  '--tfce_E %0.2f',
              'TFCE_connectivity':                  '--tfce_C %0.2f',
              'list_num_voxel_EVs_pos':             '--vxl %s',
              'list_img_voxel_EVs':                 '--vxf %s'}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'randomise'

    def inputs_help(self):
        """Print command line documentation for randomise."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(input_4D=None,
                            output_rootname=None,
                            demean_data=None,
                            one_sample_gmean=None,
                            mask_image=None,
                            design_matrix=None,
                            t_contrast=None,
                            f_contrast=None,
                            xchange_block_labels=None,
                            print_unique_perm=None,
                            print_info_parallelMode=None,
                            num_permutations=None,
                            vox_pvalus=None,
                            fstats_only=None,
                            thresh_free_cluster=None,
                            thresh_free_cluster_2Dopt=None,
                            cluster_thresholding=None,
                            cluster_mass_thresholding=None,
                            fcluster_thresholding=None,
                            fcluster_mass_thresholding=None,
                            variance_smoothing=None,
                            diagnostics_off=None,
                            output_raw=None,
                            output_perm_vect=None,
                            int_seed=None,
                            TFCE_height_param=None,
                            TFCE_extent_param=None,
                            TFCE_connectivity=None,
                            list_num_voxel_EVs_pos=None,
                            list_img_voxel_EVs=None)

    def _parse_inputs(self):
        """validate fsl randomise options"""
        allargs = super(Randomise, self)._parse_inputs(skip=('input_4D', 'output_rootname'))

        # Add source files to the args if they are specified
        if self.inputs.input_4D:
            allargs.insert(0, '-i ' + self.inputs.input_4D)
        else:
            raise AttributeError('randomise needs a 4D image as input')

        if self.inputs.output_rootname:
            allargs.insert(1, '-o ' + self.inputs.output_rootname)

        return allargs

    def run(self, input_4D=None, output_rootname=None, **inputs):
        """Execute the command.
        >>> from nipype.interfaces import fsl
        >>> rand = fsl.Randomise(input_4D='infile2',output_rootname='outfile2',f_contrast='infile.f',one_sample_gmean=True,int_seed=4)
        >>> rand.cmdline
        'randomise -i infile2 -o outfile2 -f infile.f --seed 4 -1'
        """
        if input_4D:
            self.inputs.input_4D = input_4D
        if not self.inputs.input_4D:
            raise AttributeError('randomise requires an input file')

        if output_rootname:
            self.inputs.output_rootname = output_rootname

        self.inputs.update(**inputs)
        results = self._runner()
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs()
        return results

    def outputs_help(self):
        """
        Parameters
        ----------
        (all default to None and are unset)

        outfile : /path/to/outfile
            path and filename to randomise generated files
        """
        print self.outputs_help.__doc__

    def outputs(self):
        """Returns a :class:`nipype.interfaces.base.Bunch` with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string,file
                path/name of file of randomise image
        """
        outputs = Bunch(tstat=None)
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        outputs = self.outputs()
        randFiles = glob(self.inputs.output_rootname + '*')
        outputs.tstat = []

        for imagePath in randFiles:
            if re.search('tstat', imagePath):
                outputs.tstat.append(imagePath)

        if not outputs.tstat:
            raise AttributeError('randomise did not create the desired files')

        return outputs

class Probtrackx(FSLCommand):

    """Use FSL  probtrackx for tractography and connectivity-based segmentation
    """

    opt_map = {'basename':                      '-s %s',
               'binaryMask':                    '-m %s',
               'seedFile':                      '-x %s',
               'verbose':                       '-V %d',
               'helpDoc':                       '-h',
               'mode':                          '--mode=%s',  # options: simple, seedmask
               'targetMasks':                   '--targetmasks=%s',
               'secondMask':                    '--mask2=%s',
               'wayPointsMask':                 '--waypoints=%s',
               'activateNetwork':               '--network',
               'surfaceDescriptor':             '--mesh=%s',
               'refVol4seedVoxels':             '--seedref=%s',
               'finalVolDir':                   '--dir=%s',
               'useActualDirName':              '--forcedir',
               'outputPathDistribution':        '--opd',
               'correctPathDistribution':       '--pd',
               'outputSeeds2targets':           '--os2t',
               'outfBasename':                   '-o %s',
               'rejectMaskPaths':               '--avoid=%s',
               'noTrackingMask':                '--stop=%s',
               'preferedOrientation':           '--prefdir=%s',
               'Tmatrix':                       '--xfm=%s',
               'numOfSamples':                  '-P %d',
               'nstepsPersample':               '-S %d',
               'curvatureThreshold':            '-c %.2f',
               'steplength':                    '--steplength=%.2f',
               'performLoopcheck':              '-l',
               'useAnisotropy':                 '-f',
               'selectRandfibres':              '--randfib',
               'forceAstartingFibre':           '--fibst=%d',
               'modifiedEulerStreamlining':     '--modeuler',
               'randSeed':                      '--rseed',
               'outS2Tcounts':                  '--seedcountastext'}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'probtrackx'

    def inputs_help(self):
        """Print command line documentation for probtrackx."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(basename=None,
                                binaryMask=None,
                                seedFile=None,
                                verbose=None,
                                helpDoc=None,
                                mode=None,
                                targetMasks=None,
                                secondMask=None,
                                wayPointsMask=None,
                                activateNetwork=None,
                                surfaceDescriptor=None,
                                refVol4seedVoxels=None,
                                finalVolDir=None,
                                useActualDirName=None,
                                outputPathDistribution=None,
                                correctPathDistribution=None,
                                outputSeeds2targets=None,
                                outfBasename=None,
                                rejectMaskPaths=None,
                                noTrackingMask=None,
                                preferedOrientation=None,
                                Tmatrix=None,
                                numOfSamples=None,
                                nstepsPersample=None,
                                curvatureThreshold=None,
                                steplength=None,
                                performLoopcheck=None,
                                useAnisotropy=None,
                                selectRandfibres=None,
                                forceAstartingFibre=None,
                                modifiedEulerStreamlining=None,
                                randSeed=None,
                                outS2Tcounts=None)

    def _parse_inputs(self):
        """validate fsl probtrackx options"""
        allargs = super(Probtrackx, self)._parse_inputs(skip=('basename', 'binaryMask', 'seedFile'))

        # Add source files to the args if they are specified
        if self.inputs.basename:
            allargs.insert(0, '-s ' + self.inputs.basename)
        else:
            raise AttributeError('probtrackx needs a basename as input')

        if self.inputs.binaryMask:
            allargs.insert(1, '-m ' + self.inputs.binaryMask)
        else:
            raise AttributeError('probtrackx needs a binary mask as input')

        if self.inputs.seedFile:
            allargs.insert(2, '-x ' + self.inputs.seedFile)
        else:
            raise AttributeError('probtrackx needs a seed volume, or voxel, \
                                    or ascii file with multiple volumes as input')

        return allargs

    def run(self, basename=None, binaryMask=None, seedFile=None, noseTest=False, **inputs):
        """Execute the command.
        >>> from nipype.interfaces import fsl
        >>> pbx = Probtrackx(basename='subj1',binaryMask='nodif_brain_mask',seedFile='standard')
        >>> pbx.cmdline
        'probtrackx -s subj1 -m nodif_brain_mask -x standard'
        """

        if basename:
            self.inputs.basename = basename

        if binaryMask:
            self.inputs.binaryMask = binaryMask

        if seedFile:
            self.inputs.seedFile = seedFile

        # incorporate user options
        self.inputs.update(**inputs)

        if not noseTest:
            directory = os.path.join(os.getcwd(), self.inputs.basename)
            if os.path.isdir(directory):
                if not self.__datacheck_ok(directory):
                    raise AttributeError('Not all standardized files found \
                                         in input directory: %s' % directory)

        results = self._runner()
        if not noseTest:
            results.outputs = self.aggregate_outputs()

        return results

    def outputs_help(self):
        """
        Parameters
        ----------
        (all default input values set to None)

        outfile : /path/to/directory_with_output_files/files
            the files are

        """
        print self.outputs_help.__doc__

    def outputs(self):
        """Returns a :class:`nipype.interfaces.base.Bunch` with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string,file
                path/name of file of probtrackx image
        """
        outputs = Bunch(outfile=None)
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        outputs = self.outputs()
        outputs.outfile = self._gen_fname(self.inputs.basename,
                                             fname=self.inputs.outfile,
                                             suffix='_pbx',
                                             check=True)
        return outputs

    def _datacheck_ok(self, directory):
        """ checks whether the directory given to -s <directory> flag contains
            the three required standardized files """

        merged_ph = False
        merged_th = False
        nodif_brain_mask = False

        f1 = self._glob(os.path.join(directory, 'merged_ph*'))
        if f1 is not None:
            merged_ph = True

        f2 = self._glob(os.path.join(directory, 'merged_th*'))
        if f2 is not None:
            merged_th = True

        f3 = self._glob(os.path.join(directory, 'nodif_brain_mask*'))
        if f3 is not None:
            nodif_brain_mask = True

        return (merged_ph and merged_th and nodif_brain_mask)


class Vecreg(FSLCommand):
    """Use FSL vecreg for registering vector data

    For complete details, see the `FDT Documentation
    <http://www.fmrib.ox.ac.uk/fsl/fdt/fdt_vecreg.html>`_

    """
    opt_map = {'infile':            '-i %s',
               'outfile':           '-o %s',
               'refVolName':        '-r %s',
               'verbose':           '-v',
               'helpDoc':           '-h',
               'tensor':            '--tensor',
               'affineTmat':        '-t %s',
               'warpFile':          '-w %s',
               'interpolation':     '--interp %s',
               'brainMask':         '-m %s'}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'vecreg'

    def inputs_help(self):
        """Print command line documentation for Vecreg."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(infile=None,
                            outfile=None,
                            refVolName=None,
                            verbose=None,
                            helpDoc=None,
                            tensor=None,
                            affineTmat=None,
                            warpFile=None,
                            interpolation=None,
                            brainMask=None,
                            cwd=None)

    def _parse_inputs(self):
        """validate fsl vecreg options"""
        allargs = super(Vecreg, self)._parse_inputs(skip=('infile', 'outfile',
                                                         'refVolName', 'cwd'))

        # Add source files to the args if they are specified
        if self.inputs.infile:
            allargs.insert(0, '-i ' + self.inputs.infile)
        else:
            raise AttributeError('vecreg needs an input file')

        if self.inputs.outfile:
            allargs.insert(1, '-o ' + self.inputs.outfile)
        else:
            outfile = self._gen_fname(self.inputs.infile,
                                         cwd=self.inputs.cwd,
                                         suffix='_vrg')
            self.inputs.outfile = outfile
            allargs.insert(1, '-o ' + outfile)

        if self.inputs.refVolName:
            allargs.insert(2, '-r ' + self.inputs.refVolName)
        else:
            raise AttributeError('vecreg needs a reference volume')

        return allargs

    def run(self, infile=None, outfile=None, refVolName=None, **inputs):
        """Execute the command.

        Examples
        --------
        >>> from nipype.interfaces import fsl
        >>> vreg = fsl.Vecreg(infile='inf', outfile='infout', \
                              refVolName='MNI152')
        >>> vreg.cmdline
        'vecreg -i inf -o infout -r MNI152'

        """
        if infile:
            self.inputs.infile = infile

        if outfile:
            self.inputs.outfile = outfile

        if refVolName:
            self.inputs.refVolName = refVolName

        self.inputs.update(**inputs)
        return super(Vecreg, self).run()

    def outputs(self):
        """Returns a :class:`nipype.interfaces.base.Bunch` with outputs

        Parameters
        ----------
        outfile : str
            path/name of file of probtrackx image
        """
        outputs = Bunch(outfile=None)
        return outputs

    def aggregate_outputs(self):
        outputs = self.outputs()
        outputs.outfile = self._gen_fname(self.inputs.infile,
                                             fname=self.inputs.outfile,
                                             cwd=self.inputs.cwd,
                                             suffix='_vrg',
                                             check=True)
        return outputs
    aggregate_outputs.__doc__ = FSLCommand.aggregate_outputs.__doc__


class ProjThresh(FSLCommand):
    """Use FSL proj_thresh for thresholding some outputs of probtrack

        For complete details, see the `FDT Documentation
        <http://www.fmrib.ox.ac.uk/fsl/fdt/fdt_thresh.html>`_

    """

    opt_map = {}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'proj_thresh'

    def inputs_help(self):
        """Print command line documentation for Proj_thresh."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(volumes=None, threshold=None, cwd=None)

    def _parse_inputs(self):
        """validate fsl Proj_thresh options"""
        allargs = []

        if self.inputs.volumes:
            for vol in self.inputs.volumes:
                allargs.append(vol)
        else:
            raise AttributeError('proj_thresh needs input volumes')

        if self.inputs.threshold:
            allargs.append(repr(self.inputs.threshold))
        else:
            raise AttributeError('proj_thresh needs a threshold value')

        return allargs

    def run(self, volumes=None, threshold=None, **inputs):
        """Execute the command.

        Examples
        --------
        >>> from nipype.interfaces import fsl
        >>> pThresh = fsl.ProjThresh(volumes = ['seeds_to_M1', 'seeds_to_M2'], \
                                     threshold = 3)
        >>> pThresh.cmdline
        'proj_thresh seeds_to_M1 seeds_to_M2 3'

        """

        if volumes is not None:
            self.inputs.volumes = filename_to_list(volumes)

        if threshold is not None:
            self.inputs.threshold = threshold

        self.inputs.update(**inputs)
        return super(ProjThresh, self).run()

    def outputs(self):
        """Returns a :class:`nipype.interfaces.base.Bunch` with outputs

        Parameters
        ----------
        outfile : str
            path/name of file of probtrackx image
        """
        outputs = Bunch(outfile=None)
        return outputs

    def aggregate_outputs(self):
        outputs = self.outputs()
        outputs.outfile = []

        for files in self.inputs.volumes:
            outputs.outfile.append(self._glob(files + '_proj_seg_thr_*'))

        return outputs
    aggregate_outputs.__doc__ = FSLCommand.aggregate_outputs.__doc__


class FindTheBiggest(FSLCommand):
    """Use FSL find_the_biggest for performing hard segmentation on
       the outputs of connectivity-based thresholding in probtrack.

       For complete details, see the `FDT
       Documentation. <http://www.fmrib.ox.ac.uk/fsl/fdt/fdt_biggest.html>`_

    """

    opt_map = {}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'find_the_biggest'

    def inputs_help(self):
        """Print command line documentation for Find_the_biggest."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(infiles=None,
                            outfile=None)

    def _parse_inputs(self):
        """validate fsl Find_the_biggest options"""
        allargs = []
        if self.inputs.infiles:
            allargs.insert(0, self.inputs.infiles)
        if self.inputs.outfile:
            allargs.insert(1, self.inputs.outfile)
        else:
            outfile = self._gen_fname(self.inputs.infiles,
                                         fname=self.inputs.outfile,
                                         suffix='_fbg')
            allargs.insert(1, outfile)

        return allargs

    def run(self, infiles=None, outfile=None, **inputs):
        """Execute the command.

        Examples
        --------
        >>> from nipype.interfaces import fsl
        >>> fBig = fsl.FindTheBiggest(infiles='all*', outfile='biggestOut')
        >>> fBig.cmdline
        'find_the_biggest all* biggestOut'

        """
        if infiles:
            self.inputs.infiles = infiles
        if not self.inputs.infiles:
            raise AttributeError('find_the_biggest requires input file(s)')
        if outfile:
            self.inputs.outfile = outfile
        return super(FindTheBiggest, self).run()

    def outputs(self):
        """Returns a :class:`nipype.interfaces.base.Bunch` with outputs

        Parameters
        ----------
        outfile : str
            path/name of file of probtrackx image
        """
        outputs = Bunch(outfile=None)
        return outputs

    def aggregate_outputs(self):
        outputs = self.outputs()
        outputs.outfile = self._gen_fname(self.inputs.infile,
                                             fname=self.inputs.outfile,
                                             suffix='_fbg',
                                             check=True)

        return outputs
    
    aggregate_outputs.__doc__ = FSLCommand.aggregate_outputs.__doc__
