# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    The fusion module provides higher-level interfaces to some of the operations
    that can be performed with the seg_LabFusion command-line program.
"""
import os
import warnings

from nipype.interfaces.niftyseg.base import NIFTYSEGCommandInputSpec, NIFTYSEGCommand, getNiftySegPath
from nipype.interfaces.base import (TraitedSpec, File, traits, isdefined)

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

