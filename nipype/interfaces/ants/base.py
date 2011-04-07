"""The ANTS module provides classes for interfacing with commands from the Advanced Normalization Tools module
--------
See the docstrings of the individual classes for examples.

"""

from glob import glob
import os
import warnings
from nipype.utils.filemanip import fname_presuffix, split_filename
from nipype.interfaces.base import CommandLineInputSpec, CommandLine, traits, TraitedSpec, File
from nipype.utils.misc import isdefined

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

class ANTSInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='-i %s',
        mandatory=True, position=1,
        desc='The input .Bfloat (camino) file.')

    mask_file = File(exists=True, argstr='--mask-image %s',
        desc='this mask -- defined in the fixed image space defines the region of interest'\
              'over which the registration is computed ==> above 0.1 means inside mask ==>'\
              'continuous values in range [0.1,1.0] effect optimization like a probability. ==>'\
              'values > 1 are treated as = 1.0')

    image_metric = traits.Enum('CC', 'MI', 'SMI', 'PR', 'MSQ', 'PSE', 'JTB', argstr='--image-metric %s',
                                desc='Intensity-Based Metrics'\
        'CC/cross-correlation/CrossCorrelation[fixedImage,movingImage,weight,radius/OrForMI-#histogramBins]'\
        'MI/mutual-information/MutualInformation[fixedImage,movingImage,weight,radius/OrForMI-#histogramBins]'\
        'SMI/spatial-mutual-information/SpatialMutualInformation[fixedImage,movingImage,weight,radius/OrForMI-#histogramBins]'\
        'PR/probabilistic/Probabilistic[fixedImage,movingImage,weight,radius/OrForMI-#histogramBins]'\
        'MSQ/mean-squares/MeanSquares -- radius > 0 uses moving image gradient in metric'\
        'deriv.[fixedImage,movingImage,weight,radius/OrForMI-#histogramBins]'\
        'Point-Set-Based Metrics:'\
        'PSE/point-set-expectation/PointSetExpectation'\
        '[fixedImage,movingImage,fixedPoints,movingPoints,weight,'\
        'pointSetPercentage,pointSetSigma,boundaryPointsOnly,kNeighborhood,'\
        'PartialMatchingIterations=100000]'\
        'the partial matching option assumes the complete labeling is in the first set of label'\
        'parameters ... more iterations leads to more symmetry in the matching - 0 iterations'\
        'means full asymmetry'\
        'JTB/jensen-tsallis-bspline/JensenTsallisBSpline'\
        '[fixedImage,movingImage,fixedPoints,movingPoints,weight,pointSetPercentage,pointSetSigma,boundaryPointsOnly,kNeighborhood,'\
        'alpha,meshResolution,splineOrder,numberOfLevels,useAnisotropicCovariances]')

    iterations = traits.List(traits.Int, argstr='--number-of-iterations %d',
        desc='Number of iterations per level -- a vector e.g. : [100,100,20]',
        minlen=3, maxlen=3, sep='x')

    restrict_deformation = traits.Bool(argstr='--Restrict-Deformation %d',
        desc='restrict the gradient that drives the deformation by scalar factors along'\
        'specified dimensions -- a float vector of length ImageDimension to multiply '\
        'against the similarity metrics gradient values --- e.g. in 3D : 0.1x1x0 --- '\
        'will set the z gradient to zero and scale the x gradient by 0.1 and y by 1 (no '\
        'change). Thus, you get a 2.5-Dimensional registration as there is still 3D '\
        'continuity in the mapping.')

    transformation_model = traits.Enum('Diff', 'Elast', 'Exp', 'Greedy Exp', 'SyN', argstr='--transformation-model %s',
       desc='TRANSFORMATION'\
       '[gradient-step-length,number-of-time-steps,DeltaTime,symmetry-type].'\
       'Choose one of the following TRANSFORMATIONS:'\
       'Diff = diffeomorphic'\
       'Elast = Elastic'\
       'Exp = exponential diff'\
       'Greedy Exp = greedy exponential diff, like diffeomorphic demons. same parameters. '\
       'SyN -- symmetric normalization'\
       'DeltaTime is the integration time-discretization step - sub-voxel - n-time steps' \
       'currently fixed at 2')

    regularization = traits.Enum('Gauss', 'DMFFD', argstr='--regularization %s',
        desc='REGULARIZATION' \
        '[gradient-field-sigma,def-field-sigma,truncation].' \
        'Choose one of the following REGULARIZATIONS:' \
        'Gauss = gaussian'\
        'DMFFD = directly manipulated free form deformation '\
        '<VALUES>: Gauss[3,0.5]')

    initial_affine = File(exists=True, argstr='--initial-affine %s',
        desc='Use the input file as the initial affine parameter ')

    fixed_image_initial_affine  = File(exists=True, argstr='--fixed-image-initial-affine %s',
        desc='Use the input file as the initial affine parameter for the fixed image')

    geodesic = traits.Enum('0', '1', '2', argstr='--geodesic %s',
        desc='geodesic = 0 / 1 / 2, 0 = not time-dependent, 1 = asymmetric , 2 = symmetric')

    go_faster = traits.Bool(argstr='--go-faster',
        desc='true / false -- if true, SyN is faster but loses some accuracy wrt '\
              'inverse-identity constraint, see Avants MIA 2008.'\
              '<VALUES>: false')

    continue_affine  = traits.Bool(argstr='--continue-affine',
        desc='true (default) | false, do (not) perform affine given the initial affine parameters'\
              '<VALUES>: true')

    number_of_affine_iterations = traits.List(traits.Int, argstr='--number-of-affine-iterations %d',
        desc="Number of iterations per level -- a vector e.g. : 100x100x20"\
        "<VALUES>: 10000x10000x10000", minlen=3, maxlen=3, sep="x")

    use_nearest_neighbor = traits.Bool(argstr='--use-NN',
        desc='Use nearest neighbor interpolation'\
              '<VALUES>: 0')

    use_histogram_matching = traits.Bool(argstr='--use-Histogram-Matching',
        desc='Use histogram matching of moving to fixed image'\
              '<VALUES>: 0')

    affine_metric_type  = traits.Enum('MI', 'MSQ', 'CC', 'GD', argstr='--affine-metric-type %s',
        desc= 'MI: mutual information (default), MSQ: mean square error,'\
        'CC: Normalized correlation, CCH: Histogram-based correlation coefficient (not recommended),'\
        'GD: gradient difference (not recommended)'\
        '<VALUES>: MI')

    mutual_info_options = traits.List(traits.Int, argstr='--MI-option %d',
        desc="option of mutual information: MI_bins x MI_samples (default: 32x32000)"\
        "<VALUES>: 32x5000", minlen=2, maxlen=2, sep="x")

    rigid_affine  = traits.Bool(argstr='--rigid-affine',
        desc='use rigid transformation : true / false(default)'\
              '<VALUES>: false')

    do_rigid   = traits.Bool(argstr='--do-rigid',
        desc='use rigid transformation : true / false(default)'\
              '<VALUES>: false')

    affine_gradient_descent_options = traits.List(traits.Float, argstr='--affine-gradient-descent-option  %d',
        desc="option of gradient descent in affine transformation: "\
        "maximum_step_length x relaxation_factor x minimum_step_length x translation_scales"\
        "<VALUES>: 0.1x0.5x1.e-4x1.e-4", minlen=4, maxlen=4, sep="x")

    use_rotation_header  = traits.Bool(argstr='--use-rotation-header ',
        desc='Use rotation matrix in image headers: true (default) / false'\
              '<VALUES>: false')

    ignore_void_origin = traits.Bool(argstr='--ignore-void-origin',
        desc='ignore the apparently unmatched origins (when use-rotation-header is false and'\
              'the rotation matrix is identity: true (default) / false')

    out_file = File(argstr='-o %s', genfile=True,
        desc='The name for the output: prefix or a name+type. e.g. OUT or OUT.nii or OUT.mha')

