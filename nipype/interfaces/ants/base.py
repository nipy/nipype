"""The ANTS module provides classes for interfacing with commands from the Advanced Normalization Tools module
--------
See the docstrings of the individual classes for examples.

"""
from glob import glob
import os
import warnings
from nipype.utils.filemanip import fname_presuffix, split_filename
from nipype.interfaces.base import CommandLineInputSpec, CommandLine, traits, TraitedSpec, File, InputMultiPath
from nipype.utils.misc import isdefined

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)




class ANTSInputSpec(CommandLineInputSpec):
    fixed_image = File(exists=True,
        desc='Fixed image')
    moving_images = InputMultiPath(File(exists=True),
        desc='Moving images')

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

    mask_file = File(exists=True, argstr='--mask-image %s',
        desc='this mask -- defined in the fixed image space defines the region of interest'\
              'over which the registration is computed ==> above 0.1 means inside mask ==>'\
              'continuous values in range [0.1,1.0] effect optimization like a probability. ==>'\
              'values > 1 are treated as = 1.0')
    iterations = traits.List(traits.Int, argstr='--number-of-iterations %s',
        desc='Number of iterations per level -- a vector e.g. : [100,100,20]',
        minlen=3, maxlen=3, sep='x')

    restrict_deformation = traits.List(traits.Float, argstr='--Restrict-Deformation %d',
        desc='restrict the gradient that drives the deformation by scalar factors along'\
        'specified dimensions -- a float vector of length ImageDimension to multiply '\
        'against the similarity metrics gradient values --- e.g. in 3D : 0.1x1x0 --- '\
        'will set the z gradient to zero and scale the x gradient by 0.1 and y by 1 (no '\
        'change). Thus, you get a 2.5-Dimensional registration as there is still 3D '\
        'continuity in the mapping.', minlen=3, maxlen=3, sep='x')

    transformation_model = traits.Enum('Diff', 'Elast', 'Exp', 'Greedy Exp', 'SyN',
        argstr='--transformation-model ',
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

    transformation_gradient_step_length = traits.Float( \
        desc='Gradient step length for transformation')
    transformation_number_of_time_steps = traits.Float( \
        desc='Number of time steps for transformation')
    transformation_delta_time = traits.Float(2,
        desc='DeltaTime is the integration time-discretization step'\
        '- sub-voxel - n-time steps currently fixed at 2')
    #transformation_symmetry_type = traits.Str(argstr=',%d',
    #    desc='Transformation symmetry type')

    regularization = traits.Enum('Gauss', 'DMFFD', argstr='--regularization ',
        desc='REGULARIZATION' \
        '[gradient-field-sigma,def-field-sigma,truncation].' \
        'Choose one of the following REGULARIZATIONS:' \
        'Gauss = gaussian'\
        'DMFFD = directly manipulated free form deformation '\
        '<VALUES>: Gauss[3,0.5]')
    regularization_gradient_field_sigma = traits.Float( \
        desc='Gradient field sigma for regularization')
    regularization_deformation_field_sigma = traits.Float( \
        desc='Deformation field sigma for regularization')
    regularization_truncation = traits.Float( \
        desc='Truncation parameter for regularization')

    initial_affine = File(exists=True, argstr='--initial-affine %s',
        desc='Use the input file as the initial affine parameter ')

    fixed_image_initial_affine  = File(exists=True, argstr='--fixed-image-initial-affine %s',
        desc='Use the input file as the initial affine parameter for the fixed image')

    geodesic = traits.Enum('not time-dependent', 'asymmetric', 'symmetric', argstr='--geodesic %s',
        desc='Geodesic; can be: not time-dependent, asymmetric, or symmetric')

    go_faster = traits.Bool(argstr='--go-faster',
        desc='true / false -- if true, SyN is faster but loses some accuracy wrt '\
              'inverse-identity constraint, see Avants MIA 2008.'\
              '<VALUES>: false')

    continue_affine  = traits.Bool(argstr='--continue-affine',
        desc='true (default) | false, do (not) perform affine given the initial affine parameters'\
              '<VALUES>: true')

    number_of_affine_iterations = traits.List(traits.Int, argstr='--number-of-affine-iterations %d',
        desc='Number of iterations per level -- a vector e.g. : 100x100x20'\
        '<VALUES>: 10000x10000x10000', minlen=3, maxlen=3, sep='x')

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
        desc='option of mutual information: MI_bins x MI_samples (default: 32x32000)'\
        '<VALUES>: 32x5000', minlen=2, maxlen=2, sep='x')

    rigid_affine  = traits.Bool(argstr='--rigid-affine',
        desc='use rigid transformation : true / false(default)'\
              '<VALUES>: false')

    do_rigid   = traits.Bool(argstr='--do-rigid',
        desc='use rigid transformation : true / false(default)'\
              '<VALUES>: false')

    affine_gradient_descent_options = traits.List(traits.Float, argstr='--affine-gradient-descent-option  %d',
        desc='option of gradient descent in affine transformation: '\
        'maximum_step_length x relaxation_factor x minimum_step_length x translation_scales'\
        '<VALUES>: 0.1x0.5x1.e-4x1.e-4', minlen=4, maxlen=4, sep='x')

    use_rotation_header  = traits.Bool(argstr='--use-rotation-header ',
        desc='Use rotation matrix in image headers: true (default) / false'\
              '<VALUES>: false')

    ignore_void_origin = traits.Bool(argstr='--ignore-void-origin',
        desc='ignore the apparently unmatched origins (when use-rotation-header is false and'\
              'the rotation matrix is identity: true (default) / false')

    out_file = File(argstr='-o %s', genfile=True,
        desc='The name for the output: prefix or a name+type. e.g. OUT or OUT.nii or OUT.mha')

    image_dimension = traits.Enum(3, 2, argstr='%d', mandatory=True, position=1, usedefault=True,
        desc='ImageDimension: 2 or 3 (for 2 or 3 Dimensional registration)')
    """
    Intensity
    """
    weight = traits.Float(desc='Weight')
    radius = traits.Float(desc='Radius')
    histogram_bins = traits.Int(desc='Histogram Bins')

    """
    POINTSET
    """
    fixed_points = traits.Int(desc='Fixed points')
    moving_points = traits.Int(desc='Moving points')
    pointset_percentage = traits.Float(desc='Point Set Percentage')
    pointset_sigma = traits.Float(desc='Point Set Sigma')
    boundary_points_only = traits.Bool(desc='Boundary points only')
    k_neighbourhood = traits.Float(desc='k Neighbourhood')

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
        _, name , _ = split_filename(self.inputs.moving_images[0])
        return name + "_ants"

    def _format_arg(self, name, spec, value):
        if name == 'geodesic':
            return spec.argstr%{"not time-dependent":'0', "asymmetric":'1', "symmetric":'2'}[value]

        if name == 'regularization':
            reglist = self.inputs.regularization + '['
            if isdefined(self.inputs.regularization_gradient_field_sigma):
                reglist += str(self.inputs.regularization_gradient_field_sigma)
            if isdefined(self.inputs.regularization_deformation_field_sigma):
                reglist += ',' + str(self.inputs.regularization_deformation_field_sigma)
            if isdefined(self.inputs.regularization_truncation):
                reglist += ',' + str(self.inputs.regularization_truncation)
            reglist += ']'
            return spec.argstr + reglist

        if name == 'transformation_model':
            translist = self.inputs.transformation_model + '['
            if isdefined(self.inputs.transformation_gradient_step_length):
                translist += str(self.inputs.transformation_gradient_step_length)
            if isdefined(self.inputs.transformation_number_of_time_steps):
                translist += ',' + str(self.inputs.transformation_number_of_time_steps)
            if isdefined(self.inputs.transformation_delta_time):
                translist += ',' + str(self.inputs.transformation_delta_time)
            translist += ']'
            return spec.argstr + translist
        return super(ANTS, self)._format_arg(name, spec, value)

