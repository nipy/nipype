"""The ants module provides basic functions for interfacing with ants functions.

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)
"""

from ..base import (TraitedSpec, File, traits)
from .base import ANTSCommand, ANTSCommandInputSpec
import os
from nipype.interfaces.base import InputMultiPath
from nipype.interfaces.traits_extension import isdefined


class ANTSInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='%d', usedefault=False,
                            position=1, desc='image dimension (2 or 3)')
    fixed_image = InputMultiPath(File(exists=True), mandatory=True, desc=('image to apply transformation to (generally a coregistered functional)'))
    moving_image = InputMultiPath(File(exists=True), argstr='%s', mandatory=True, desc=('image to apply transformation to (generally a coregistered functional)'))

    metric = traits.List(traits.Enum('CC', 'MI', 'SMI', 'PR', 'SSD',
                         'MSQ', 'PSE'), mandatory=True, desc='')

    metric_weight = traits.List(traits.Float(), requires=['metric'], desc='')
    radius = traits.List(traits.Int(), requires=['metric'], desc='')

    output_transform_prefix = traits.Str('out', usedefault=True, argstr='--output-naming %s', mandatory=True, desc='')
    transformation_model = traits.Enum('Diff', 'Elast', 'Exp', 'Greedy Exp', 'SyN', argstr='%s', mandatory=True, desc='')
    gradient_step_length = traits.Float(
        requires=['transformation_model'], desc='')
    number_of_time_steps = traits.Float(
        requires=['gradient_step_length'], desc='')
    delta_time = traits.Float(requires=['number_of_time_steps'], desc='')
    symmetry_type = traits.Float(requires=['delta_time'], desc='')

    use_histogram_matching = traits.Bool(
        argstr='%s', default=True, usedefault=True)
    number_of_iterations = traits.List(
        traits.Int(), argstr='--number-of-iterations %s', sep='x')
    smoothing_sigmas = traits.List(
        traits.Int(), argstr='--gaussian-smoothing-sigmas %s', sep='x')
    subsampling_factors = traits.List(
        traits.Int(), argstr='--subsampling-factors %s', sep='x')
    affine_gradient_descent_option = traits.List(traits.Float(), argstr='%s')

    mi_option = traits.List(traits.Int(), argstr='--MI-option %s', sep='x')
    regularization = traits.Enum('Gauss', 'DMFFD', argstr='%s', desc='')
    regularization_gradient_field_sigma = traits.Float(
        requires=['regularization'], desc='')
    regularization_deformation_field_sigma = traits.Float(
        requires=['regularization'], desc='')
    number_of_affine_iterations = traits.List(
        traits.Int(), argstr='--number-of-affine-iterations %s', sep='x')

    # fixed_image_mask = File(exists=True, argstr='--mask-image %s', desc="this mask -- defined in the 'fixed' image space defines the region of interest over which the registration is computed ==> above 0.1 means inside mask ==> continuous values in range [0.1,1.0] effect optimization like a probability. ==> values > 1 are treated as = 1.0")
    # moving_image_mask = File(exists=True, argstr='--mask-image %s', desc="this mask -- defined in the 'moving' image space defines the region of interest over which the registration is computed ==> above 0.1 means inside mask ==> continuous values in range [0.1,1.0] effect optimization like a probability. ==> values > 1 are treated as = 1.0")


class ANTSOutputSpec(TraitedSpec):
    affine_transform = File(exists=True, desc='Affine transform file')
    warp_transform = File(exists=True, desc='Warping deformation field')
    inverse_warp_transform = File(
        exists=True, desc='Inverse warping deformation field')
    metaheader = File(exists=True, desc='VTK metaheader .mhd file')
    metaheader_raw = File(exists=True, desc='VTK metaheader .raw file')


