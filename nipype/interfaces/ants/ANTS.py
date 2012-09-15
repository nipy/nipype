# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)

"""

import os

from ..base import InputMultiPath, traits, TraitedSpec, File
from .base import ANTSCommand, ANTSCommandInputSpec

class ANTSInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='%d', usedefault=False, position=1, desc='image dimension (2 or 3)')
    fixed_image = InputMultiPath(File(exists=True), mandatory=True, desc=('image to apply transformation to (generally a coregistered functional)') )
    moving_image = InputMultiPath(File(exists=True), argstr='%s', mandatory=True, desc=('image to apply transformation to (generally a coregistered functional)') )

    metric = traits.List(traits.Enum('CC', 'MI', 'SMI', 'PR', 'SSD', 'MSQ', 'PSE'), mandatory=True, desc='')

    metric_weight = traits.List(traits.Float(), requires=['metric'], desc='')
    radius = traits.List(traits.Int(), requires=['metric'], desc='')

    output_transform_prefix = traits.Str('out', usedefault=True, argstr='%s', mandatory=True, desc='')
    transformation_model = traits.Enum('Diff', 'Elast', 'Exp', 'Greedy Exp', 'SyN', argstr='%s', mandatory=True, desc='')
    gradient_step_length = traits.Float(requires=['transformation_model'], desc='')
    number_of_time_steps = traits.Float(requires=['gradient_step_length'], desc='')
    delta_time = traits.Float(requires=['number_of_time_steps'], desc='')
    symmetry_type = traits.Float(requires=['delta_time'], desc='')

    use_histogram_matching = traits.Bool(argstr='%s', default=True, usedefault=True)
    number_of_iterations = traits.List(traits.Int(), argstr='--number-of-iterations %s', sep='x')
    smoothing_sigmas = traits.List(traits.Int(), argstr='--gaussian-smoothing-sigmas %s', sep='x')
    subsampling_factors = traits.List(traits.Int(), argstr='--subsampling-factors %s', sep='x')
    affine_gradient_descent_option = traits.List(traits.Float(), argstr='%s')

    mi_option = traits.List(traits.Int(), argstr='--MI-option %s', sep='x')
    regularization = traits.Enum('Gauss', 'DMFFD', argstr='%s', desc='')
    regularization_gradient_field_sigma = traits.Float(requires=['regularization'], desc='')
    regularization_deformation_field_sigma = traits.Float(requires=['regularization'], desc='')
    number_of_affine_iterations = traits.List(traits.Int(), argstr='--number-of-affine-iterations %s', sep='x')

    # fixed_image_mask = File(exists=True, argstr='--mask-image %s', desc="this mask -- defined in the 'fixed' image space defines the region of interest over which the registration is computed ==> above 0.1 means inside mask ==> continuous values in range [0.1,1.0] effect optimization like a probability. ==> values > 1 are treated as = 1.0")
    # moving_image_mask = File(exists=True, argstr='--mask-image %s', desc="this mask -- defined in the 'moving' image space defines the region of interest over which the registration is computed ==> above 0.1 means inside mask ==> continuous values in range [0.1,1.0] effect optimization like a probability. ==> values > 1 are treated as = 1.0")

class ANTSOutputSpec(TraitedSpec):
    affine_transform = File(exists=True, desc='Affine transform file')
    warp_transform = File(exists=True, desc='Warping deformation field')
    inverse_warp_transform = File(exists=True, desc='Inverse warping deformation field')
    metaheader = File(exists=True, desc='VTK metaheader .mhd file')
    metaheader_raw = File(exists=True, desc='VTK metaheader .raw file')


class ANTS(ANTSCommand):
    """


    Examples
    --------

    >>> from nipype.interfaces.ants.ANTS import ANTS
    >>> ants = ANTS()
    >>> ants.inputs.dimension = 3
    >>> ants.inputs.output_transform_prefix = 'MY'
    >>> ants.inputs.metric = ['CC']
    >>> ants.inputs.fixed_image = ['T1.nii']
    >>> ants.inputs.moving_image = ['resting.nii']
    >>> ants.inputs.metric_weight = [1.0]
    >>> ants.inputs.radius = [5]
    >>> ants.inputs.transformation_model = 'SyN'
    >>> ants.inputs.gradient_step_length = 0.25
    >>> ants.inputs.number_of_iterations = [50, 35, 15]
    >>> ants.inputs.use_histogram_matching = True
    >>> ants.inputs.mi_option = [32, 16000]
    >>> ants.inputs.regularization = 'Gauss'
    >>> ants.inputs.regularization_gradient_field_sigma = 3
    >>> ants.inputs.regularization_deformation_field_sigma = 0
    >>> ants.inputs.number_of_affine_iterations = [10000,10000,10000,10000,10000]
    >>> ants.cmdline
    'ANTS 3 --MI-option 32x16000 --image-metric CC[T1.nii,resting.nii,1,5] --number-of-affine-iterations 10000x10000x10000x10000x10000 --number-of-iterations 50x35x15 --output-naming MY --regularization Gauss[3.0,0.0] --transformation-model SyN[0.25] --use-Histogram-Matching 1'
    """
    _cmd = 'ANTS'
    input_spec = ANTSInputSpec
    output_spec = ANTSOutputSpec

    def _image_metric_constructor(self):
        retval = []
        intensityBased = ['CC', 'MI', 'SMI', 'PR', 'SSD', 'MSQ']
        pointSetBased = ['PSE', 'JTB']
        for ii in range(len(self.inputs.moving_image)):
            if self.inputs.metric[ii] in intensityBased:
                retval.append('--image-metric %s[%s,%s,%g,%d]' % (self.inputs.metric[ii], self.inputs.fixed_image[ii],
                                                                  self.inputs.moving_image[ii], self.inputs.metric_weight[ii],
                                                                  self.inputs.radius[ii]))
            elif self.inputs.metric[ii] == pointSetBased:
                pass
                # retval.append('--image-metric %s[%s, %s, ...'.format(self.inputs.metric[ii], self.inputs.fixed_image[ii], self.inputs.moving_image[ii], ...))
        return ' '.join(retval)

    def _transformation_constructor(self):
        model = self.inputs.transformation_model
        stepLength = self.inputs.gradient_step_length
        timeStep = self.inputs.number_of_time_steps
        deltaTime = self.inputs.delta_time
        symmetryType = self.inputs.symmetry_type
        retval = ['--transformation-model %s' % model]
        parameters = []
        for elem in (stepLength, timeStep, deltaTime, symmetryType):
            if not elem is traits.Undefined:
                parameters.append('%#.2g' % elem)
        if len(parameters) > 0:
            if len(parameters) > 1:
                parameters = ','.join(parameters)
            else:
                parameters = ''.join(parameters)
            retval.append('[%s]'% parameters)
        return ''.join(retval)

    def _regularization_constructor(self):
        return '--regularization {0}[{1},{2}]'.format(self.inputs.regularization,
                                     self.inputs.regularization_gradient_field_sigma,
                                     self.inputs.regularization_deformation_field_sigma)

    def _affine_gradient_descent_option_constructor(self):
        retval = ['--affine-gradient-descent-option']
        values = self.inputs.affine_gradient_descent_option
        defaults =  [0.1, 0.5, 1.e-4, 1.e-4]
        for ii in range(len(defaults)):
            try:
                defaults[ii] = values[ii]
            except IndexError:
                break
        index = 0
        stringList = [('%g' % defaults[index]) for index in range(4)]
        parameters = 'x'.join(stringList)
        retval.append(parameters)
        return ' '.join(retval)

    def _format_arg(self, opt, spec, val):
        if opt == 'moving_image':
            return self._image_metric_constructor()
        elif opt == 'output_transform_prefix':
            return '--output-naming %s' % self.inputs.output_transform_prefix
        elif opt == 'transformation_model':
            return self._transformation_constructor()
        elif opt == 'regularization':
            return self._regularization_constructor()
        elif opt == 'use_histogram_matching':
            if self.inputs.use_histogram_matching:
                return '--use-Histogram-Matching 1'
            else:
                return '--use-Histogram-Matching 0'
        elif opt == 'affine_gradient_descent_option':
            return self._affine_gradient_descent_option_constructor()
        return super(ANTS, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['affine_transform'] = os.path.abspath(self.inputs.output_transform_prefix + 'Affine.txt')
        outputs['warp_transform'] = os.path.abspath(self.inputs.output_transform_prefix + 'Warp.nii.gz')
        outputs['inverse_warp_transform'] = os.path.abspath(self.inputs.output_transform_prefix + 'InverseWarp.nii.gz')
        #outputs['metaheader'] = os.path.abspath(self.inputs.output_transform_prefix + 'velocity.mhd')
        #outputs['metaheader_raw'] = os.path.abspath(self.inputs.output_transform_prefix + 'velocity.raw')
        return outputs

"""
COMMAND:
       ANTS

