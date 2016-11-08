# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The em module provides higher-level interfaces to some of the operations
that can be performed with the seg_em command-line program.
"""
import os

from nipype.interfaces.niftyseg.base import NIFTYSEGCommand, \
                                    NIFTYSEGCommandInputSpec, getNiftySegPath
from nipype.interfaces.base import (TraitedSpec, File, traits, isdefined)


class EMInputSpec(NIFTYSEGCommandInputSpec):

    in_file = File(argstr='-in %s', exists=True, mandatory=True,
                   desc='Input image to segment',
                   position=4)

    mask_file = File(argstr='-mask %s', exists=True,
                     desc='Filename of the ROI for label fusion')

    no_prior = traits.Int(argstr='-nopriors %s', mandatory=True,
                          desc='Number of classes to use without prior',
                          xor=['prior_4D'])
    prior_4D = File(argstr='-prior4D %s', exists=True, mandatory=True,
                    desc='4D file containing the priors',
                    xor=['no_prior'])
    bc_order_val = traits.Int(argstr='-bc_order %s', default=3,
                              desc='Polynomial order for the bias field')
    mrf_beta_val = traits.Float(argstr='-mrf_beta %s',
                                desc='Weight of the Markov Random Field')

    out_file = File(argstr='-out %s', genfile=True,
                    desc='Output segmentation')
    out_bc_file = File(argstr='-bc_out %s', genfile=True,
                       desc='Output bias corrected image')


class EMOutputSpec(TraitedSpec):

    out_file = File(desc="Output segmentation")
    out_bc_file = File(desc="Output bias corrected image")


class EM(NIFTYSEGCommand):

    _cmd = getNiftySegPath('seg_em')
    _suffix = '_em'
    input_spec = EMInputSpec
    output_spec = EMOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file, suffix=self._suffix)
        outputs['out_file'] = os.path.abspath(outputs['out_file'])
        outputs['out_bc_file'] = self.inputs.out_bc_file
        if not isdefined(self.inputs.out_bc_file):
            outputs['out_bc_file'] = self._gen_fname(self.inputs.in_file, suffix='_bc' + self._suffix)
        outputs['out_bc_file'] = os.path.abspath(outputs['out_bc_file'])
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()['out_file']
        if name == 'out_bc_file':
            return self._list_outputs()['out_bc_file']
        return None