class ANTS(ANTSCommand):
    """


    Examples
    --------

    >>> from nipype.interfaces.ants import ANTS
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
    'ANTS 3 --MI-option 32x16000 --image-metric CC[ T1.nii, resting.nii, 1, 5 ] --number-of-affine-iterations 10000x10000x10000x10000x10000 --number-of-iterations 50x35x15 --output-naming MY --regularization Gauss[3.0,0.0] --transformation-model SyN[0.25] --use-Histogram-Matching 1'
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
                retval.append(
                    '--image-metric %s[ %s, %s, %g, %d ]' % (self.inputs.metric[ii],
                                                             self.inputs.fixed_image[ii],
                                                             self.inputs.moving_image[ii],
                                                             self.inputs.metric_weight[ii],
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
            retval.append('[%s]' % parameters)
        return ''.join(retval)

    def _regularization_constructor(self):
        return '--regularization {0}[{1},{2}]'.format(self.inputs.regularization,
                                                      self.inputs.regularization_gradient_field_sigma,
                                                      self.inputs.regularization_deformation_field_sigma)

    def _affine_gradient_descent_option_constructor(self):
        retval = ['--affine-gradient-descent-option']
        values = self.inputs.affine_gradient_descent_option
        defaults = [0.1, 0.5, 1.e-4, 1.e-4]
        for ii in range(len(defaults)):
            try:
                defaults[ii] = values[ii]
            except IndexError:
                break
        stringList = [('%g' % defaults[index]) for index in range(4)]
        parameters = 'x'.join(stringList)
        retval.append(parameters)
        return ' '.join(retval)

    def _format_arg(self, opt, spec, val):
        if opt == 'moving_image':
            return self._image_metric_constructor()
        elif opt == 'transformation_model':
            return self._transformation_constructor()
        elif opt == 'regularization':
            return self._regularization_constructor()
        elif opt == 'affine_gradient_descent_option':
            return self._affine_gradient_descent_option_constructor()
        elif opt == 'use_histogram_matching':
            if self.inputs.use_histogram_matching:
                return '--use-Histogram-Matching 1'
            else:
                return '--use-Histogram-Matching 0'
        return super(ANTS, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['affine_transform'] = os.path.abspath(
            self.inputs.output_transform_prefix + 'Affine.txt')
        outputs['warp_transform'] = os.path.abspath(
            self.inputs.output_transform_prefix + 'Warp.nii.gz')
        outputs['inverse_warp_transform'] = os.path.abspath(
            self.inputs.output_transform_prefix + 'InverseWarp.nii.gz')
        #outputs['metaheader'] = os.path.abspath(self.inputs.output_transform_prefix + 'velocity.mhd')
        #outputs['metaheader_raw'] = os.path.abspath(self.inputs.output_transform_prefix + 'velocity.raw')
        return outputs


class RegistrationInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='--dimensionality %d',
                            usedefault=True, desc='image dimension (2 or 3)')
    fixed_image = InputMultiPath(File(exists=True), mandatory=True,
                                 desc='image to apply transformation to (generally a coregistered functional)')
    fixed_image_mask = File(
        mandatory=False, requires=['moving_image_mask'], exists=True, desc='')
    moving_image = InputMultiPath(File(exists=True), mandatory=True,
                                  desc='image to apply transformation to (generally a coregistered functional)')
    moving_image_mask = File(argstr='%s', mandatory=False, requires=[
                             'fixed_image_mask'], exists=True, desc='')
    initial_moving_transform = File(
        argstr='%s', mandatory=False, exists=True, desc='')
    invert_initial_moving_transform = traits.Bool(
        default=False, usedefault=True, mandatory=False,
        requires=["initial_moving_transform"], desc='')
    metric = traits.List(traits.Enum("CC", "MeanSquares", "Demons",
                         "GC", "MI", "Mattes"), mandatory=True, desc='')
    metric_weight = traits.List(
        traits.Float(1.0), usedefault=True, requires=['metric'], mandatory=True,
        desc="Note that the metricWeight is currently not used. Rather, it is a temporary place \
    holder until multivariate metrics are available for a single stage.")
    ###  This is interpreted as number_of_bins for MI and Mattes, and as radius for all other metrics
    radius_or_number_of_bins = traits.List(
        traits.Int(5), usedefault=True, requires=['metric_weight'], desc='')
    sampling_strategy = traits.List(
        trait=traits.Enum("Dense", "Regular", "Random", None), value=['Dense'], minlen=1,
        usedefault=True, requires=['metric_weight'], desc='')
    sampling_percentage = traits.List(
        trait=traits.Either(traits.Range(low=0.0, high=1.0), None), value=[None], minlen=1,
        requires=['sampling_strategy'], desc='')
    use_estimate_learning_rate_once = traits.List(traits.Bool(), desc='')
    use_histogram_matching = traits.List(
        traits.Bool(argstr='%s'), default=True, usedefault=True)
    interpolation = traits.Enum(
        'Linear', 'NearestNeighbor', 'CosineWindowedSinc', 'WelchWindowedSinc',
        'HammingWindowedSinc', 'LanczosWindowedSinc',
        # 'MultiLabel',
        # 'Gaussian',
        # 'BSpline',
        argstr='%s', usedefault=True)
    write_composite_transform = traits.Bool(argstr='--write-composite-transform %d', default=False, usedefault=True, desc='')
    collapse_output_transforms = traits.Bool(
        argstr='--collapse-output-transforms %d', default=False,
        usedefault=False,  # This should be true for explicit completeness
        desc='Collapse output transforms. Specifically, enabling this option combines all adjacent linear transforms and composes all adjacent displacement field transforms before writing the results to disk.')

    transforms = traits.List(traits.Enum('Rigid', 'Affine', 'CompositeAffine',
                                         'Similarity', 'Translation', 'BSpline',
                                         'GaussianDisplacementField', 'TimeVaryingVelocityField',
                                         'TimeVaryingBSplineVelocityField', 'SyN', 'BSplineSyN',
                                         'Exponential', 'BSplineExponential'), argstr='%s', mandatory=True)
    # TODO: transform_parameters currently supports rigid, affine, composite affine, translation, bspline, gaussian displacement field (gdf), and SyN -----ONLY-----!
    transform_parameters = traits.List(traits.Either(traits.Float(),
                                                     traits.Tuple(
                                                         traits.Float()),
                                                     traits.Tuple(traits.Float(),  # gdf & syn
                                                                  traits.Float(
                                                                  ),
                                                                  traits.Float())))
    # Convergence flags
    number_of_iterations = traits.List(traits.List(traits.Int()))
    smoothing_sigmas = traits.List(traits.List(traits.Int()))
    shrink_factors = traits.List(traits.List(traits.Int()))
    convergence_threshold = traits.List(trait=traits.Float(), value=[1e-6], minlen=1, requires=['number_of_iterations'], usedefault=True)
    convergence_window_size = traits.List(trait=traits.Int(), value=[10], minlen=1, requires=['convergence_threshold'], usedefault=True)
    # Output flags
    output_transform_prefix = traits.Str(
        "transform", usedefault=True, argstr="%s", desc="")
    output_warped_image = traits.Either(
        traits.Bool, File(), hash_files=False, desc="")
    output_inverse_warped_image = traits.Either(traits.Bool, File(
    ), hash_files=False, requires=['output_warped_image'], desc="")
    winsorize_upper_quantile = traits.Range(low=0.0, high=1.0, value=1.0, argstr='%s', usedefault=True, desc="The Upper quantile to clip image ranges")
    winsorize_lower_quantile = traits.Range(low=0.0, high=1.0, value=0.0, argstr='%s', usedefault=True, desc="The Lower quantile to clip image ranges")
    collapse_linear_transforms_to_fixed_image_header = traits.Bool(
        argstr='%s', default=False, usedefault=True, desc='')


class RegistrationOutputSpec(TraitedSpec):
    forward_transforms = traits.List(
        File(), desc='List of output transforms for forward registration')
    reverse_transforms = traits.List(
        File(), desc='List of output transforms for reverse registration')
    forward_invert_flags = traits.List(traits.Bool(
    ), desc='List of flags corresponding to the forward transforms')
    reverse_invert_flags = traits.List(traits.Bool(
    ), desc='List of flags corresponding to the reverse transforms')
    composite_transform = traits.List(File(), desc='Composite transform file')
    inverse_composite_transform = traits.List(
        File(), desc='Inverse composite transform file')


class Registration(ANTSCommand):
    """
    Examples
    --------
    >>> import copy
    >>> from nipype.interfaces.ants import Registration
    >>> reg = Registration()
    >>> reg.inputs.fixed_image = ['fixed1.nii', 'fixed2.nii']
    >>> reg.inputs.moving_image = ['moving1.nii', 'moving2.nii']
    >>> reg.inputs.output_transform_prefix = "output_"
    >>> reg.inputs.initial_moving_transform = 'trans.mat'
    >>> reg.inputs.transforms = ['Affine', 'SyN']
    >>> reg.inputs.transform_parameters = [(2.0,), (0.25, 3.0, 0.0)]
    >>> reg.inputs.number_of_iterations = [[1500, 200], [100, 50, 30]]
    >>> reg.inputs.dimension = 3
    >>> reg.inputs.write_composite_transform = True
    >>> reg.inputs.collapse_output_transforms = False
    >>> reg.inputs.metric = ['Mattes']*2
    >>> reg.inputs.metric_weight = [1]*2 # Default (value ignored currently by ANTs)
    >>> reg.inputs.radius_or_number_of_bins = [32]*2
    >>> reg.inputs.sampling_strategy = ['Random', None]
    >>> reg.inputs.sampling_percentage = [0.05, None]
    >>> reg.inputs.convergence_threshold = [1.e-8, 1.e-9]
    >>> reg.inputs.convergence_window_size = [20]*2
    >>> reg.inputs.smoothing_sigmas = [[1,0], [2,1,0]]
    >>> reg.inputs.shrink_factors = [[2,1], [3,2,1]]
    >>> reg.inputs.use_estimate_learning_rate_once = [True, True]
    >>> reg.inputs.use_histogram_matching = [True, True] # This is the default
    >>> reg.inputs.output_warped_image = 'output_warped_image.nii.gz'

    >>> reg1 = copy.deepcopy(reg)
    >>> reg1.inputs.winsorize_lower_quantile = 0.025
    >>> reg1.inputs.collapse_linear_transforms_to_fixed_image_header = False
    >>> reg1.cmdline
    'antsRegistration --collapse-linear-transforms-to-fixed-image-header 0 --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 0 ] --interpolation Linear --output [ output_, output_warped_image.nii.gz ] --transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ,Random,0.05 ] --convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1x0 --shrink-factors 2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[ 0.25, 3.0, 0.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32  ] --convergence [ 100x50x30, 1e-09, 20 ] --smoothing-sigmas 2x1x0 --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 --winsorize-image-intensities [ 0.025, 1.0 ]  --write-composite-transform 1'
    >>> reg1.run()  #doctest: +SKIP

    >>> reg2 = copy.deepcopy(reg)
    >>> reg2.inputs.winsorize_upper_quantile = 0.975
    >>> reg2.cmdline
    'antsRegistration --collapse-linear-transforms-to-fixed-image-header 0 --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 0 ] --interpolation Linear --output [ output_, output_warped_image.nii.gz ] --transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ,Random,0.05 ] --convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1x0 --shrink-factors 2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[ 0.25, 3.0, 0.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32  ] --convergence [ 100x50x30, 1e-09, 20 ] --smoothing-sigmas 2x1x0 --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 0.975 ]  --write-composite-transform 1'

    >>> reg3 = copy.deepcopy(reg)
    >>> reg3.inputs.winsorize_lower_quantile = 0.025
    >>> reg3.inputs.winsorize_upper_quantile = 0.975
    >>> reg3.cmdline
    'antsRegistration --collapse-linear-transforms-to-fixed-image-header 0 --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 0 ] --interpolation Linear --output [ output_, output_warped_image.nii.gz ] --transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ,Random,0.05 ] --convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1x0 --shrink-factors 2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[ 0.25, 3.0, 0.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32  ] --convergence [ 100x50x30, 1e-09, 20 ] --smoothing-sigmas 2x1x0 --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 --winsorize-image-intensities [ 0.025, 0.975 ]  --write-composite-transform 1'