OPTIONS:
       -x, --mask-image maskFileName
              this mask -- defined in the 'fixed' image space defines the region of interest
              over which the registration is computed ==> above 0.1 means inside mask ==>
              continuous values in range [0.1,1.0] effect optimization like a probability. ==>
              values > 1 are treated as = 1.0

       -m, --image-metric
              The metric weights are relative to the weights on the N other metrics passed to
              ANTS --- N is unlimited. So, the weight, w_i on the i^{th} metric will be
              w_i=w_i/ ( sum_i w_i ).

              Intensity-Based Metrics:
              * CC/cross-correlation/CrossCorrelation[fixedImage,movingImage,weight,radius/OrForMI-#histogramBins]
              * MI/mutual-information/MutualInformation[fixedImage,movingImage,weight,radius/OrForMI-#histogramBins]
              * SMI/spatial-mutual-information/SpatialMutualInformation[fixedImage,movingImage,weight,radius/OrForMI-#histogramBins]
              * PR/probabilistic/Probabilistic[fixedImage,movingImage,weight,radius/OrForMI-#histogramBins]
              * SSD/difference[fixedImage,movingImage,weight,radius/OrForMI-#histogramBins]
              * MSQ/mean-squares/MeanSquares/deriv.[fixedImage,movingImage,weight,radius/OrForMI-#histogramBins]

              Point-Set-Based Metrics:
              * PSE/point-set-expectation/PointSetExpectation[fixedImage,movingImage,fixedPoints,movingPoints,weight,pointSetPercentage,pointSetSigma,boundaryPointsOnly,kNeighborhood,PartialMatchingIterations=100000]
                  + the partial matching option assumes the complete labeling is in the first set of label parameters more iterations leads to more symmetry in the matching - 0 iterations means full asymmetry
              * JTB/jensen-tsallis-bspline/JensenTsallisBSpline[fixedImage,movingImage,fixedPoints,movingPoints,weight,pointSetPercentage,pointSetSigma,boundaryPointsOnly,kNeighborhood,alpha,meshResolution,splineOrder,numberOfLevels,useAnisotropicCovariances]

       -o, --output-naming
              The name for the output - a prefix or a name+type : e.g. -o OUT or -o OUT.nii or
              -o OUT.mha

       --R    TODO/FIXME: the --R sets an ROI option -- it passes a vector of parameters that
              sets the center and bounding box of the region of interest for a sub-registration. e.g. in 3D the option setting

       -r 10x12x15x50x50x25
              sets up a bounding box of size 50,50,25 with origin at 10,12,15 in voxel (should this be physical?) coordinates.
              <VALUES>: 0

       -i, --number-of-iterations
              number of iterations per level -- a 'vector' e.g. : 100x100x20
              <VALUES>: 10x10x5

       --Restrict-Deformation
              restrict the gradient that drives the deformation by scalar factors along
              specified dimensions -- a TReal 'vector' of length ImageDimension to multiply
              against the similarity metric's gradient values --- e.g. in 3D : 0.1x1x0 ---
              will set the z gradient to zero and scale the x gradient by 0.1 and y by 1 (no
              change). Thus, you get a 2.5-Dimensional registration as there is still 3D
              continuity in the mapping.
              <VALUES>: 1x1

       -v, --verbose
              verbose output

       --use-all-metrics-for-convergence
              enable to use weighted sum of all metric terms for convergence computation. By
              default, only the first metric is used
              <VALUES>: 0

       -h
              Print the help menu (short version).
              <VALUES>: 0

       --help
              Print the help menu.
              <VALUES>: 1, 0
       -t, --transformation-model
                   TRANSFORMATION[gradient-step-length,number-of-time-steps,DeltaTime,symmetry-type].
               Choose one of the following TRANSFORMATIONS:
                       * Diff = diffeomorphic
                       * Elast = Elastic
                       * Exp = exponential diff
                       * Greedy Exp = greedy exponential diff, diffeomorphic demons. same parameters.
                       * SyN = symmetric normalization

              DeltaTime is the integration time-discretization step - sub-voxel - n-time steps currently fixed at 2
              <VALUES>: SyN[0.5]

       -r, --regularization
                   REGULARIZATION[gradient-field-sigma,def-field-sigma,truncation]
              Choose one of the following REGULARIZATIONS:
                  * Gauss = gaussian
                  * DMFFD = directly manipulated free form deformation
              <VALUES>: Gauss[3,0.5]

       -a, --initial-affine
              use the input file as the initial affine parameter

       -F, --fixed-image-initial-affine
              use the input file as the initial affine parameter for the fixed image

       --fixed-image-initial-affine-ref-image
              reference space for using the input file as the initial affine parameter for the
              fixed image

       -T, --geodesic
                  0 / 1 / 2
             0 = not time-dependent, 1 = asymmetric , 2 = symmetric

       -G, --go-faster
              true / false -- if true, SyN is faster but loses some accuracy wrt
              inverse-identity constraint, see Avants MIA 2008.
              <VALUES>: false

       --continue-affine
              true (default) | false, do (not) perform affine given the initial affine
              parameters
              <VALUES>: true

       --number-of-affine-iterations
                  AxBxC
              number of iterations per level -- a 'vector' e.g. : 100x100x20
              <VALUES>: 10000x10000x10000

       --use-NN
              use nearest neighbor interpolation
              <VALUES>: 0

       --use-Histogram-Matching
              use histogram matching of moving to fixed image
              <VALUES>: 0

       --affine-metric-type <type>
              MI: mutual information (default), MSQ: mean square error, SSD, CC: Normalized
              correlation, CCH: Histogram-based correlation coefficient (not recommended), GD:
              gradient difference (not recommended)
              <VALUES>: MI

       --MI-option <AxB>
              option of mutual information: MI_bins x MI_samples (default: 32x32000)
              <VALUES>: 32x5000

       --rigid-affine
              use rigid transformation : true / false(default)
              <VALUES>: false

       --do-rigid
              use rigid transformation : true / false(default)
              <VALUES>: false

       --affine-gradient-descent-option
              option of gradient descent in affine transformation: maximum_step_length x
              relaxation_factor x minimum_step_length x translation_scales
              <VALUES>: 0.1x0.5x1.e-4x1.e-4

       --use-rotation-header
              use rotation matrix in image headers: true (default) / false
              <VALUES>: false

       --ignore-void-origin
              ignore the apparently unmatched origins (when use-rotation-header is false and
              the rotation matrix is identity: true (default) / false
              <VALUES>: false

       --gaussian-smoothing-sigmas
              At each resolution level the image is subsampled and smoothed by Gaussian
              convolution. This option allows the user to override the default smoothing by
              specifying sigma values (in mm) for smoothing both fixed and moving images for
              each resolution level.
              <VALUES>:

       --subsampling-factors
              At each resolution level the image is subsampled and smoothed by Gaussian
              convolution. This option allows the user to override the default subsampling by
              specifying the subsampling factor for both fixed and moving images for each
              resolution level.
              <VALUES>:

=======================================================================

How to run the test case:

cd {TEST_DATA}/EXPERIEMENTS/ANTS_NIPYPE_SMALL_TEST
{BINARIES_DIRECTORY}/bin/ANTS \
    3 \
    --output-naming OrigANTS_20120430_1348_ANTS6_ \
    -m CC[SUBJ_A_T1_resampled.nii.gz,SUBJ_B_T1_resampled.nii.gz,1,5] \
    -t Affine[0.25] \
    -t SyN[0.25,3.0,0.0] \
    -i 100x70x20 \
    --subsampling-factors 3x2x1 \
    --gaussian-smoothing-sigmas 0x0x0 \
    --use-Histogram-Matching 1

//OPTIONAL INTERFACE FOR MULTI_MODAL_REGISTRATION:
#    -m 'CC[SUBJ_A_T2.nii.gz,SUBJ_B_T2.nii.gz,1,5]' \

Nipype interface proposal
ants.inputs.dimensionality = 3 # [2,3]
ants.inputs.fixed_image_mask = 'maskImageFileName'
===========================================
### Note: multiple metrics can be used ###
===========================================
ants.inputs.metric = ['CC','MI','PSE']
                         = ['CrossCorrelation','MutualInformation','PointSetExpectation']
                         = ['cross-correlation','mutual-information','point-set-expectation']
ants.inputs.fixed_image = ['fixedImageFileName']
ants.inputs.moving_image = ['movingImageFileName']
ants.inputs.metric_weight = [0.3,0.4,0.3] # len() == number of metrics
ants.inputs.radius = [3] # Requires specific metrics
ants.inputs.histogram_bins = [25] # Requires specific metrics: MI & SMI
===========================================
# Requires specific metrics: PointSet-based
===========================================
ants.inputs.point_set_percentage = ... ### TODO: Find allowed values ###
ants.inputs.point_set_sigma = ... ### TODO: Find allowed values ###
ants.inputs.boundary_points_only = False
ants.inputs.k_neignborhood = ... ### TODO: Find allowed values ### Is this for kNN? Int or Float?
ants.inputs.partial_matching_iterations = 50000 # Default:100000
===========================================
ants.inputs.output_transform_prefix = 'outputFilePrefix'
                         = 'outputFileName.extension'
ants.inputs.roi_size = [50,50,25] # In voxels!!!
ants.inputs.roi_origin = [10,12.15] # In voxels!!!
ants.inputs.number_of_iterations = [100,100,20]
ants.inputs.restrict_deformation = True
ants.inputs.use_all_metrics_for_convergence = True # Default: False
===========================================
### Note: multiple transformations can be used ###
===========================================
ants.inputs.transformation_model = 'SyN' # ['Diff', 'Elast', 'Exp', Greedy Exp', 'SyN']
ants.inputs.transformation_gradient_step_length = 0.25
ants.inputs.transformation_number_of_time_steps = 3.0
ants.inputs.transformation_delta_time = 0.0
ants.inputs.transformation_symmetry_type = ... ### TODO: Find allowed values ###
===========================================
ants.inputs.regularization = 'Gauss' # ['Gauss', 'DMFFD']
ants.inputs.regularization_gradient_field_sigma = 3
ants.inputs.regularization_deformation_field_sigma = 0.5
ants.inputs.regularization_truncation = ... ### TODO: Find allowed values ###
===========================================
ants.inputs.initial_affine = 'initialAffineTransformFileName'
ants.inputs.fixed_image_initial_affine = 'initialFixedImageAffineTransformFileName'
ants.inputs.fixed_image_initial_affine_reference_image = 'initialFixedImageAffineReferenceImageFileName'
ants.inputs.geodesic = 0 # [0,1,2]
                     = 'time-independent' ['time-independent', 'asymmetric', 'symmetric'] ### TODO: Discuss this feature with Hans ###
ants.inputs.goFaster = True # This may be dependent on transformation type?
ants.inputs.continueAffine = True # (Default)
ants.inputs.numberOfAffineIterations = [10000, 10000, 10000] # len() = number of levels
ants.inputs.useNN = True
ants.inputs.useHistogramMatching = True
ants.inputs.affineMetricType = 'MI' # ['MI', 'MSQ', 'SSD', 'CC', 'CCH', 'GD'] ('CCH' & 'GD' are NOT recommended)
ants.inputs.MIOption = [32, 32000] # (Default) ### TODO: Which metric does this apply to? ###
ants.inputs.rigidAffine = False # (Default)
ants.inputs.doRigid = False #(Default)
===========================================
### TODO: What option does this section affect/require? Or does it? ###
ants.inputs.affineGradientDesentMaxStepLength = 0.1
ants.inputs.affineGradientDesentRelaxationFactor = 0.5
ants.inputs.affineGradientDesentMinStepLength = 1e-4
ants.inputs.affineGradientDesentTranslationScales = 1e-4
===========================================
ants.inputs.useRotationHeader = True # (default)
ants.inputs.ignoreVoidOrigin = True # (default) Requires: useRotationHeader == False AND rotationMatrix == Identity
ants.inputs.gaussianSmoothingSigmas = ...
ants.inputs.subsamplingFactors = [...] # len() == 2 x (number of levels) <-- 2 == number of image 'types' (fixed, moving)
===========================================

=======================================================================

  Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)

"""
