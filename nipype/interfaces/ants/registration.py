"""The ants module provides basic functions for interfacing with ants functions.

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)
"""

from builtins import range

from ..base import TraitedSpec, File, traits, InputMultiPath
from .base import ANTSCommand, ANTSCommandInputSpec
import os
from ..traits_extension import isdefined


class ANTSInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='%d', usedefault=False,
                            position=1, desc='image dimension (2 or 3)')
    fixed_image = InputMultiPath(File(exists=True), mandatory=True,
                                 desc=('image to apply transformation to (generally a coregistered '
                                       'functional)'))
    moving_image = InputMultiPath(File(exists=True), argstr='%s',
                                  mandatory=True,
                                  desc=('image to apply transformation to (generally a coregistered '
                                        'functional)'))

#    Not all metrics are appropriate for all modalities. Also, not all metrics
#    are efficeint or appropriate at all resolution levels, Some metrics perform
#    well for gross global registraiton, but do poorly for small changes (i.e.
#    Mattes), and some metrics do well for small changes but don't work well for
#    gross level changes (i.e. 'CC').
#
#    This is a two stage registration. in the first stage
#      [ 'Mattes', .................]
#         ^^^^^^ <- First stage
#    Do a unimodal registration of the first elements of the fixed/moving input
#    list use the"CC" as the metric.
#
#    In the second stage
#      [ ....., ['Mattes','CC'] ]
#               ^^^^^^^^^^^^^^^ <- Second stage
#    Do a multi-modal registration where the first elements of fixed/moving
#    input list use 'CC' metric and that is added to 'Mattes' metric result of
#    the second elements of the fixed/moving input.
#
#    Cost = Sum_i ( metricweight[i] Metric_i ( fixedimage[i], movingimage[i]) )
    metric = traits.List(traits.Enum('CC', 'MI', 'SMI', 'PR', 'SSD',
                                     'MSQ', 'PSE'), mandatory=True, desc='')

    metric_weight = traits.List(traits.Float(), requires=['metric'], desc='')
    radius = traits.List(traits.Int(), requires=['metric'], desc='')

    output_transform_prefix = traits.Str('out', usedefault=True,
                                         argstr='--output-naming %s',
                                         mandatory=True, desc='')
    transformation_model = traits.Enum('Diff', 'Elast', 'Exp', 'Greedy Exp',
                                       'SyN', argstr='%s', mandatory=True,
                                       desc='')
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
            if self.use_histogram_matching:
                return '--use-Histogram-Matching 1'
            else:
                return '--use-Histogram-Matching 0'
        return super(ANTSInputSpec, self)._format_arg(opt, spec, val)

    def _image_metric_constructor(self):
        retval = []
        intensity_based = ['CC', 'MI', 'SMI', 'PR', 'SSD', 'MSQ']
        point_set_based = ['PSE', 'JTB']
        for ii in range(len(self.moving_image)):
            if self.metric[ii] in intensity_based:
                retval.append(
                    '--image-metric %s[ %s, %s, %g, %d ]' % (self.metric[ii],
                                                             self.fixed_image[
                                                                 ii],
                                                             self.moving_image[
                                                                 ii],
                                                             self.metric_weight[
                                                                 ii],
                                                             self.radius[ii]))
            elif self.metric[ii] == point_set_based:
                pass
                # retval.append('--image-metric %s[%s, %s, ...'.format(self.metric[ii],
                #               self.fixed_image[ii], self.moving_image[ii], ...))
        return ' '.join(retval)

    def _transformation_constructor(self):
        model = self.transformation_model
        step_length = self.gradient_step_length
        time_step = self.number_of_time_steps
        delta_time = self.delta_time
        symmetry_type = self.symmetry_type
        retval = ['--transformation-model %s' % model]
        parameters = []
        for elem in (step_length, time_step, delta_time, symmetry_type):
            if elem is not traits.Undefined:
                parameters.append('%#.2g' % elem)
        if len(parameters) > 0:
            if len(parameters) > 1:
                parameters = ','.join(parameters)
            else:
                parameters = ''.join(parameters)
            retval.append('[%s]' % parameters)
        return ''.join(retval)

    def _regularization_constructor(self):
        return '--regularization {0}[{1},{2}]'.format(self.regularization,
                                                      self.regularization_gradient_field_sigma,
                                                      self.regularization_deformation_field_sigma)

    def _affine_gradient_descent_option_constructor(self):
        values = self.affine_gradient_descent_option
        defaults = [0.1, 0.5, 1.e-4, 1.e-4]
        for ii in range(len(defaults)):
            try:
                defaults[ii] = values[ii]
            except IndexError:
                break
        parameters = self._format_xarray([('%g' % defaults[index]) for index in range(4)])
        retval = ['--affine-gradient-descent-option', parameters]
        return ' '.join(retval)