class ANTSOutputSpec(TraitedSpec):
    output = File(exists=True, desc='The output file')

class ANTS(CommandLine):
    """ ANTS main module
    """

    _cmd = 'ANTS'
    input_spec=ANTSInputSpec
    output_spec=ANTSOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["output"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + "_ants"

class WarpImageMultiTransformInputSpec(CommandLineInputSpec):
    """WarpImageMultiTransform
Usage:

WarpImageMultiTransform ImageDimension moving_image output_image  -R reference_image --use-NN   SeriesOfTransformations--(See Below)

 SeriesOfTransformations --- WarpImageMultiTransform can apply, via concatenation, an unlimited number of transformations to your data .
 Thus, SeriesOfTransformations may be  an Affine transform followed by a warp  another affine and then another warp.
  Inverse affine transformations are invoked by calling   -i MyAffine.txt
 InverseWarps are invoked by passing the InverseWarp.nii.gz  filename (see below for a note about this).

 Example 1: Mapping a warped image into the reference_image domain by applying abcdWarpxvec.nii.gz/abcdWarpyvec.nii.gz/abcdWarpzvec.nii.gz and then abcdAffine.txt

WarpImageMultiTransform 3 moving_image output_image -R reference_image abcdWarp.nii.gz abcdAffine.txt

 Example 2: To map the fixed/reference_image warped into the moving_image domain by applying the inversion of abcdAffine.txt and then abcdInverseWarpxvec.nii.gz/abcdInverseWarpyvec.nii.gz/abcdInverseWarpzvec.nii.gz .

WarpImageMultiTransform 3 reference_image output_image -R moving_image -i  abcdAffine.txt abcdInverseWarp.nii.gz


  Note that the inverse maps (Ex. 2) are passed to this program in the reverse order of the forward maps (Ex. 1).
 This makes sense, geometrically ... see ANTS.pdf for visualization of this syntax.

 Other Example Usages:
 Reslice the image: WarpImageMultiTransform 3 Imov.nii.gz Iout.nii.gz --tightest-bounding-box --reslice-by-header
 Reslice the image to a reference image: WarpImageMultiTransform 3 Imov.nii.gz Iout.nii.gz -R Iref.nii.gz --tightest-bounding-box --reslice-by-header

 Important Notes:
 Prefixname "abcd" without any extension will use ".nii.gz" by default
 The abcdWarp and abcdInverseWarp do not exist. They are formed on the basis of abcd(Inverse)Warpxvec/yvec/zvec.nii.gz when calling WarpImageMultiTransform, yet you have to use them as if they exist.
"""
    image_dimension = traits.Enum('3', '2', argstr='%s', mandatory=True, position=1, usedefault=True
        desc='ImageDimension: 2 or 3 (for 2 or 3 Dimensional registration)')

    moving_image = File(exists=True, argstr='%s', mandatory=True, position=2,
        desc='the image to apply the transformation to')

    output_image = File(argstr='%s', mandatory=True, genfile=True, position=3,
        desc='The name for the output: prefix or a name+type. e.g. OUT or OUT.nii or OUT.mha')

    inversion_affine = File(exists=True, argstr='-i %s',
        desc='will use the inversion of the following affine transform.')

##Need to write xor for reference image for the tightest-bounding-box and reslice-by-header booleans
    compute_tightest_bounding_box = traits.Bool(argstr='--tightest-bounding-box',
        desc='Computes the tightest bounding box using all the affine transformations.'\
        'It will be overrided by -R reference_image if given.')

    reslice_by_header = traits.Bool(argstr='--reslice-by-header',
        desc='equivalent to -i -mh, or -fh -i -mh if used together with the reference_image.'\
        'It uses the orientation matrix and origin encoded in the image file header.'\
        'It can be used together with reference_image. This is typically not used together with any other transforms.')

    use_nearest_neighbor = traits.Bool(argstr='--use-NN',
        desc='Use nearest neighbor interpolation')

    use_BSpline = traits.Bool(argstr='--use-BSpline',
        desc='Use 3rd order B-Spline Interpolation.')

class WarpImageMultiTransformOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc='The output image')

class WarpImageMultiTransform(CommandLine):
    """ WarpImageMultiTransform
    """

    _cmd = 'WarpImageMultiTransform'
    input_spec=WarpImageMultiTransformInputSpec
    output_spec=WarpImageMultiTransformOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["output_image"] = os.path.abspath(self._gen_outfilename())
        return outputs
    def _gen_filename(self, name):
        if name is 'output_image':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + "_warp"
