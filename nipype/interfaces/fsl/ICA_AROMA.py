#ICA_AROMA pulled from: https://github.com/rhr-pruim/ICA-AROMA
#This assumes ICA_AROMA.py is already installed and callable via $PATH
from nipype.interfaces.base import (
    TraitedSpec,
    CommandLineInputSpec,
    CommandLine,
    File,
    Directory,
    traits,
    OutputMultiPath
)
import os

class ICA_AROMAInputSpec(CommandLineInputSpec):
    featDir = Directory(exists=True,
                        desc='If a feat directory exists and temporal filtering '
                        'has not been run yet, ICA_AROMA can use the files in '
                        'this directory.',mandatory=False,xor=['infile','mask','affmat','warp','mc'])
    infile = File(exists=True, 
                  desc='volume to be denoised', 
                  argstr='-i %s',mandatory=False,xor=['featDir'])
    outdir = Directory(desc='path to output directory', 
                  argstr='-o %s',mandatory=True)
    mask = File(exists=True, 
                desc='path/name volume mask', 
                argstr='-m %s',mandatory=False,xor=['featDir'])
    dim = traits.Int(desc='Dimensionality reduction when running '
                     'MELODIC (defualt is automatic estimation)', 
                     argstr='-dim %d')
    TR = traits.Float(desc='TR in seconds. If this is not specified '
                      'the TR will be extracted from the header of the fMRI nifti file.',
                      argstr='%.2f')
    melodic_dir = Directory(exists=True,
                            desc='path to MELODIC directory if MELODIC has already been ran',
                            argstr='-meldir %s')
    affmat = File(exists=True,
                  desc='path/name of the mat-file describing the '
                  'affine registration (e.g. FSL FLIRT) of the '
                  'functional data to structural space (.mat file)',
                  argstr='-affmat %s',mandatory=False,xor=['featDir'])
    warp = File(exists=True,
                desc='File name of the warp-file describing '
                'the non-linear registration (e.g. FSL FNIRT) '
                'of the structural data to MNI152 space (.nii.gz)',
                argstr='-warp %s',mandatory=False,xor=['featDir'])
    mc = File(exists=True,
              desc='motion parameters file',
              argstr='-mc %s',mandatory=False,xor=['featDir'])
    denoise_type = traits.Str(argstr='-den %s',
                              desc='Type of denoising strategy: '
                              '-none: only classification, no denoising '
                              '-nonaggr (default): non-aggresssive denoising, i.e. partial component regression '
                              '-aggr: aggressive denoising, i.e. full component regression '
                              '-both: both aggressive and non-aggressive denoising (two outputs)',
                              mandatory=True)

class ICA_AROMAOutputSpec(TraitedSpec):
    out_file = OutputMultiPath(File(exists=True), 
                               desc='if generated: 1-(non aggressive denoised volume),'
                               '2-(aggressive denoised volume)')
   
class ICA_AROMA(CommandLine):
    """

    Example
    -------

    >>> from nipype.interfaces.fsl import ICA_AROMA 
    >>> AROMA_obj=ICA_AROMA.ICA_AROMA()
    >>> outDir=os.path.join(os.getcwd(),'ICA_AROMA_testout')
    >>> func='/path/to/mcImg_brain.nii.gz'
    >>> affmat='/path/to/functoT1.mat'
    >>> warp='/path/to/T1toMNI_warp.nii.gz'
    >>> mc='/path/to/mcImg.par'
    >>> mask='/path/to/mcImg_mask.nii.gz'
    >>> denoise_type='both'
    >>> AROMA_obj.inputs.infile=func
    >>> AROMA_obj.inputs.affmat=affmat
    >>> AROMA_obj.inputs.warp=warp
    >>> AROMA_obj.inputs.mc=mc
    >>> AROMA_obj.inputs.mask=mask
    >>> AROMA_obj.inputs.denoise_type=denoise_type
    >>> AROMA_obj.inputs.outdir=outDir
    >>> AROMA_obj.cmdline
    'ICA_AROMA.py -affmat /path/to/functoT1.mat -den both 
    -i /path/to/mcImg_brain.nii.gz 
    -m /path/to/mcImg_mask.nii.gz 
    -mc /path/to/mcImg.par 
    -o /path/to/ICA_AROMA_testout 
    -warp /path/to/T1toMNI_warp.nii.gz'
    >>> AROMA_obj.run()

    """
    _cmd = 'ICA_AROMA.py'
    input_spec = ICA_AROMAInputSpec
    output_spec = ICA_AROMAOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec.get()
        outdir = self.input_spec.outdir
        denoising_strategy = input_spec.denoise_type

        if denoising_strategy is "noaggr":
          outputs['out_file'] = os.path.join(outdir,'denoised_func_data_nonaggr.nii.gz')
        elif denoising_strategy is "aggr":
          outputs['out_file'] = os.path.join(outdir,'denoised_func_data_aggr.nii.gz')
        elif denoising_strategy is "both":
          outputs['out_file'] = (os.path.join(outdir,'denoised_func_data_nonaggr.nii.gz'), os.path.join(outdir,'denoised_func_data_aggr.nii.gz'))
        elif denoising_strategy is "none":
          print "No denoising selected"
        else:
          raise RuntimeError('denoise_type must be specified as one of'
                             ' noaggr,aggr,both, or none')

        return outputs