class ANTS_IntensityInputSpec(ANTSInputSpec):
    weight = traits.Float(argstr='%d,',
        desc='Weight')
    radius = traits.Float(argstr='%d,',
        desc='Radius')
    histogram_bins = traits.Int(argstr='%d,',
        desc='Histogram Bins')

class ANTS_Intensity(ANTS):
    def _format_arg(self, name, spec, value):
        if name == 'image_metric':
            metriclist = self.inputs.image_metric + '['
            if isdefined(self.inputs.fixed_image):
                metriclist += str(self.inputs.fixed_image)
            if isdefined(self.inputs.moving_images):
                metriclist += ',' + ",".join(self.inputs.moving_images)
            if isdefined(self.inputs.weight):
                metriclist += ','+ str(self.inputs.weight)
            if isdefined(self.inputs.radius):
                metriclist += ',' + str(self.inputs.radius)
            if isdefined(self.inputs.histogram_bins):
                metriclist += ',' + str(self.inputs.histogram_bins)
            metriclist += ']'
            return super(ANTS_Intensity, self)._format_arg('image_metric', spec, metriclist)
        return super(ANTS_Intensity, self)._format_arg(name, spec, value)

class ANTS_PointSetInputSpec(ANTSInputSpec):
    fixed_points = traits.Int(argstr='%d,',
        desc='Fixed points')
    moving_points = traits.Int(argstr='%d,',
        desc='Moving points')
    weight = traits.Float(argstr='%d,',
        desc='Weight')
    pointset_percentage = traits.Float(argstr='%d,',
        desc='Point Set Percentage')
    pointset_sigma = traits.Float(argstr='%d,',
        desc='Point Set Sigma')
    boundary_points_only = traits.Bool(argstr='%d,',
        desc='Boundary points only')
    k_neighbourhood = traits.Float(argstr='%d,',
        desc='k Neighbourhood')

