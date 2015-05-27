# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    The fusion module provides higher-level interfaces to some of the operations
    that can be performed with the seg_DetectLesions command-line program.
"""
import os
import warnings

from nipype.interfaces.niftyseg.base import NIFTYSEGCommandInputSpec, NIFTYSEGCommand, getNiftySegPath
from nipype.interfaces.base import (TraitedSpec, File, traits, isdefined)

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class PatchMatchInputSpec(NIFTYSEGCommandInputSpec):

    # Mandatory input arguments
    in_file = File(argstr='%s', exists=True, mandatory=True,
                   desc='Input image to segment',
                   position=1)

    mask_file = File(argstr='%s', exists=True, mandatory=True,
                     desc='Input mask for the area where applies PatchMatch',
                     position=2)

    database_file = File(argstr='%s', genfile=True,  mandatory=True,
                    desc='Database with the segmentations',
                    position=3)

    # Output file name
    out_file = File(desc='The output filename of the patchmatch results',
                    argstr='%s', name_source=['in_file'], name_template='%s_pm', 
                    position=4)

    # Optional arguments
    patch_size = traits.Int(desc="Patch size, #voxels",
                               argstr='-size %i', mandatory=False)

    cs_size = traits.Int(desc="Constrained search area size, number of times bigger than the patchsize",
                               argstr='-cs %i', mandatory=False)

    match_num = traits.Int(desc="Number of better matching",
                               argstr='-match %i', mandatory=False)

    pm_num = traits.Int(desc="Number of patchmatch executions",
                               argstr='-pm %i', mandatory=False)

    it_num = traits.Int(desc="Number of iterations for the patchmatch algorithm",
                               argstr='-it %i', mandatory=False)



class PatchMatchOutputSpec(TraitedSpec):

    out_file = File(desc="Output segmentation")


class PatchMatch(NIFTYSEGCommand):

    _cmd = getNiftySegPath('seg_DetectLesions')
    _suffix = '_pm'
    input_spec = PatchMatchInputSpec
    output_spec = PatchMatchOutputSpec

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

