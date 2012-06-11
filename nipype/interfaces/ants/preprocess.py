"""The ants module provides basic functions for interfacing with ants functions.

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)

"""

from ..base import (TraitedSpec, File, traits, isdefined)
from ...utils.filemanip import split_filename
from .base import ANTSCommand, ANTSCommandInputSpec
import os


class N4BiasFieldCorrectionInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='--image-dimension %d', usedefault=True,
                            desc='image dimension (2 or 3)')
    input_image = File(argstr='--input-image %s', mandatory=True,
                        desc=('image to apply transformation to (generally a '
                              'coregistered functional)'))
    output_image = traits.Str(argstr='--output %s',
                             desc=('output file name'), genfile=True,
                             hash_file=False)
    bspline_fitting_distance = traits.Float(argstr="--bsline-fitting [%g]")
    shrink_factor = traits.Int(argstr="--shrink-factor %d")
    n_iterations = traits.List(traits.Int(), argstr="--convergence [ %s", sep="x", requires=['convergence_threshold'], position=1)
    convergence_threshold = traits.Float(argstr=",%g]", requires=['n_iterations'], position=2)


class N4BiasFieldCorrectionOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc='Warped image')


class N4BiasFieldCorrection(ANTSCommand):
    """N4 is a variant of the popular N3 (nonparameteric nonuniform normalization)
    retrospective bias correction algorithm. Based on the assumption that the
    corruption of the low frequency bias field can be modeled as a convolution of
    the intensity histogram by a Gaussian, the basic algorithmic protocol is to
    iterate between deconvolving the intensity histogram by a Gaussian, remapping
    the intensities, and then spatially smoothing this result by a B-spline modeling
    of the bias field itself. The modifications from and improvements obtained over
    the original N3 algorithm are described in the following paper: N. Tustison et
    al., N4ITK: Improved N3 Bias Correction, IEEE Transactions on Medical Imaging,
    29(6):1310-1320, June 2010.

    Examples
    --------

    >>> from nipype.interfaces.ants import N4BiasFieldCorrection
    >>> n4 = N4BiasFieldCorrection()
    >>> n4.inputs.dimension = 3
    >>> n4.inputs.input_image = 'structural.nii'
    >>> n4.inputs.bspline_fitting_distance = 300
    >>> n4.inputs.shrink_factor = 3
    >>> n4.inputs.n_iterations = [50,50,30,20]
    >>> n4.inputs.convergence_threshold = 1e-6
    >>> n4.cmdline
    'N4BiasFieldCorrection --convergence [ 50x50x30x20 ,1e-06] --bsline-fitting [300] --image-dimension 3 --input-image structural.nii --output structural_corrected.nii --shrink-factor 3'
    """

    _cmd = 'N4BiasFieldCorrection'
    input_spec = N4BiasFieldCorrectionInputSpec
    output_spec = N4BiasFieldCorrectionOutputSpec

    def _gen_filename(self, name):
        if name == 'output_image':
            output = self.inputs.output_image
            if not isdefined(output):
                _, name, ext = split_filename(self.inputs.input_image)
                output = name + '_corrected' + ext
            return output
        return None

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output_image'] = os.path.abspath(self._gen_filename('output_image'))
        return outputs