class ANTSOutputSpec(TraitedSpec):
    affine_transform = File(
        name_source='output_transform_prefix', name_template='%sAffine.txt',
        keep_extension=False, desc='Affine transform file')
    warp_transform = File(
        name_source='output_transform_prefix', name_template='%sWarp.nii.gz',
        keep_extension=False, desc='Warping deformation field')
    inverse_warp_transform = File(
        name_source='output_transform_prefix', name_template='%sInverseWarp.nii.gz',
        keep_extension=False, desc='Inverse warping deformation field')
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
    'ANTS 3 --MI-option 32x16000 --image-metric CC[ T1.nii, resting.nii, 1, 5 ] --number-of-affine-iterations \
10000x10000x10000x10000x10000 --number-of-iterations 50x35x15 --output-naming MY --regularization Gauss[3.0,0.0] \
--transformation-model SyN[0.25] --use-Histogram-Matching 1'
    """
    _cmd = 'ANTS'
    _input_spec = ANTSInputSpec
    _output_spec = ANTSOutputSpec


class RegistrationInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='--dimensionality %d',
                            usedefault=True, desc='image dimension (2 or 3)')
    fixed_image = InputMultiPath(File(exists=True), mandatory=True,
                                 desc='image to apply transformation to (generally a coregistered functional)')
    fixed_image_mask = File(argstr='%s', exists=True,
                            desc='mask used to limit metric sampling region of the fixed image')
    moving_image = InputMultiPath(File(exists=True), mandatory=True,
                                  desc='image to apply transformation to (generally a coregistered functional)')
    moving_image_mask = File(requires=['fixed_image_mask'],
                             exists=True, desc='mask used to limit metric sampling region of the moving image')

    save_state = File(argstr='--save-state %s', exists=False,
                      desc='Filename for saving the internal restorable state of the registration')
    restore_state = File(argstr='--restore-state %s', exists=True,
                         desc='Filename for restoring the internal restorable state of the registration')

    initial_moving_transform = File(argstr='%s', exists=True, desc='',
                                    xor=['initial_moving_transform_com'])
    invert_initial_moving_transform = traits.Bool(requires=["initial_moving_transform"],
        desc='', xor=['initial_moving_transform_com'])

    initial_moving_transform_com = traits.Enum(0, 1, 2, argstr='%s',
                                               default=0, xor=['initial_moving_transform'],
                                               desc="Use center of mass for moving transform")
    metric_item_trait = traits.Enum("CC", "MeanSquares", "Demons", "GC", "MI",
                                    "Mattes")
    metric_stage_trait = traits.Either(
        metric_item_trait, traits.List(metric_item_trait))
    metric = traits.List(metric_stage_trait, mandatory=True,
                         desc='the metric(s) to use for each stage. '
                         'Note that multiple metrics per stage are not supported '
                         'in ANTS 1.9.1 and earlier.')
    metric_weight_item_trait = traits.Float(1.0)
    metric_weight_stage_trait = traits.Either(
        metric_weight_item_trait, traits.List(metric_weight_item_trait))
    metric_weight = traits.List(
        metric_weight_stage_trait, value=[1.0], usedefault=True,
        requires=['metric'], mandatory=True,
        desc='the metric weight(s) for each stage. '
        'The weights must sum to 1 per stage.')
    radius_bins_item_trait = traits.Int(5)
    radius_bins_stage_trait = traits.Either(
        radius_bins_item_trait, traits.List(radius_bins_item_trait))
    radius_or_number_of_bins = traits.List(
        radius_bins_stage_trait, value=[5], usedefault=True,
        requires=['metric_weight'],
        desc='the number of bins in each stage for the MI and Mattes metric, '
        'the radius for other metrics')
    sampling_strategy_item_trait = traits.Enum(
        "None", "Regular", "Random", None)
    sampling_strategy_stage_trait = traits.Either(
        sampling_strategy_item_trait, traits.List(sampling_strategy_item_trait))
    sampling_strategy = traits.List(
        trait=sampling_strategy_stage_trait, requires=['metric_weight'],
        desc='the metric sampling strategy (strategies) for each stage')
    sampling_percentage_item_trait = traits.Either(
        traits.Range(low=0.0, high=1.0), None)
    sampling_percentage_stage_trait = traits.Either(
        sampling_percentage_item_trait, traits.List(sampling_percentage_item_trait))
    sampling_percentage = traits.List(
        trait=sampling_percentage_stage_trait, requires=['sampling_strategy'],
        desc="the metric sampling percentage(s) to use for each stage")
    use_estimate_learning_rate_once = traits.List(traits.Bool(), desc='')
    use_histogram_matching = traits.Either(
        traits.Bool, traits.List(traits.Bool(argstr='%s')),
        default=True, usedefault=True)
    interpolation = traits.Enum(
        'Linear', 'NearestNeighbor', 'CosineWindowedSinc', 'WelchWindowedSinc',
        'HammingWindowedSinc', 'LanczosWindowedSinc', 'BSpline', 'MultiLabel', 'Gaussian',
        argstr='%s', usedefault=True)
    interpolation_parameters = traits.Either(traits.Tuple(traits.Int()),  # BSpline (order)
                                             traits.Tuple(traits.Float(),  # Gaussian/MultiLabel (sigma, alpha)
                                                          traits.Float())
                                             )

    write_composite_transform = traits.Bool(
        argstr='--write-composite-transform %d',
        default=False, usedefault=True, desc='')
    collapse_output_transforms = traits.Bool(
        argstr='--collapse-output-transforms %d', default=True,
        usedefault=True,  # This should be true for explicit completeness
        desc=('Collapse output transforms. Specifically, enabling this option '
              'combines all adjacent linear transforms and composes all '
              'adjacent displacement field transforms before writing the '
              'results to disk.'))
    initialize_transforms_per_stage = traits.Bool(
        argstr='--initialize-transforms-per-stage %d', default=False,
        usedefault=True,  # This should be true for explicit completeness
        desc=('Initialize linear transforms from the previous stage. By enabling this option, '
              'the current linear stage transform is directly intialized from the previous '
              'stages linear transform; this allows multiple linear stages to be run where '
              'each stage directly updates the estimated linear transform from the previous '
              'stage. (e.g. Translation -> Rigid -> Affine). '
              ))
    # NOTE: Even though only 0=False and 1=True are allowed, ants uses integer
    # values instead of booleans
    float = traits.Bool(
        argstr='--float %d', default=False,
        desc='Use float instead of double for computations.')

    transforms = traits.List(traits.Enum('Rigid', 'Affine', 'CompositeAffine',
                                         'Similarity', 'Translation', 'BSpline',
                                         'GaussianDisplacementField', 'TimeVaryingVelocityField',
                                         'TimeVaryingBSplineVelocityField', 'SyN', 'BSplineSyN',
                                         'Exponential', 'BSplineExponential'), argstr='%s', mandatory=True)
    # TODO: input checking and allow defaults
    # All parameters must be specified for BSplineDisplacementField, TimeVaryingBSplineVelocityField, BSplineSyN,
    # Exponential, and BSplineExponential. EVEN DEFAULTS!
    transform_parameters = traits.List(traits.Either(traits.Tuple(traits.Float()),  # Translation, Rigid, Affine,
                                                                                    # CompositeAffine, Similarity
                                                     traits.Tuple(traits.Float(),  # GaussianDisplacementField, SyN
                                                                  traits.Float(),
                                                                  traits.Float()
                                                                  ),
                                                     traits.Tuple(traits.Float(),  # BSplineSyn,
                                                                  traits.Int(),    # BSplineDisplacementField,
                                                                  traits.Int(),    # TimeVaryingBSplineVelocityField
                                                                  traits.Int()
                                                                  ),
                                                     traits.Tuple(traits.Float(),  # TimeVaryingVelocityField
                                                                  traits.Int(),
                                                                  traits.Float(),
                                                                  traits.Float(),
                                                                  traits.Float(),
                                                                  traits.Float()
                                                                  ),
                                                     traits.Tuple(traits.Float(),  # Exponential
                                                                  traits.Float(),
                                                                  traits.Float(),
                                                                  traits.Int()
                                                                  ),
                                                     traits.Tuple(traits.Float(),  # BSplineExponential
                                                                  traits.Int(),
                                                                  traits.Int(),
                                                                  traits.Int(),
                                                                  traits.Int()
                                                                  ),
                                                     )
                                       )
    # Convergence flags
    number_of_iterations = traits.List(traits.List(traits.Int()))
    smoothing_sigmas = traits.List(traits.List(traits.Float()), mandatory=True)
    sigma_units = traits.List(traits.Enum('mm', 'vox'),
                              requires=['smoothing_sigmas'],
                              desc="units for smoothing sigmas")
    shrink_factors = traits.List(traits.List(traits.Int()), mandatory=True)
    convergence_threshold = traits.List(trait=traits.Float(), value=[
                                        1e-6], minlen=1, requires=['number_of_iterations'], usedefault=True)
    convergence_window_size = traits.List(trait=traits.Int(), value=[
                                          10], minlen=1, requires=['convergence_threshold'], usedefault=True)
    # Output flags
    output_transform_prefix = traits.Str(
        "transform", usedefault=True, argstr="%s", desc="")
    output_warped_image = traits.Either(
        traits.Bool, File(), hash_files=False, desc="")
    output_inverse_warped_image = traits.Either(traits.Bool, File(),
                                                hash_files=False,
                                                requires=['output_warped_image'], desc="")
    winsorize_upper_quantile = traits.Range(
        low=0.0, high=1.0, value=1.0, argstr='%s', usedefault=True, desc="The Upper quantile to clip image ranges")
    winsorize_lower_quantile = traits.Range(
        low=0.0, high=1.0, value=0.0, argstr='%s', usedefault=True, desc="The Lower quantile to clip image ranges")


    def parse_args(self, skip=None):
        if skip is None:
            skip = []

        if (isdefined(self.winsorize_upper_quantile) and
            isdefined(self.winsorize_lower_quantile)):
            skip += ['winsorize_upper_quantile']
        return super(RegistrationInputSpec, self).parse_args(skip)

    def _format_arg(self, opt, spec, val):
        if opt == 'fixed_image_mask':
            if isdefined(self.moving_image_mask):
                return '--masks [ %s, %s ]' % (self.fixed_image_mask,
                                               self.moving_image_mask)
            else:
                return '--masks %s' % self.fixed_image_mask
        elif opt == 'transforms':
            return self._format_registration()
        elif opt == 'initial_moving_transform':
            try:
                do_invert_transform = int(self.invert_initial_moving_transform)
            except ValueError:
                do_invert_transform = 0  # Just do the default behavior
            return '--initial-moving-transform [ %s, %d ]' % (self.initial_moving_transform,
                                                              do_invert_transform)
        elif opt == 'initial_moving_transform_com':
            try:
                do_center_of_mass_init = int(self.initial_moving_transform_com)
            except ValueError:
                do_center_of_mass_init = 0  # Just do the default behavior
            return '--initial-moving-transform [ %s, %s, %d ]' % (self.fixed_image[0],
                                                                  self.moving_image[0],
                                                                  do_center_of_mass_init)
        elif opt == 'interpolation':
            if self.interpolation in ['BSpline', 'MultiLabel', 'Gaussian'] and \
                    isdefined(self.interpolation_parameters):
                return '--interpolation %s[ %s ]' % (self.interpolation,
                                                     ', '.join([str(param)
                                                                for param in self.interpolation_parameters]))
            else:
                return '--interpolation %s' % self.interpolation
        elif opt == 'output_transform_prefix':
            out_filename = self._get_outputfilenames(inverse=False)
            inv_out_filename = self._get_outputfilenames(inverse=True)
            if out_filename and inv_out_filename:
                return '--output [ %s, %s, %s ]' % (self.output_transform_prefix,
                                                    out_filename,
                                                    inv_out_filename)
            elif out_filename:
                return '--output [ %s, %s ]' % (self.output_transform_prefix,
                                                out_filename)
            else:
                return '--output %s' % self.output_transform_prefix
        elif opt == 'winsorize_upper_quantile' or opt == 'winsorize_lower_quantile':
            return self._format_winsorize_image_intensities()

        # This feature was removed from recent versions of antsRegistration due to corrupt outputs.
        # elif opt == 'collapse_linear_transforms_to_fixed_image_header':
        #    return self._formatCollapseLinearTransformsToFixedImageHeader()
        return super(RegistrationInputSpec, self)._format_arg(opt, spec, val)


    def _format_metric(self, index):
        """
        Format the antsRegistration -m metric argument(s).

        Parameters
        ----------
        index: the stage index
        """
        # The metric name input for the current stage.
        name_input = self.metric[index]
        # The stage-specific input dictionary.
        stage_inputs = dict(
            fixed_image=self.fixed_image[0],
            moving_image=self.moving_image[0],
            metric=name_input,
            weight=self.metric_weight[index],
            radius_or_bins=self.radius_or_number_of_bins[index],
            optional=self.radius_or_number_of_bins[index]
        )
        # The optional sampling strategy and percentage.
        if isdefined(self.sampling_strategy) and self.sampling_strategy:
            sampling_strategy = self.sampling_strategy[index]
            if sampling_strategy:
                stage_inputs['sampling_strategy'] = sampling_strategy
        if isdefined(self.sampling_percentage) and self.sampling_percentage:
            sampling_percentage = self.sampling_percentage[index]
            if sampling_percentage:
                stage_inputs['sampling_percentage'] = sampling_percentage

        # Make a list of metric specifications, one per -m command line
        # argument for the current stage.
        # If there are multiple inputs for this stage, then convert the
        # dictionary of list inputs into a list of metric specifications.
        # Otherwise, make a singleton list of the metric specification
        # from the non-list inputs.
        if isinstance(name_input, list):
            items = list(stage_inputs.items())
            indexes = list(range(0, len(name_input)))
            specs = list()
            for i in indexes:
                temp = dict([(k, v[i]) for k, v in items])
                if len(self.fixed_image) == 1:
                    temp["fixed_image"] = self.fixed_image[0]
                else:
                    temp["fixed_image"] = self.fixed_image[i]

                if len(self.moving_image) == 1:
                    temp["moving_image"] = self.moving_image[0]
                else:
                    temp["moving_image"] = self.moving_image[i]

                specs.append(temp)
        else:
            specs = [stage_inputs]

        # Format the --metric command line metric arguments, one per
        # specification.
        return [self._format_metric_argument(**spec) for spec in specs]

    @staticmethod
    def _format_metric_argument(**kwargs):
        retval = '%s[ %s, %s, %g, %d' % (kwargs['metric'],
                                         kwargs['fixed_image'],
                                         kwargs['moving_image'],
                                         kwargs['weight'],
                                         kwargs['radius_or_bins'])

        # The optional sampling strategy.
        if 'sampling_strategy' in kwargs:
            sampling_strategy = kwargs['sampling_strategy']
        elif 'sampling_percentage' in kwargs:
            # The sampling percentage is specified but not the
            # sampling strategy. Use the default strategy.
            sampling_strategy = Registration.DEF_SAMPLING_STRATEGY
        else:
            sampling_strategy = None
        # Format the optional sampling arguments.
        if sampling_strategy:
            retval += ', %s' % sampling_strategy
            if 'sampling_percentage' in kwargs:
                retval += ', %g' % kwargs['sampling_percentage']

        retval += ' ]'

        return retval

    def _format_transform(self, index):
        retval = []
        retval.append('%s[ ' % self.transforms[index])
        parameters = ', '.join([str(
            element) for element in self.transform_parameters[index]])
        retval.append('%s' % parameters)
        retval.append(' ]')
        return "".join(retval)

    def _format_registration(self):
        retval = []
        for ii in range(len(self.transforms)):
            retval.append('--transform %s' % (self._format_transform(ii)))
            for metric in self._format_metric(ii):
                retval.append('--metric %s' % metric)
            retval.append('--convergence %s' % self._format_convergence(ii))
            if isdefined(self.sigma_units):
                retval.append('--smoothing-sigmas %s%s' %
                              (self._format_xarray(self.smoothing_sigmas[ii]),
                               self.sigma_units[ii]))
            else:
                retval.append('--smoothing-sigmas %s' %
                              self._format_xarray(self.smoothing_sigmas[ii]))
            retval.append('--shrink-factors %s' %
                          self._format_xarray(self.shrink_factors[ii]))
            if isdefined(self.use_estimate_learning_rate_once):
                retval.append('--use-estimate-learning-rate-once %d' %
                              self.use_estimate_learning_rate_once[ii])
            if isdefined(self.use_histogram_matching):
                # use_histogram_matching is either a common flag for all transforms
                # or a list of transform-specific flags
                if isinstance(self.use_histogram_matching, bool):
                    histval = self.use_histogram_matching
                else:
                    histval = self.use_histogram_matching[ii]
                retval.append('--use-histogram-matching %d' % histval)
        return " ".join(retval)

    def _get_outputfilenames(self, inverse=False):
        output_filename = None
        if not inverse:
            if isdefined(self.output_warped_image) and \
                    self.output_warped_image:
                output_filename = self.output_warped_image
                if isinstance(output_filename, bool):
                    output_filename = '%s_Warped.nii.gz' % self.output_transform_prefix
                else:
                    output_filename = output_filename
            return output_filename
        inv_output_filename = None
        if isdefined(self.output_inverse_warped_image) and \
                self.output_inverse_warped_image:
            inv_output_filename = self.output_inverse_warped_image
            if isinstance(inv_output_filename, bool):
                inv_output_filename = '%s_InverseWarped.nii.gz' % self.output_transform_prefix
            else:
                inv_output_filename = inv_output_filename
        return inv_output_filename

    def _format_convergence(self, ii):
        convergence_iter = self._format_xarray(self.number_of_iterations[ii])
        if len(self.convergence_threshold) > ii:
            convergence_value = self.convergence_threshold[ii]
        else:
            convergence_value = self.convergence_threshold[0]
        if len(self.convergence_window_size) > ii:
            convergence_ws = self.convergence_window_size[ii]
        else:
            convergence_ws = self.convergence_window_size[0]
        return '[ %s, %g, %d ]' % (convergence_iter, convergence_value, convergence_ws)

    def _format_winsorize_image_intensities(self):
        if not self.winsorize_upper_quantile > self.winsorize_lower_quantile:
            raise RuntimeError("Upper bound MUST be more than lower bound: %g > %g"
                               % (self.winsorize_upper_quantile, self.winsorize_lower_quantile))
        return '--winsorize-image-intensities [ %s, %s ]' % (self.winsorize_lower_quantile,
                                                             self.winsorize_upper_quantile)


    def _output_filenames(self, prefix, count, transform, inverse=False):
        self.low_dimensional_transform_map = {'Rigid': 'Rigid.mat',
                                              'Affine': 'Affine.mat',
                                              'GenericAffine': 'GenericAffine.mat',
                                              'CompositeAffine': 'Affine.mat',
                                              'Similarity': 'Similarity.mat',
                                              'Translation': 'Translation.mat',
                                              'BSpline': 'BSpline.txt',
                                              'Initial': 'DerivedInitialMovingTranslation.mat'}
        if transform in list(self.low_dimensional_transform_map.keys()):
            suffix = self.low_dimensional_transform_map[transform]
            inverse_mode = inverse
        else:
            inverse_mode = False  # These are not analytically invertable
            if inverse:
                suffix = 'InverseWarp.nii.gz'
            else:
                suffix = 'Warp.nii.gz'
        return '%s%d%s' % (prefix, count, suffix), inverse_mode


class RegistrationOutputSpec(TraitedSpec):
    forward_transforms = traits.List(
        File(exists=True), desc='List of output transforms for forward registration')
    reverse_transforms = traits.List(
        File(exists=True), desc='List of output transforms for reverse registration')
    forward_invert_flags = traits.List(traits.Bool(
    ), desc='List of flags corresponding to the forward transforms')
    reverse_invert_flags = traits.List(traits.Bool(
    ), desc='List of flags corresponding to the reverse transforms')
    composite_transform = File(exists=True, desc='Composite transform file')
    inverse_composite_transform = File(desc='Inverse composite transform file')
    warped_image = File(desc="Outputs warped image")
    inverse_warped_image = File(desc="Outputs the inverse of the warped image")
    save_state = File(desc="The saved registration state to be restored")


class Registration(ANTSCommand):

    """
    Examples
    --------
    >>> import copy, pprint
    >>> from nipype.interfaces.ants import Registration
    >>> reg = Registration()
    >>> reg.inputs.fixed_image = 'fixed1.nii'
    >>> reg.inputs.moving_image = 'moving1.nii'
    >>> reg.inputs.output_transform_prefix = "output_"
    >>> reg.inputs.initial_moving_transform = 'trans.mat'
    >>> reg.inputs.invert_initial_moving_transform = True
    >>> reg.inputs.transforms = ['Affine', 'SyN']
    >>> reg.inputs.transform_parameters = [(2.0,), (0.25, 3.0, 0.0)]
    >>> reg.inputs.number_of_iterations = [[1500, 200], [100, 50, 30]]
    >>> reg.inputs.dimension = 3
    >>> reg.inputs.write_composite_transform = True
    >>> reg.inputs.collapse_output_transforms = False
    >>> reg.inputs.initialize_transforms_per_stage = False
    >>> reg.inputs.metric = ['Mattes']*2
    >>> reg.inputs.metric_weight = [1]*2 # Default (value ignored currently by ANTs)
    >>> reg.inputs.radius_or_number_of_bins = [32]*2
    >>> reg.inputs.sampling_strategy = ['Random', None]
    >>> reg.inputs.sampling_percentage = [0.05, None]
    >>> reg.inputs.convergence_threshold = [1.e-8, 1.e-9]
    >>> reg.inputs.convergence_window_size = [20]*2
    >>> reg.inputs.smoothing_sigmas = [[1,0], [2,1,0]]
    >>> reg.inputs.sigma_units = ['vox'] * 2
    >>> reg.inputs.shrink_factors = [[2,1], [3,2,1]]
    >>> reg.inputs.use_estimate_learning_rate_once = [True, True]
    >>> reg.inputs.use_histogram_matching = [True, True] # This is the default
    >>> reg.inputs.output_warped_image = 'output_warped_image.nii.gz'

    >>> reg1 = copy.deepcopy(reg)
    >>> reg1.inputs.winsorize_lower_quantile = 0.025
    >>> reg1.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 0 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] \
--transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] \
--convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[ 0.25, 3.0, 0.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] --convergence [ 100x50x30, 1e-09, 20 ] \
--smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 \
--use-histogram-matching 1 --winsorize-image-intensities [ 0.025, 1.0 ] --write-composite-transform 1'
    >>> reg1.run()  # doctest: +SKIP

    >>> reg2 = copy.deepcopy(reg)
    >>> reg2.inputs.winsorize_upper_quantile = 0.975
    >>> reg2.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 0 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] \
--transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] \
--convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[ 0.25, 3.0, 0.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] --convergence [ 100x50x30, 1e-09, 20 ] \
--smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 \
--use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 0.975 ] --write-composite-transform 1'

    >>> reg3 = copy.deepcopy(reg)
    >>> reg3.inputs.winsorize_lower_quantile = 0.025
    >>> reg3.inputs.winsorize_upper_quantile = 0.975
    >>> reg3.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 0 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] \
--transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] \
--convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[ 0.25, 3.0, 0.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] --convergence [ 100x50x30, 1e-09, 20 ] \
--smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 \
--use-histogram-matching 1 --winsorize-image-intensities [ 0.025, 0.975 ] --write-composite-transform 1'

    >>> reg3a = copy.deepcopy(reg)
    >>> reg3a.inputs.float = True
    >>> reg3a.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --float 1 \
