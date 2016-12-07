# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The fusion module provides higher-level interfaces to some of the operations
that can be performed with the seg_LabFusion command-line program.
"""
import os
import warnings

from nipype.interfaces.niftyseg.base import NiftySegCommand, get_custom_path
from nipype.interfaces.base import (TraitedSpec, File, traits, isdefined,
                                    CommandLineInputSpec)
from ...utils.filemanip import load_json, save_json

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class STEPSInputSpec(CommandLineInputSpec):
    """Input Spec for seg_LabelFusion."""
    in_file = File(argstr='%s', exists=True, mandatory=True,
                   desc='Input image to segment', position=4)

    kernel_size = traits.Float(
        desc="Gaussian kernel size in mm to compute the local similarity",
        argstr='-STEPS %f', mandatory=True, position=2)

    template_num = traits.Int(desc='Number of images to fuse',
                              argstr='%i', mandatory=True, position=3)

    warped_seg_file = File(
        argstr='-in %s', exists=True, mandatory=True, position=1,
        desc='Input 4D image containing the propagated segmentations')

    warped_img_file = File(
        argstr='%s', exists=True, mandatory=True, position=5,
        desc='Input 4D image containing the propagated template images')

    mask_file = File(argstr='-mask %s', exists=True, mandatory=False,
                     desc='Filename of the ROI for label fusion')

    mrf_value = traits.Float(argstr='-MRF_beta %s', mandatory=False,
                             desc='MRF prior strength (between 0 and 5)')

    out_file = File(argstr='-out %s', genfile=True,
                    desc='Output consensus segmentation')

    prob_flag = traits.Bool(desc='Probabilistic/Fuzzy segmented image',
                            argstr='-outProb')

    prob_update_flag = traits.Bool(
        desc='Update label proportions at each iteration',
        argstr='-prop_update')


class STEPSOutputSpec(TraitedSpec):
    """Output Spec for seg_LabelFusion."""
    out_file = File(desc="Output consensus segmentation")


class STEPS(NiftySegCommand):
    """Interface for seg_LabelFusion.

    Usage ->	seg_LabFusion -in <filename> -<Type of Label Fusion> [OPTIONS]

    * * Mandatory * *

    -in <filename>			| Filename of the 4D integer label image

    * * Type of Classifier Fusion (mutually exclusive) * *

    -STEPS <k> <n> <i> <t> 		| STEPS algorithm
                                | Size of the kernel (k), number of local
                                | labels to use (n), Original image to segment
                                | (3D Image), registered templates (4D Image).
    -MLSTEPS <k> <l> <n> <i> <t>
                    | Multi-level STEPS algorithm (Beta testing. Do not use!)
                    | Size of the kernel (k), number of levels (l) and local
                    | labels to use (n), Original image to segment (3D Image),
                    | registered templates (4D Image).
    -STAPLE 			| STAPLE algorithm
    -MV 				| Majority Vote algorithm
    -SBA 				| Shape Based Averaging algorithm (Beta)

    * * General Options * *

    -v <int>			| Verbose level [0 = off, 1 = on, 2 = debug]
                        | (default = 0)
    -unc 				| Only consider non-consensus voxels to calculate
                        | statistics
    -out <filename>			| Filename of the integer segmented image
                            | (default=LabFusion.nii.gz)
    -mask <filename>		| Filename of the ROI for label fusion
                            | (greatly reduces memory requirements)
    -outProb 			| Probabilistic/Fuzzy segmented image (only for 1 label)
    --version			|Print current source code git hash key and exit

    * * STAPLE and STEPS options * *

    -prop <proportion> 		| Proportion of the label (only for single labels)
    -prop_update 			| Update label proportions at each iteration.
    -setPQ <P> <Q> 			| Value of P and Q [ 0 < (P,Q) < 1 ]
                            | (default = 0.99 0.99)
    -MRF_beta <float>		| MRF prior strength [ 0 < beta < 5 ]
    -max_iter <int>			| Maximum number of iterations (default = 15)
    -uncthres <float>		| If <float> percent of labels agree,
                            | then area is not uncertain
    -conv <float>			| Ratio for convergence (default epsilon = 10^-5)

    * * Ranking for STAPLE and MV (mutually exclusive) * *

    -ALL  (default)			| Use all labels with no Ranking
    -GNCC <n> <img> <tmpl>
                    | Global Normalized Cross Correlation Ranking
                    | (Calculated in the full image):
                    | Number of sorted classifiers to use (n),
                    | Original image to segment (3D image),
                    | registered templates (4D Image).
    -ROINCC <d> <n> <img> <tmpl>
                    | ROI Normalized Cross Correlation Ranking
                    | (On the registered label ROI):
                    | Dilation of the ROI ( <int> d>=1 ), Number of sorted
                    | classifiers to use (n),  Original image to segment
                    | (3D image), registered templates (4D Image).
    -LNCC <k> <n> <img> <tmpl>
                    | Locally Normalized Cross Correlation Ranking
                    | (On a local gaussian kernel):
                    | Size of the kernel (k), number of local classifiers to
                    | use (n), Original image to segment (3D Image),
                    | registered templates (4D Image). LNCC is only available
                    | for STAPLE and MV.

    """
    _cmd = get_custom_path('seg_LabFusion')
    _suffix = '_steps'
    input_spec = STEPSInputSpec
    output_spec = STEPSOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                                                  suffix=self._suffix)
        outputs['out_file'] = os.path.abspath(outputs['out_file'])
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()['out_file']
        return None


class CalcTopNCCInputSpec(CommandLineInputSpec):
    """Input Spec for seg_CalcTopNCC."""
    in_file = File(argstr='-target %s', exists=True, mandatory=True,
                   desc='Target file', position=1)

    num_templates = traits.Int(argstr='-templates %s', mandatory=True,
                               position=2, desc='Number of Templates')

    in_templates = traits.List(File(exists=True), argstr="%s", position=3,
                               mandatory=True)

    top_templates = traits.Int(argstr='-n %s', mandatory=True, position=4,
                               desc='Number of Top Templates')

    mask_file = File(argstr='-mask %s', exists=True, mandatory=False,
                     desc='Filename of the ROI for label fusion')


class CalcTopNCCOutputSpec(TraitedSpec):
    """Output Spec for seg_CalcTopNCC."""
    out_files = traits.Any(File(exists=True))


class CalcTopNCC(NiftySegCommand):
    """Interface for seg_CalcTopNCC.

    Usage:	seg_CalcTopNCC -target <filename> -templates <Number of templates>
                       <Template Names> -n <Number of Top Templates> <OPTIONS>

    * * Options * *
    -mask <filename>	Filename of the ROI mask
    --version		Print current source code git hash key and exit
    """
    _cmd = get_custom_path('seg_CalcTopNCC')
    _suffix = '_topNCC'
    input_spec = CalcTopNCCInputSpec
    output_spec = CalcTopNCCOutputSpec

    def aggregate_outputs(self, runtime=None, needed_outputs=None):
        outputs = self._outputs()
        # local caching for backward compatibility
        outfile = os.path.join(os.getcwd(), 'CalcTopNCC.json')
        if runtime is None:
            try:
                out_files = load_json(outfile)['files']
            except IOError:
                return self.run().outputs
        else:
            out_files = []
            for line in runtime.stdout.split('\n'):
                if line:
                    values = line.split()
                    if len(values) > 1:
                        out_files.append([str(val) for val in values])
                    else:
                        out_files.extend([str(val) for val in values])
            if len(out_files) == 1:
                out_files = out_files[0]
            save_json(outfile, dict(files=out_files))
        outputs.out_files = out_files
        return outputs