class ANTS_PointSet(ANTS):
    def _format_arg(self, name, spec, value):
        if name == 'image_metric':
            metriclist = self.inputs.image_metric + '['
            if isdefined(self.inputs.fixed_image):
                metriclist += "'" + str(self.inputs.fixed_image) + "'"
            if isdefined(self.inputs.moving_images):
                metriclist += ',' + "'" + "','".join(self.inputs.moving_images) + "'"
            if isdefined(self.inputs.fixed_points):
                metriclist += ',' + str(self.inputs.fixed_points)
            if isdefined(self.inputs.moving_points):
                metriclist += ',' + str(self.inputs.moving_points)
            if isdefined(self.inputs.weight):
                metriclist += ',' + str(self.inputs.weight)
            if isdefined(self.inputs.pointset_percentage):
                metriclist += ',' + str(self.inputs.pointset_percentage)
            if isdefined(self.inputs.pointset_sigma):
                metriclist += ',' + str(self.inputs.pointset_sigma)
            if isdefined(self.inputs.boundary_points_only):
                metriclist += ',' + str(self.inputs.boundary_points_only)
            if isdefined(self.inputs.k_neighbourhood):
                metriclist += ',' + str(self.inputs.k_neighbourhood)
            metriclist += ']'
            return super(ANTS_Intensity, self)._format_arg('image_metric', spec, metriclist)
        return super(ANTS, self)._format_arg(name, spec, value)

class ANTS_CrossCorrelation(ANTS_Intensity):
    """
    'CC/cross-correlation/CrossCorrelation[fixedImage,movingImage,weight,radius/OrForMI-#histogramBins]'\
    """
    def __init__(self, command=None, **inputs):
        inputs["image_metric"] = "CC"
        return super(ANTS_CrossCorrelation, self).__init__(command, **inputs)

class ANTS_CrossCorrelationInputSpec(ANTS_IntensityInputSpec):
    pass

class ANTS_MutualInformation(ANTS_Intensity):
    """
    'MI/mutual-information/MutualInformation
    [fixedImage,movingImage,weight,radius/OrForMI-#histogramBins]'\
    """
    def __init__(self, command=None, **inputs):
        inputs["image_metric"] = "MI"
        return super(ANTS_MutualInformation, self).__init__(command, **inputs)

class ANTS_MutualInformationInputSpec(ANTS_IntensityInputSpec):
    pass

class ANTS_SpatialMutualInformation(ANTS_Intensity):
    """
    'SMI/spatial-mutual-information/SpatialMutualInformation
    [fixedImage,movingImage,weight,radius/OrForMI-#histogramBins]'\
    """
    def __init__(self, command=None, **inputs):
        inputs["image_metric"] = "SMI"
        return super(ANTS_SpatialMutualInformation, self).__init__(command, **inputs)

class ANTS_SpatialMutualInformationInputSpec(ANTS_IntensityInputSpec):
    pass

class ANTS_Probabilistic(ANTS_Intensity):
    """
    'PR/probabilistic/Probabilistic[fixedImage,movingImage,weight,radius/OrForMI-#histogramBins]'\
    """
    def __init__(self, command=None, **inputs):
        inputs["image_metric"] = "PR"
        return super(ANTS_Probabilistic, self).__init__(command, **inputs)

class ANTS_ProbabilisticInputSpec(ANTS_IntensityInputSpec):
    pass

class ANTS_MeanSquares(ANTS_Intensity):
    """
    'MSQ/mean-squares/MeanSquares -- radius > 0 uses moving image gradient in metric'\
    'deriv.[fixedImage,movingImage,weight,radius/OrForMI-#histogramBins]'\
    """
    def __init__(self, command=None, **inputs):
        inputs["image_metric"] = "MSQ"
        return super(ANTS_MeanSquares, self).__init__(command, **inputs)

class ANTS_MeanSquaresInputSpec(ANTS_IntensityInputSpec):
    pass

