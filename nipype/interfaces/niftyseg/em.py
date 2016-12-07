# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The em module provides higher-level interfaces to some of the operations
that can be performed with the seg_em command-line program.
"""
import os

from nipype.interfaces.niftyseg.base import NiftySegCommand, get_custom_path
from nipype.interfaces.base import (TraitedSpec, File, traits, isdefined,
                                    CommandLineInputSpec, InputMultiPath)


class EMInputSpec(CommandLineInputSpec):
    """Input Spec for seg_EM."""
    in_file = File(argstr='-in %s', exists=True, mandatory=True,
                   desc='Input image to segment', position=4)

    mask_file = File(argstr='-mask %s', exists=True,
                     desc='Filename of the ROI for label fusion')
    # Priors
    no_prior = traits.Int(argstr='-nopriors %s', mandatory=True,
                          desc='Number of classes to use without prior',
                          xor=['prior_4D', 'priors'])
    prior_4D = File(argstr='-prior4D %s', exists=True, mandatory=True,
                    desc='4D file containing the priors',
                    xor=['no_prior', 'priors'])
    priors = traits.Tuple(
        traits.Int(), InputMultiPath(), argstr='%s', mandatory=True,
        desc='The number of priors (n>0) and their filenames.',
        xor=['no_prior', 'prior_4D'])

    # iterations
    max_iter = traits.Int(argstr='-max_iter %s', default=100,
                          desc='Maximum number of iterations')
    min_iter = traits.Int(argstr='-min_iter %s', default=0,
                          desc='Minimun number of iterations')

    # other options
    bc_order_val = traits.Int(argstr='-bc_order %s', default=3,
                              desc='Polynomial order for the bias field')
    mrf_beta_val = traits.Float(argstr='-mrf_beta %s',
                                desc='Weight of the Markov Random Field')
    bc_thresh_val = traits.Float(argstr='-bc_thresh %s', default=0,
                                 desc='Bias field correction will run only if \
the ratio of improvement is below bc_thresh. (default=0 [OFF])')
    reg_val = traits.Float(argstr='-reg %s',
                           desc='Amount of regularization over the diagonal of \
the covariance matrix [above 1]')
    outlier_val = traits.Tuple(
        traits.Float(), traits.Float(), argstr='-outlier %s %s',
        desc='Outlier detection as in (Van Leemput TMI 2003). \
<fl1> is the Mahalanobis threshold [recommended between 3 and 7] \
<fl2> is a convergence ratio below which the outlier detection is \
going to be done [recommended 0.01]')
    relax_priors = traits.Tuple(
        traits.Float(), traits.Float(), argstr='-rf %s %s',
        desc='Relax Priors [relaxation factor: 0<rf<1 (recommended=0.5), \
gaussian regularization: gstd>0 (recommended=2.0)] /only 3D/')

    # outputs
    out_file = File(argstr='-out %s', genfile=True, desc='Output segmentation')
    out_bc_file = File(argstr='-bc_out %s', genfile=True,
                       desc='Output bias corrected image')
    out_outlier_file = File(argstr='-out_outlier %s', genfile=True,
                            desc='Output outlierness image')


class EMOutputSpec(TraitedSpec):
    """Output Spec for seg_EM."""
    out_file = File(desc="Output segmentation")
    out_bc_file = File(desc="Output bias corrected image")
    out_outlier_file = File(desc='Output outlierness image')


class EM(NiftySegCommand):
    """Interface for seg_EM.

    EM Statistical Segmentation:
    Usage ->	seg_EM -in <filename> [OPTIONS]

    * * Mandatory * *

    -in <filename>
                | Filename of the input image
    -out <filename>
                | Filename of the segmented image
                | The input image should be 2D, 3D or 4D images.
                | 2D images should be on the XY plane.
                | 4D images are segmented as if they were multimodal.

        + Select one of the following (mutually exclusive) -

    -priors <n> <fnames>
                | The number of priors (n>0) and their filenames.
                | Priors should be registerd to the input image
    -priors4D <fname>
                | 4D image with the piors stacked in the 4th dimension.
                | Priors should be registerd to the input image
    -nopriors <n>
                | The number of classes (n>0)

    * * General Options * *

    -mask <filename>
                | Filename of the brain-mask of the input image
    -max_iter <int>
                | Maximum number of iterations (default = 100)
    -min_iter <int>
                | Minimum number of iterations (default = 0)
    -v <int>
                | Verbose level [0 = off, 1 = on, 2 = debug] (default = 0)
    -mrf_beta <float>
                | MRF prior strength [off = 0, max = 1] (default = 0.4)
    -bc_order <int>
                | Polynomial order for the bias field [off = 0, max = 5]
                | (default = 3)
    -bc_thresh <float>
                | Bias field correction will run only if the ratio of
                | improvement is below bc_thresh (default=0 [OFF])
    -bc_out <filename>
                | Output the bias corrected image
    -reg <float>
                | Amount of regularization over the diagonal of the covariance
                | matrix [above 1]
    -outlier <fl1> <fl2>
                | Outlier detection as in (Van Leemput TMI 2003).
                | <fl1> is the Mahalanobis threshold
                | [recommended between 3 and 7]
                | <fl2> is a convergence ratio below which the outlier
                | detection is going to be done [recommended 0.01].
    -out_outlier <filename>
                | Output outlierness image
    -rf <rel> <gstd>
                | Relax Priors [relaxation factor: 0<rf<1 (recommended=0.5),
                | gaussian regularization: gstd>0 (recommended=2.0)] /only 3D/
    -MAP <M V M V ...>
                | MAP formulation: M and V are the parameters
                | (mean & variance) of the semiconjugate prior over the
                | class mean
    --version
                |Print current source code git hash key and exit
    """
    _cmd = get_custom_path('seg_EM')
    _suffix = '_em'
    input_spec = EMInputSpec
    output_spec = EMOutputSpec

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for seg_EM."""
        if opt == 'priors':
            if self.inputs.priors[0] != len(self.inputs.priors[1]):
                # error
                msg = "Priors options not set properly: number of files(%d) \
different than the number of file paths given (%d)"
                raise Exception(msg % (self.inputs.priors[0],
                                       len(self.inputs.priors[1])))
            return '-priors %d %s' % (self.inputs.priors[0],
                                      ' '.join(self.inputs.priors[1]))
        else:
            return super(EM, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                                                  suffix=self._suffix)
        outputs['out_file'] = os.path.abspath(outputs['out_file'])
        outputs['out_bc_file'] = self.inputs.out_bc_file
        if not isdefined(self.inputs.out_bc_file):
            outputs['out_bc_file'] = self._gen_fname(
                    self.inputs.in_file, suffix=('_bc%s' % self._suffix))
        outputs['out_bc_file'] = os.path.abspath(outputs['out_bc_file'])
        outputs['out_outlier_file'] = self.inputs.out_outlier_file
        if not isdefined(self.inputs.out_outlier_file):
            outputs['out_outlier_file'] = self._gen_fname(
                    self.inputs.in_file, suffix=('_outlier%s' % self._suffix))
        outputs['out_outlier_file'] = os.path.abspath(
                    outputs['out_outlier_file'])
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()['out_file']
        if name == 'out_bc_file':
            return self._list_outputs()['out_bc_file']
        if name == 'out_outlier_file':
            return self._list_outputs()['out_outlier_file']
        return None
