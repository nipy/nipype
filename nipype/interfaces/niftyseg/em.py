# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Nipype interface for seg_EM.

The em module provides higher-level interfaces to some of the operations
that can be performed with the seg_em command-line program.

Examples
--------
See the docstrings of the individual classes for examples.
"""

from ..base import TraitedSpec, File, traits, CommandLineInputSpec, InputMultiPath
from .base import NiftySegCommand
from ..niftyreg.base import get_custom_path


class EMInputSpec(CommandLineInputSpec):
    """Input Spec for EM."""

    in_file = File(
        argstr="-in %s",
        exists=True,
        mandatory=True,
        desc="Input image to segment",
        position=4,
    )

    mask_file = File(
        argstr="-mask %s", exists=True, desc="Filename of the ROI for label fusion"
    )

    # Priors
    no_prior = traits.Int(
        argstr="-nopriors %s",
        mandatory=True,
        desc="Number of classes to use without prior",
        xor=["prior_4D", "priors"],
    )

    prior_4D = File(
        argstr="-prior4D %s",
        exists=True,
        mandatory=True,
        desc="4D file containing the priors",
        xor=["no_prior", "priors"],
    )

    priors = InputMultiPath(
        argstr="%s",
        mandatory=True,
        desc="List of priors filepaths.",
        xor=["no_prior", "prior_4D"],
    )

    # iterations
    max_iter = traits.Int(
        argstr="-max_iter %s",
        default_value=100,
        usedefault=True,
        desc="Maximum number of iterations",
    )

    min_iter = traits.Int(
        argstr="-min_iter %s",
        default_value=0,
        usedefault=True,
        desc="Minimum number of iterations",
    )

    # other options
    bc_order_val = traits.Int(
        argstr="-bc_order %s",
        default_value=3,
        usedefault=True,
        desc="Polynomial order for the bias field",
    )

    mrf_beta_val = traits.Float(
        argstr="-mrf_beta %s", desc="Weight of the Markov Random Field"
    )

    desc = "Bias field correction will run only if the ratio of improvement \
is below bc_thresh. (default=0 [OFF])"

    bc_thresh_val = traits.Float(
        argstr="-bc_thresh %s", default_value=0, usedefault=True, desc=desc
    )

    desc = "Amount of regularization over the diagonal of the covariance \
matrix [above 1]"

    reg_val = traits.Float(argstr="-reg %s", desc=desc)

    desc = "Outlier detection as in (Van Leemput TMI 2003). <fl1> is the \
Mahalanobis threshold [recommended between 3 and 7] <fl2> is a convergence \
ratio below which the outlier detection is going to be done [recommended 0.01]"

    outlier_val = traits.Tuple(
        traits.Float(), traits.Float(), argstr="-outlier %s %s", desc=desc
    )

    desc = "Relax Priors [relaxation factor: 0<rf<1 (recommended=0.5), \
gaussian regularization: gstd>0 (recommended=2.0)] /only 3D/"

    relax_priors = traits.Tuple(
        traits.Float(), traits.Float(), argstr="-rf %s %s", desc=desc
    )

    # outputs
    out_file = File(
        name_source=["in_file"],
        name_template="%s_em.nii.gz",
        argstr="-out %s",
        desc="Output segmentation",
    )
    out_bc_file = File(
        name_source=["in_file"],
        name_template="%s_bc_em.nii.gz",
        argstr="-bc_out %s",
        desc="Output bias corrected image",
    )
    out_outlier_file = File(
        name_source=["in_file"],
        name_template="%s_outlier_em.nii.gz",
        argstr="-out_outlier %s",
        desc="Output outlierness image",
    )


class EMOutputSpec(TraitedSpec):
    """Output Spec for EM."""

    out_file = File(desc="Output segmentation")
    out_bc_file = File(desc="Output bias corrected image")
    out_outlier_file = File(desc="Output outlierness image")


class EM(NiftySegCommand):
    """Interface for executable seg_EM from NiftySeg platform.

    seg_EM is a general purpose intensity based image segmentation tool. In
    it's simplest form, it takes in one 2D or 3D image and segments it in n
    classes.

    `Source code <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg>`_ |
    `Documentation <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg_documentation>`_

    Examples
    --------
    >>> from nipype.interfaces import niftyseg
    >>> node = niftyseg.EM()
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.no_prior = 4
    >>> node.cmdline
    'seg_EM -in im1.nii -bc_order 3 -bc_thresh 0 -max_iter 100 -min_iter 0 -nopriors 4 \
-bc_out im1_bc_em.nii.gz -out im1_em.nii.gz -out_outlier im1_outlier_em.nii.gz'

    """

    _cmd = get_custom_path("seg_EM", env_dir="NIFTYSEGDIR")
    _suffix = "_em"
    input_spec = EMInputSpec
    output_spec = EMOutputSpec

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for seg_EM."""
        if opt == "priors":
            _nb_priors = len(self.inputs.priors)
            return "-priors %d %s" % (_nb_priors, " ".join(self.inputs.priors))
        else:
            return super(EM, self)._format_arg(opt, spec, val)
