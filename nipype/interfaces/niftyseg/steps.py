# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    The fusion module provides higher-level interfaces to some of the operations
    that can be performed with the seg_LabFusion command-line program.
"""
import os
import warnings

from nipype.interfaces.niftyseg.base import NIFTYSEGCommandInputSpec, NIFTYSEGCommand, getNiftySegPath
from nipype.interfaces.base import (TraitedSpec, File, traits, OutputMultiPath, isdefined)
from ...utils.filemanip import (load_json, save_json, split_filename,
                                fname_presuffix)
warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class STEPSInputSpec(NIFTYSEGCommandInputSpec):

    in_file = File(argstr='%s', exists=True, mandatory=True,
                   desc='Input image to segment',
                   position=4)

    kernel_size = traits.Float(desc="Gaussian kernel size in mm to compute the local similarity",
                               argstr='-STEPS %f', mandatory=True,
                               position=2)

    template_num = traits.Int(desc='Number of images to fuse',
                              argstr='%i', mandatory=True,
                              position=3)

    warped_seg_file = File(argstr='-in %s', exists=True, mandatory=True,
                           desc='Input 4D image containing the propagated segmentations',
                           position=1)

    warped_img_file = File(argstr='%s', exists=True, mandatory=True,
                           desc='Input 4D image containing the propagated template images',
                           position=5)

    mask_file = File(argstr='-mask %s', exists=True, mandatory=False,
                     desc='Filename of the ROI for label fusion')

    mrf_value = traits.Float(argstr='-MRF_beta %s', mandatory=False,
                             desc='MRF prior strength (between 0 and 5)')

    out_file = File(argstr='-out %s', genfile=True,
                    desc='Output consensus segmentation')

    prob_flag = traits.Bool(desc='Probabilistic/Fuzzy segmented image',
                           argstr='-outProb')

    prob_update_flag = traits.Bool(desc='Update label proportions at each iteration',
                           argstr='-prop_update')


class STEPSOutputSpec(TraitedSpec):

    out_file = File(desc="Output consensus segmentation")


class STEPS(NIFTYSEGCommand):

    _cmd = getNiftySegPath('seg_LabFusion')
    _suffix = '_steps'
    input_spec = STEPSInputSpec
    output_spec = STEPSOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file, suffix=self._suffix)
        outputs['out_file'] = os.path.abspath(outputs['out_file'])
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()['out_file']
        return None

class CalcTopNCCInputSpec(NIFTYSEGCommandInputSpec):

    in_file = File(argstr='-target %s', exists=True, mandatory=True,
                   desc='Target file',
                   position=1)

    num_templates = traits.Int(argstr='-templates %s', mandatory=True, position=2,
                               desc='Number of Templates')

    in_templates = traits.List(File(exists=True), argstr="%s", position=3,
                               mandatory=True)

    top_templates = traits.Int(argstr='-n %s', mandatory=True, position=4,
                               desc='Number of Top Templates')

    mask_file = File(argstr='-mask %s', exists=True, mandatory=False,
                     desc='Filename of the ROI for label fusion')


class CalcTopNCCOutputSpec(TraitedSpec):

    out_files = traits.Any(File(exists=True))


class CalcTopNCC(NIFTYSEGCommand):
    _cmd = getNiftySegPath('seg_CalcTopNCC')
    _suffix = '_topNCC'
    input_spec = CalcTopNCCInputSpec
    output_spec = CalcTopNCCOutputSpec

    def aggregate_outputs(self, runtime=None, needed_outputs=None):
        outputs = self._outputs()
        # local caching for backward compatibility
        outfile = os.path.join(os.getcwd(), 'CalcTopNCC.json')
        if runtime is None:
            try:
                out_stat = load_json(outfile)['files']
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

