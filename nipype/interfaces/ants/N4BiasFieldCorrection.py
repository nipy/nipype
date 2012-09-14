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

"""
COMMAND:
     N4BiasFieldCorrection
          N4 is a variant of the popular N3 (nonparameteric nonuniform normalization)
          retrospective bias correction algorithm. Based on the assumption that the
          corruption of the low frequency bias field can be modeled as a convolution of
          the intensity histogram by a Gaussian, the basic algorithmic protocol is to
          iterate between deconvolving the intensity histogram by a Gaussian, remapping
          the intensities, and then spatially smoothing this result by a B-spline modeling
          of the bias field itself. The modifications from and improvements obtained over
          the original N3 algorithm are described in the following paper: N. Tustison et
          al., N4ITK: Improved N3 Bias Correction, IEEE Transactions on Medical Imaging,
          29(6):1310-1320, June 2010.

OPTIONS:
     -d, --image-dimensionality 2/3/4
          This option forces the image to be treated as a specified-dimensional image. If
          not specified, N4 tries to infer the dimensionality from the input image.

     -i, --input-image inputImageFilename
          A scalar image is expected as input for bias correction. Since N4 log transforms
          the intensities, negative values or values close to zero should be processed
          prior to correction.

     -x, --mask-image maskImageFilename
          If a mask image is specified, the final bias correction is only performed in the
          mask region. If a weight image is not specified, only intensity values inside
          the masked region are used during the execution of the algorithm. If a weight
          image is specified, only the non-zero weights are used in the execution of the
          algorithm although the mask region defines where bias correction is performed in
          the final output. Otherwise bias correction occurs over the entire image domain.
          See also the option description for the weight image.

     -w, --weight-image weightImageFilename
          The weight image allows the user to perform a relative weighting of specific
          voxels during the B-spline fitting. For example, some studies have shown that N3
          performed on white matter segmentations improves performance. If one has a
          spatial probability map of the white matter, one can use this map to weight the
          b-spline fitting towards those voxels which are more probabilistically
          classified as white matter. See also the option description for the mask image.

     -s, --shrink-factor 1/2/3/4/...
          Running N4 on large images can be time consuming. To lessen computation time,
          the input image can be resampled. The shrink factor, specified as a single
          integer, describes this resampling. Shrink factors <= 4 are commonly used.

     -c, --convergence [<numberOfIterations=50x50x50x50>,<convergenceThreshold=0.000001>]
          Convergence is determined by calculating the coefficient of variation between
          subsequent iterations. When this value is less than the specified threshold from
          the previous iteration or the maximum number of iterations is exceeded the
          program terminates. Multiple resolutions can be specified by using 'x' between
          the number of iterations at each resolution, e.g. 100x50x50.

     -b, --bspline-fitting [splineDistance,<splineOrder=3>]
                           [initialMeshResolution,<splineOrder=3>]
          These options describe the b-spline fitting parameters. The initial b-spline
          mesh at the coarsest resolution is specified either as the number of elements in
          each dimension, e.g. 2x2x3 for 3-D images, or it can be specified as a single
          scalar parameter which describes the isotropic sizing of the mesh elements. The
          latter option is typically preferred. For each subsequent level, the spline
          distance decreases in half, or equivalently, the number of mesh elements doubles
          Cubic splines (order = 3) are typically used.

     -t, --histogram-sharpening [<FWHM=0.15>,<wienerNoise=0.01>,<numberOfHistogramBins=200>]
          These options describe the histogram sharpening parameters, i.e. the
          deconvolution step parameters described in the original N3 algorithm. The
          default values have been shown to work fairly well.

     -o, --output [correctedImage,<biasField>]
          The output consists of the bias corrected version of the input image.
          Optionally, one can also output the estimated bias field.

     -h
          Print the help menu (short version).
          <VALUES>: 0

     --help
          Print the help menu.
          <VALUES>: 0
===========================================
N4BiasFieldCorrection \
    -d $DIM \
    -i $MOVING \
    -o ${OUTPUTNAME}.nii.gz \
    -b [200] \
    -s 3 \
    -c [50x50x30x20,1e-6]

"""