--initial-moving-transform [ trans.mat, 1 ] --initialize-transforms-per-stage 0 --interpolation Linear \
--output [ output_, output_warped_image.nii.gz ] --transform Affine[ 2.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] --convergence [ 1500x200, 1e-08, 20 ] \
--smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 \
--transform SyN[ 0.25, 3.0, 0.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] \
--convergence [ 100x50x30, 1e-09, 20 ] --smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ] \
--write-composite-transform 1'

    >>> reg3b = copy.deepcopy(reg)
    >>> reg3b.inputs.float = False
    >>> reg3b.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --float 0 \
--initial-moving-transform [ trans.mat, 1 ] --initialize-transforms-per-stage 0 --interpolation Linear \
--output [ output_, output_warped_image.nii.gz ] --transform Affine[ 2.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] --convergence [ 1500x200, 1e-08, 20 ] \
--smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 \
--transform SyN[ 0.25, 3.0, 0.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] \
--convergence [ 100x50x30, 1e-09, 20 ] --smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ] \
--write-composite-transform 1'

    >>> # Test collapse transforms flag
    >>> reg4 = copy.deepcopy(reg)
    >>> reg4.inputs.save_state = 'trans.mat'
    >>> reg4.inputs.restore_state = 'trans.mat'
    >>> reg4.inputs.initialize_transforms_per_stage = True
    >>> reg4.inputs.collapse_output_transforms = True
    >>> pprint.pprint(reg4.outputs)  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    {'composite_transform': '.../nipype/testing/data/output_Composite.h5',
     'forward_invert_flags': [],
     'forward_transforms': [],
     'inverse_composite_transform': '.../nipype/testing/data/output_InverseComposite.h5',
     'inverse_warped_image': <undefined>,
     'reverse_invert_flags': [],
     'reverse_transforms': [],
     'save_state': '.../nipype/testing/data/trans.mat',
     'warped_image': '.../nipype/testing/data/output_warped_image.nii.gz'}
    >>> reg4.cmdline
    'antsRegistration --collapse-output-transforms 1 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 1 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] \
--restore-state trans.mat --save-state trans.mat --transform Affine[ 2.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] --convergence [ 1500x200, 1e-08, 20 ] \
--smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 \
--transform SyN[ 0.25, 3.0, 0.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] \
--convergence [ 100x50x30, 1e-09, 20 ] --smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ] \
--write-composite-transform 1'

    >>> # Test collapse transforms flag
    >>> reg4b = copy.deepcopy(reg4)
    >>> reg4b.inputs.write_composite_transform = False
    >>> outputs = reg4b._list_outputs()
    >>> pprint.pprint(reg4b.outputs)  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    {'composite_transform': <undefined>,
     'forward_invert_flags': [False, False],
     'forward_transforms': ['.../nipype/testing/data/output_0GenericAffine.mat',
     '.../nipype/testing/data/output_1Warp.nii.gz'],
     'inverse_composite_transform': <undefined>,
     'inverse_warped_image': <undefined>,
     'reverse_invert_flags': [True, False],
     'reverse_transforms': ['.../nipype/testing/data/output_0GenericAffine.mat', \
'.../nipype/testing/data/output_1InverseWarp.nii.gz'],
     'save_state': '.../nipype/testing/data/trans.mat',
     'warped_image': '.../nipype/testing/data/output_warped_image.nii.gz'}
    >>> reg4b.aggregate_outputs()  # doctest: +SKIP
    >>> reg4b.cmdline
    'antsRegistration --collapse-output-transforms 1 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 1 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] \
--restore-state trans.mat --save-state trans.mat --transform Affine[ 2.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] --convergence [ 1500x200, 1e-08, 20 ] \
--smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 \
--transform SyN[ 0.25, 3.0, 0.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] \
--convergence [ 100x50x30, 1e-09, 20 ] --smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ] \
--write-composite-transform 0'

    >>> # Test multiple metrics per stage
    >>> reg5 = copy.deepcopy(reg)
    >>> reg5.inputs.fixed_image = 'fixed1.nii'
    >>> reg5.inputs.moving_image = 'moving1.nii'
    >>> reg5.inputs.metric = ['Mattes', ['Mattes', 'CC']]
    >>> reg5.inputs.metric_weight = [1, [.5,.5]]
    >>> reg5.inputs.radius_or_number_of_bins = [32, [32, 4] ]
    >>> reg5.inputs.sampling_strategy = ['Random', None] # use default strategy in second stage
    >>> reg5.inputs.sampling_percentage = [0.05, [0.05, 0.10]]
    >>> reg5.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 0 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] \
--transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] \
--convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[ 0.25, 3.0, 0.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 0.5, 32, None, 0.05 ] \
--metric CC[ fixed1.nii, moving1.nii, 0.5, 4, None, 0.1 ] --convergence [ 100x50x30, 1e-09, 20 ] \
--smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 \
--use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ] --write-composite-transform 1'

    >>> # Test multiple inputs
    >>> reg6 = copy.deepcopy(reg5)
    >>> reg6.inputs.fixed_image = ['fixed1.nii', 'fixed2.nii']
    >>> reg6.inputs.moving_image = ['moving1.nii', 'moving2.nii']
    >>> reg6.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 0 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] \
--transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] \
--convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[ 0.25, 3.0, 0.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 0.5, 32, None, 0.05 ] \
--metric CC[ fixed2.nii, moving2.nii, 0.5, 4, None, 0.1 ] --convergence [ 100x50x30, 1e-09, 20 ] \
--smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 \
--use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ] --write-composite-transform 1'

    >>> # Test Interpolation Parameters (BSpline)
    >>> reg7a = copy.deepcopy(reg)
    >>> reg7a.inputs.interpolation = 'BSpline'
    >>> reg7a.inputs.interpolation_parameters = (3,)
    >>> reg7a.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 0 --interpolation BSpline[ 3 ] --output [ output_, output_warped_image.nii.gz ] \
--transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] \
--convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[ 0.25, 3.0, 0.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] --convergence [ 100x50x30, 1e-09, 20 ] \
--smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 \
--use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ] --write-composite-transform 1'

    >>> # Test Interpolation Parameters (MultiLabel/Gaussian)
    >>> reg7b = copy.deepcopy(reg)
    >>> reg7b.inputs.interpolation = 'Gaussian'
    >>> reg7b.inputs.interpolation_parameters = (1.0, 1.0)
    >>> reg7b.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 0 --interpolation Gaussian[ 1.0, 1.0 ] \
--output [ output_, output_warped_image.nii.gz ] --transform Affine[ 2.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] --convergence [ 1500x200, 1e-08, 20 ] \
--smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 \
--transform SyN[ 0.25, 3.0, 0.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] \
--convergence [ 100x50x30, 1e-09, 20 ] --smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ] \
--write-composite-transform 1'

    >>> # Test Extended Transform Parameters
    >>> reg8 = copy.deepcopy(reg)
    >>> reg8.inputs.transforms = ['Affine', 'BSplineSyN']
    >>> reg8.inputs.transform_parameters = [(2.0,), (0.25, 26, 0, 3)]
    >>> reg8.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 0 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] \
--transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] \
--convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform BSplineSyN[ 0.25, 26, 0, 3 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] --convergence [ 100x50x30, 1e-09, 20 ] \
--smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 \
--use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ] --write-composite-transform 1'
    """
    DEF_SAMPLING_STRATEGY = 'None'
    """The default sampling strategy argument."""

    _cmd = 'antsRegistration'
    _input_spec = RegistrationInputSpec
    _output_spec = RegistrationOutputSpec
    _linear_transform_names = ['Rigid', 'Affine', 'Translation', 'CompositeAffine', 'Similarity']

    def _post_run(self):
        self.outputs.forward_transforms = []
        self.outputs.forward_invert_flags = []
        self.outputs.reverse_transforms = []
        self.outputs.reverse_invert_flags = []

        # invert_initial_moving_transform should be always defined, even if
        # there's no initial transform
        invert_initial_moving_transform = False
        if isdefined(self.inputs.invert_initial_moving_transform):
            invert_initial_moving_transform = self.inputs.invert_initial_moving_transform

        if self.inputs.write_composite_transform:
            filename = self.inputs.output_transform_prefix + 'Composite.h5'
            self.outputs.composite_transform = os.path.abspath(filename)
            filename = self.inputs.output_transform_prefix + \
                'InverseComposite.h5'
            self.outputs.inverse_composite_transform = os.path.abspath(filename)
        else:  # If composite transforms are written, then individuals are not written (as of 2014-10-26
            if not self.inputs.collapse_output_transforms:
                transform_count = 0
                if isdefined(self.inputs.initial_moving_transform):
                    self.outputs.forward_transforms.append(self.inputs.initial_moving_transform)
                    self.outputs.forward_invert_flags.append(invert_initial_moving_transform)
                    self.outputs.reverse_transforms.insert(0, self.inputs.initial_moving_transform)
                    self.outputs.reverse_invert_flags.insert(0, not invert_initial_moving_transform)  # Prepend
                    transform_count += 1
                elif isdefined(self.inputs.initial_moving_transform_com):
                    forward_filename, forward_inversemode = self._output_filenames(
                        self.inputs.output_transform_prefix,
                        transform_count,
                        'Initial')
                    reverse_filename, reverse_inversemode = self._output_filenames(
                        self.inputs.output_transform_prefix,
                        transform_count,
                        'Initial',
                        True)
                    self.outputs.forward_transforms.append(os.path.abspath(forward_filename))
                    self.outputs.forward_invert_flags.append(False)
                    self.outputs.reverse_transforms.insert(0,
                                                         os.path.abspath(reverse_filename))
                    self.outputs.reverse_invert_flags.insert(0, True)
                    transform_count += 1

                for count in range(len(self.inputs.transforms)):
                    forward_filename, forward_inversemode = self._output_filenames(
                        self.inputs.output_transform_prefix, transform_count,
                        self.inputs.transforms[count])
                    reverse_filename, reverse_inversemode = self._output_filenames(
                        self.inputs.output_transform_prefix, transform_count,
                        self.inputs.transforms[count], True)
                    self.outputs.forward_transforms.append(os.path.abspath(forward_filename))
                    self.outputs.forward_invert_flags.append(forward_inversemode)
                    self.outputs.reverse_transforms.insert(0, os.path.abspath(reverse_filename))
                    self.outputs.reverse_invert_flags.insert(0, reverse_inversemode)
                    transform_count += 1
            else:
                transform_count = 0
                is_linear = [t in self._linear_transform_names for t in self.inputs.transforms]
                collapse_list = []

                if isdefined(self.inputs.initial_moving_transform) or \
                   isdefined(self.inputs.initial_moving_transform_com):
                    is_linear.insert(0, True)

                # Only files returned by collapse_output_transforms
                if any(is_linear):
                    collapse_list.append('GenericAffine')
                if not all(is_linear):
                    collapse_list.append('SyN')

                for transform in collapse_list:
                    forward_filename, forward_inversemode = self._output_filenames(
                        self.inputs.output_transform_prefix,
                        transform_count,
                        transform,
                        inverse=False)
                    reverse_filename, reverse_inversemode = self._output_filenames(
                        self.inputs.output_transform_prefix,
                        transform_count,
                        transform,
                        inverse=True)
                    self.outputs.forward_transforms.append(os.path.abspath(forward_filename))
                    self.outputs.forward_invert_flags.append(forward_inversemode)
                    self.outputs.reverse_transforms.append(os.path.abspath(reverse_filename))
                    self.outputs.reverse_invert_flags.append(reverse_inversemode)
                    transform_count += 1

        out_filename = self._get_outputfilenames(inverse=False)
        inv_out_filename = self._get_outputfilenames(inverse=True)
        if out_filename:
            self.outputs.warped_image = os.path.abspath(out_filename)
        if inv_out_filename:
            self.outputs.inverse_warped_image = os.path.abspath(inv_out_filename)
        if len(self.inputs.save_state):
            self.outputs.save_state = os.path.abspath(self.inputs.save_state)