Test collapse transforms flag
    >>> reg4 = copy.deepcopy(reg)
    >>> reg4.inputs.collapse_output_transforms = True
    >>> outputs = reg4._list_outputs()
    >>> print outputs #doctest: +ELLIPSIS
    {'reverse_invert_flags': [True, False], 'inverse_composite_transform': ['.../nipype/testing/data/output_InverseComposite.h5'], 'forward_invert_flags': [False, False], 'reverse_transforms': ['.../nipype/testing/data/output_0GenericAffine.mat', '.../nipype/testing/data/output_1InverseWarp.nii.gz'], 'composite_transform': ['.../nipype/testing/data/output_Composite.h5'], 'forward_transforms': ['.../nipype/testing/data/output_0GenericAffine.mat', '.../nipype/testing/data/output_1Warp.nii.gz']}
    >>> reg4.aggregate_outputs() #doctest: +SKIP

    """
    _cmd = 'antsRegistration'
    input_spec = RegistrationInputSpec
    output_spec = RegistrationOutputSpec
    _numberOfOutputTransforms = 0
    _quantilesDone = False

    def _optionalMetricParameters(self, index):
        if (len(self.inputs.sampling_strategy) > index) and (self.inputs.sampling_strategy[index] is not None):
            if self.inputs.sampling_strategy[index] == "Dense":
                return ''  # The default when nothing is specified
            if isdefined(self.inputs.sampling_percentage) and (self.inputs.sampling_percentage is not None):
                return ',%s,%g' % (self.inputs.sampling_strategy[index], self.inputs.sampling_percentage[index])
            else:
                return ',%s' % self.inputs.sampling_strategy[index]
        return ''

    def _formatMetric(self, index):
        retval = []
        retval.append(
            '%s[ %s, %s, %g, %d' % (self.inputs.metric[index], self.inputs.fixed_image[0],
                                    self.inputs.moving_image[
                                    0], self.inputs.metric_weight[index],
                                    self.inputs.radius_or_number_of_bins[index]))
        retval.append(' %s' % self._optionalMetricParameters(index))
        retval.append(' ]')
        return "".join(retval)

    def _formatTransform(self, index):
        retval = []
        retval.append('%s[ ' % self.inputs.transforms[index])
        parameters = ', '.join([str(
            element) for element in self.inputs.transform_parameters[index]])
        retval.append('%s' % parameters)
        retval.append(' ]')
        return "".join(retval)

    def _formatRegistration(self):
        retval = []
        for ii in range(len(self.inputs.transforms)):
            retval.append('--transform %s' % (self._formatTransform(ii)))
            retval.append('--metric %s' % self._formatMetric(ii))
            retval.append('--convergence %s' % self._formatConvergence(ii))
            retval.append('--smoothing-sigmas %s' % self._antsJoinList(
                self.inputs.smoothing_sigmas[ii]))
            retval.append('--shrink-factors %s' %
                          self._antsJoinList(self.inputs.shrink_factors[ii]))
            if isdefined(self.inputs.use_estimate_learning_rate_once):
                retval.append('--use-estimate-learning-rate-once %d' %
                              self.inputs.use_estimate_learning_rate_once[ii])
            if isdefined(self.inputs.use_histogram_matching):
                retval.append('--use-histogram-matching %d' %
                              self.inputs.use_histogram_matching[ii])
        return " ".join(retval)

    def _antsJoinList(self, antsList):
        return "x".join([str(i) for i in antsList])

    def _formatConvergence(self, ii):
        convergence_iter = self._antsJoinList(
            self.inputs.number_of_iterations[ii])
        if len(self.inputs.convergence_threshold) > ii:
            convergence_value = self.inputs.convergence_threshold[ii]
        else:
            convergence_value = self.inputs.convergence_threshold[0]
        if len(self.inputs.convergence_window_size) > ii:
            convergence_ws = self.inputs.convergence_window_size[ii]
        else:
            convergence_ws = self.inputs.convergence_window_size[0]
        return '[ %s, %g, %d ]' % (convergence_iter, convergence_value, convergence_ws)

    def _formatWinsorizeImageIntensities(self):
        assert(self.inputs.winsorize_upper_quantile > self.inputs.winsorize_lower_quantile), "Upper bound MUST be more than lower bound: %g > %g" \
            % (self.inputs.winsorize_upper_quantile, self.inputs.winsorize_lower_quantile)
        self._quantilesDone = True
        return '--winsorize-image-intensities [ %s, %s ]' % (self.inputs.winsorize_lower_quantile, self.inputs.winsorize_upper_quantile)

    def _formatCollapseLinearTransformsToFixedImageHeader(self):
        if self.inputs.collapse_linear_transforms_to_fixed_image_header:
            return '--collapse-linear-transforms-to-fixed-image-header 1'
        else:
            return '--collapse-linear-transforms-to-fixed-image-header 0'

    def _format_arg(self, opt, spec, val):
        if opt == 'moving_image_mask':
            return '--masks [ %s, %s ]' % (self.inputs.fixed_image_mask, self.inputs.moving_image_mask)
        elif opt == 'transforms':
            if self.inputs.collapse_output_transforms:
                self._numberOfOutputTransforms = 2  # Affine and displacement
            else:
                self._numberOfOutputTransforms = len(self.inputs.transforms)
            return self._formatRegistration()
        elif opt == 'initial_moving_transform':
            if self.inputs.invert_initial_moving_transform:
                return '--initial-moving-transform [ %s, 1 ]' % self.inputs.initial_moving_transform
            else:
                return '--initial-moving-transform [ %s, 0 ]' % self.inputs.initial_moving_transform
        elif opt == 'interpolation':
            # TODO: handle multilabel, gaussian, and bspline options
            return '--interpolation %s' % self.inputs.interpolation
        elif opt == 'output_transform_prefix':
            if isdefined(self.inputs.output_inverse_warped_image) and self.inputs.output_inverse_warped_image:
                return '--output [ %s, %s, %s ]' % (self.inputs.output_transform_prefix, self.inputs.output_warped_image, self.inputs.output_inverse_warped_image)
            elif isdefined(self.inputs.output_warped_image) and self.inputs.output_warped_image:
                return '--output [ %s, %s ]' % (self.inputs.output_transform_prefix, self.inputs.output_warped_image)
            else:
                return '--output %s' % self.inputs.output_transform_prefix
        elif opt == 'winsorize_upper_quantile' or opt == 'winsorize_lower_quantile':
            if not self._quantilesDone:
                return self._formatWinsorizeImageIntensities()
            return ''  # Must return something for argstr!
        elif opt == 'collapse_linear_transforms_to_fixed_image_header':
            return self._formatCollapseLinearTransformsToFixedImageHeader()
        return super(Registration, self)._format_arg(opt, spec, val)

    def _outputFileNames(self, prefix, count, transform, inverse=False):
        self.lowDimensionalTransformMap = {'Rigid': 'Rigid.mat',
                                           'Affine': 'Affine.mat',
                                           'GenericAffine': 'GenericAffine.mat',
                                           'CompositeAffine': 'Affine.mat',
                                           'Similarity': 'Similarity.mat',
                                           'Translation': 'Translation.mat',
                                           'BSpline': 'BSpline.txt'}
        if transform in self.lowDimensionalTransformMap.keys():
            suffix = self.lowDimensionalTransformMap[transform]
            inverse_mode = inverse
        else:
            inverse_mode = False  # These are not analytically invertable
            if inverse:
                suffix = 'InverseWarp.nii.gz'
            else:
                suffix = 'Warp.nii.gz'
        return '%s%d%s' % (prefix, count, suffix), inverse_mode

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['forward_transforms'] = []
        outputs['forward_invert_flags'] = []
        outputs['reverse_transforms'] = []
        outputs['reverse_invert_flags'] = []
        if not self.inputs.collapse_output_transforms:
            if isdefined(self.inputs.initial_moving_transform):
                outputs['forward_transforms'].append(
                    self.inputs.initial_moving_transform)
                outputs['forward_invert_flags'].append(
                    self.inputs.invert_initial_moving_transform)
                outputs['reverse_transforms'].insert(
                    0, self.inputs.initial_moving_transform)
                outputs['reverse_invert_flags'].insert(0, not self.inputs.invert_initial_moving_transform)  # Prepend
                transformCount = 1
                for count in range(self._numberOfOutputTransforms):
                    forwardFileName, forwardInverseMode = self._outputFileNames(self.inputs.output_transform_prefix, transformCount,
                                                                                self.inputs.transforms[count])
                    reverseFileName, reverseInverseMode = self._outputFileNames(self.inputs.output_transform_prefix, transformCount,
                                                                                self.inputs.transforms[count], True)
                    outputs['forward_transforms'].append(
                        os.path.abspath(forwardFileName))
                    outputs['forward_invert_flags'].append(forwardInverseMode)
                    outputs['reverse_transforms'].insert(
                        0, os.path.abspath(reverseFileName))
                    outputs[
                        'reverse_invert_flags'].insert(0, reverseInverseMode)
                    transformCount += 1
        else:
            transformCount = 0
            for transform in ['GenericAffine', 'SyN']:  # Only files returned by collapse_output_transforms
                forwardFileName, forwardInverseMode = self._outputFileNames(self.inputs.output_transform_prefix, transformCount, transform)
                reverseFileName, reverseInverseMode = self._outputFileNames(self.inputs.output_transform_prefix, transformCount, transform, True)
                outputs['forward_transforms'].append(
                    os.path.abspath(forwardFileName))
                outputs['forward_invert_flags'].append(forwardInverseMode)
                outputs['reverse_transforms'].append(
                    os.path.abspath(reverseFileName))
                outputs['reverse_invert_flags'].append(reverseInverseMode)
                transformCount += 1
        if self.inputs.write_composite_transform:
            fileName = self.inputs.output_transform_prefix + 'Composite.h5'
            outputs['composite_transform'] = [os.path.abspath(fileName)]
            fileName = self.inputs.output_transform_prefix + \
                'InverseComposite.h5'
            outputs['inverse_composite_transform'] = [
                os.path.abspath(fileName)]
        return outputs