class ANTS_PointSetExpectation(ANTS_PointSet):
    """
            'Point-Set-Based Metrics:'\

    'PSE/point-set-expectation/PointSetExpectation'\
        '[fixedImage,movingImage,fixedPoints,movingPoints,weight,'\
        'pointSetPercentage,pointSetSigma,boundaryPointsOnly,kNeighborhood,'\
        'PartialMatchingIterations=100000]'\
        'the partial matching option assumes the complete labeling is in the
        first set of label parameters ... more iterations leads to more symmetry
        in the matching - 0 iterations'\
        'means full asymmetry'\
    """
    def __init__(self, command=None, **inputs):
        inputs["image_metric"] = "PSE"
        return super(ANTS_PointSetExpectation, self).__init__(command, **inputs)

class ANTS_PointSetExpectationInputSpec(ANTS_PointSetInputSpec):
    partial_matching_iterations = traits.Int(100000, argstr='%d,', usedefault=True,
        desc='Partial matching iterations')

class ANTS_JensenTsallisBSpline(ANTS_PointSet):
    """
    'Point-Set-Based Metrics:'\

    'JTB/jensen-tsallis-bspline/JensenTsallisBSpline'\
        '[fixedImage,movingImage,fixedPoints,movingPoints,weight,pointSetPercentage,
        pointSetSigma,boundaryPointsOnly,kNeighborhood,'\
        'alpha,meshResolution,splineOrder,numberOfLevels,useAnisotropicCovariances]'
    """
    def __init__(self, command=None, **inputs):
        inputs["image_metric"] = "JTB"
        return super(ANTS_JensenTsallisBSpline, self).__init__(command, **inputs)

class ANTS_JensenTsallisBSplineInputSpec(ANTS_PointSetInputSpec):
    alpha = traits.Float(argstr='%d,',
        desc='Alpha')
    mesh_resolution = traits.Float(argstr='%d,',
        desc='Mesh resolution')
    number_of_levels = traits.Int(argstr='%d,',
        desc='Number of levels')
    spline_order = traits.Int(argstr='%d,',
        desc='Spline order')
    use_anisotropic_covariances = traits.Bool(argstr='%d,',
        desc='Use anisotropic covariances')

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
    image_dimension = traits.Enum(3, 2, argstr='%d', mandatory=True, position=1, usedefault=True,
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

class MultiplyImagesInputSpec(CommandLineInputSpec):
    image_dimension = traits.Enum(3, 2, argstr='%d', mandatory=True, position=1, usedefault=True,
        desc='ImageDimension: 2 or 3 (for 2 or 3 Dimensional registration)')

    in_file1 = File(exists=True, argstr='%s', mandatory=True, position=2,
        desc='the first image to multiply')

    in_file2 = File(exists=True, argstr='%s', mandatory=True, position=3,
        desc='the second image to multiply')

    out_product = File(argstr='%s', genfile=True, position=4,
        desc='The name for the output: prefix or a name+type. e.g. OUT or OUT.nii or OUT.mha')

class MultiplyImagesOutputSpec(TraitedSpec):
    product = File(exists=True, desc='The output image')

class MultiplyImages(CommandLine):
    """MultiplyImages
    Usage:

    MultiplyImages ImageDimension img1.nii img2.nii product.nii {smoothing}
    """

    _cmd = 'MultiplyImages'
    input_spec=MultiplyImagesInputSpec
    output_spec=MultiplyImagesOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["product"] = os.path.abspath(self._gen_outfilename())
        return outputs
    def _gen_filename(self, name):
        if name is 'product':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file1)
        return name + "_multiplied"

class AverageImagesInputSpec(CommandLineInputSpec):
    image_dimension = traits.Enum(3, 2, argstr='%d', mandatory=True, position=1, usedefault=True,
        desc='ImageDimension: 2 or 3 (for 2 or 3 Dimensional registration)')

    out_file = File(argstr='%s', genfile=True, position=2,
        desc='The name for the output: prefix or a name+type. e.g. OUT or OUT.nii or OUT.mha')

    normalize  = traits.Bool(argstr='%s', position=3,
        desc='Normalize: 0 (false) or 1 (true); '\
        'if true, the 2nd image is divided by its mean. This will select the largest image to average into.')

    in_files = File(exists=True, argstr='%s', mandatory=True, position=4,
        desc='the images to average')

class AverageImagesOutputSpec(TraitedSpec):
    output = File(exists=True, desc='The output image')

class AverageImages(CommandLine):
    """AverageImages
    Usage:

    AverageImages ImageDimension Outputfname.nii.gz Normalize <images>

    """

    _cmd = 'AverageImages'
    input_spec=AverageImagesInputSpec
    output_spec=AverageImagesOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["output"] = os.path.abspath(self._gen_outfilename())
        return outputs
    def _gen_filename(self, name):
        if name is 'output':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_files[0])
        return name + "_averaged"
