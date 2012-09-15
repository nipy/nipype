#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
# \authors David M. Welch, Jessica Forbes, Hans Johnson
"""
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)

"""
# Standard library imports
import os

# Local imports
from ..base import (CommandLine, CommandLineInputSpec,
                                    InputMultiPath, traits, TraitedSpec,
                                    isdefined, File)


class antsRegistrationInputSpec(CommandLineInputSpec):
    # Initial inputs
    fixed_image_mask = File(mandatory=False, desc=(''), requires=['moving_image_mask'], exists=True)
    moving_image_mask = File(argstr='%s', mandatory=False, desc='', requires=['fixed_image_mask'], exists=True)
    initial_moving_transform = File(argstr='%s', desc='', exists=True)
    fixed_image = InputMultiPath(File(exists=True), mandatory=True, desc=('image to apply transformation to (generally a coregistered functional)') )
    moving_image = InputMultiPath(File(exists=True), mandatory=True, desc=('image to apply transformation to (generally a coregistered functional)') )
    # Input flags
    dimension = traits.Enum(3, 2, argstr='--dimensionality %d', usedefault=True, desc='image dimension (2 or 3)')
    invert_initial_moving_transform = traits.Bool(default=False, usedefault=True, desc='', requires=["initial_moving_transform"])
    # Metric flags
    metric = traits.List(traits.Enum("CC", "MeanSquares", "Demons", "GC", "MI", "Mattes"),
                         mandatory=True, desc="")
    metric_weight = traits.List(traits.Int(1), usedefault=True,
                                requires=['metric'], mandatory=True,
                                desc="Note that the metricWeight is currently not used. \
                                Rather, it is a temporary place holder until multivariate \
                                metrics are available for a single stage.")
    ###  This is interpreted as number_of_bins for MI and Mattes, and as radius for all other metrics
    radius_or_number_of_bins = traits.List(traits.Int(5), usedefault=True,
                                 requires=['metric_weight'], desc='')
    sampling_strategy = traits.List(trait=traits.Enum("Regular", "Random", None), value=['Regular'], minlen=1, usedefault=True,
                                    requires=['metric_weight'], desc='')
    sampling_percentage = traits.List(trait=traits.Either(traits.Range(low=0.0, high=1.0),None),value=[None],minlen=1,
                                      requires=['sampling_strategy'], desc='')
    use_estimate_learning_rate_once = traits.List(traits.Bool(), desc='')
    use_histogram_matching = traits.List(traits.Bool(argstr='%s'), default=True, usedefault=True)
    # Transform flags
    write_composite_transform = traits.Bool(argstr='--write-composite-transform %d', default=False, usedefault=True, desc='')
    transforms = traits.List(traits.Enum('Rigid', 'Affine', 'CompositeAffine',
                                        'Similarity', 'Translation', 'BSpline',
                                        'GaussianDisplacementField', 'TimeVaryingVelocityField',
                                        'TimeVaryingBSplineVelocityField', 'SyN', 'BSplineSyN',
                                        'Exponential', 'BSplineExponential'), argstr='%s', mandatory=True)
    # TODO: transform_parameters currently supports rigid, affine, composite affine, translation, bspline, gaussian displacement field (gdf), and SyN -----ONLY-----!
    transform_parameters = traits.List(
        traits.Either(
            traits.Float(),
            traits.Tuple(traits.Float()),
            traits.Tuple(traits.Float(), # gdf & syn
                         traits.Float(),
                         traits.Float())))
    # Convergence flags
    number_of_iterations = traits.List(traits.List(traits.Int()))
    smoothing_sigmas = traits.List(traits.List(traits.Int()))
    shrink_factors = traits.List(traits.List(traits.Int()))
    convergence_threshold = traits.List(trait=traits.Float(), value=[1e-6],minlen=1, requires=['number_of_iterations'], usedefault=True)
    convergence_window_size = traits.List(trait=traits.Int(), value=[10],minlen=1, requires=['convergence_threshold'], usedefault=True)
    # Output flags
    output_transform_prefix = traits.Str("transform", usedefault=True, argstr="%s", desc="")
    output_warped_image = traits.Either(traits.Bool, File(), hash_files=False, desc="")
    output_inverse_warped_image = traits.Either(traits.Bool, File(), hash_files=False, requires=['output_warped_image'], desc="")


class antsRegistrationOutputSpec(TraitedSpec):
    forward_transforms = traits.List(File(exists=True), desc='List of output transforms for forward registration')
    reverse_transforms = traits.List(File(exists=True), desc='List of output transforms for reverse registration')
    forward_invert_flags = traits.List(traits.Bool(), desc='List of flags corresponding to the forward transforms')
    reverse_invert_flags = traits.List(traits.Bool(), desc='List of flags corresponding to the reverse transforms')
    composite_transform = traits.List(File(exists=True), desc='Composite transform file')
    inverse_composite_transform = traits.List(File(exists=True), desc='Inverse composite transform file')


class antsRegistration(CommandLine):
    """
    Examples
    --------
    >>> from nipype.interfaces.ants.antsRegistration import antsRegistration
    >>> reg = antsRegistration()
    >>> reg.inputs.fixed_image = ['fixed1.nii', 'fixed2.nii']
    >>> reg.inputs.moving_image = ['moving1.nii', 'moving2.nii']
    >>> reg.inputs.output_transform_prefix = "t1_average_BRAINSABC_To_template_t1_clipped"
    >>> reg.inputs.initial_moving_transform = 'trans.mat'
    >>> reg.inputs.transforms = ['Affine', 'SyN']
    >>> reg.inputs.transform_parameters = [(2.0,), (0.25, 3.0, 0.0)]
    >>> reg.inputs.number_of_iterations = [[1500, 200], [100, 50, 30]]
    >>> reg.inputs.dimension = 3
    >>> reg.inputs.write_composite_transform = True
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
    >>> reg.inputs.output_warped_image = 't1_average_BRAINSABC_To_template_t1_clipped_INTERNAL_WARPED.nii.gz'
    >>> reg.cmdline
    'antsRegistration --dimensionality 3 --initial-moving-transform [trans.mat,0] --output [t1_average_BRAINSABC_To_template_t1_clipped,t1_average_BRAINSABC_To_template_t1_clipped_INTERNAL_WARPED.nii.gz] --transform Affine[2.0] --metric Mattes[fixed1.nii,moving1.nii,1,32,Random,0.05] --convergence [1500x200,1e-08,20] --smoothing-sigmas 1x0 --shrink-factors 2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[0.25,3.0,0.0] --metric Mattes[fixed1.nii,moving1.nii,1,32] --convergence [100x50x30,1e-09,20] --smoothing-sigmas 2x1x0 --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 --write-composite-transform 1'
    """
    _cmd = 'antsRegistration'
    input_spec = antsRegistrationInputSpec
    output_spec = antsRegistrationOutputSpec


    def _optionalMetricParameters(self, index):
        if (len(self.inputs.sampling_strategy) > index) and (self.inputs.sampling_strategy[index] is not None):
            if isdefined(self.inputs.sampling_percentage):
                return ',%s,%g' % (self.inputs.sampling_strategy[index], self.inputs.sampling_percentage[index])
            else:
                return ',%s' % self.inputs.sampling_strategy[index]
        return ''

    def _formatMetric(self, index):
        retval = []
        retval.append('%s[%s,%s,%g,%d' % (self.inputs.metric[index], self.inputs.fixed_image[0],
                                        self.inputs.moving_image[0], self.inputs.metric_weight[index],
                                        self.inputs.radius_or_number_of_bins[index]))
        retval.append(self._optionalMetricParameters(index))
        retval.append(']')
        return "".join(retval)

    def _formatTransform(self, index):
        retval = []
        retval.append('%s[' % self.inputs.transforms[index])
        parameters = ','.join([str(element) for element in self.inputs.transform_parameters[index]])
        retval.append('%s' % parameters)
        retval.append(']')
        return "".join(retval)

    def _formatRegistration(self):
        retval = []
        for ii in range(len(self.inputs.transforms)):
            retval.append('--transform %s' % (self._formatTransform(ii)))
            retval.append('--metric %s' % self._formatMetric(ii))
            retval.append('--convergence %s' % self._formatConvergence(ii))
            retval.append('--smoothing-sigmas %s' % self._antsJoinList(self.inputs.smoothing_sigmas[ii]))
            retval.append('--shrink-factors %s' % self._antsJoinList(self.inputs.shrink_factors[ii]))
            if isdefined(self.inputs.use_estimate_learning_rate_once):
                retval.append('--use-estimate-learning-rate-once %d' % self.inputs.use_estimate_learning_rate_once[ii])
            if isdefined(self.inputs.use_histogram_matching):
                retval.append('--use-histogram-matching %d' % self.inputs.use_histogram_matching[ii])
        return " ".join(retval)

    def _antsJoinList(self, antsList):
        return "x".join([str(i) for i in antsList])

    def _formatConvergence(self, ii):
        convergence_iter = self._antsJoinList(self.inputs.number_of_iterations[ii])
        if len( self.inputs.convergence_threshold ) > ii:
            convergence_value=self.inputs.convergence_threshold[ii]
        else:
            convergence_value=self.inputs.convergence_threshold[0]
        if len( self.inputs.convergence_window_size ) > ii:
            convergence_ws=self.inputs.convergence_window_size[ii]
        else:
            convergence_ws=self.inputs.convergence_window_size[0]
        return '[%s,%g,%d]' % (convergence_iter, convergence_value, convergence_ws)

    def _format_arg(self, opt, spec, val):
        if opt == 'moving_image_mask':
            return '--masks [%s,%s]' % (self.inputs.fixed_image_mask, self.inputs.moving_image_mask)
        elif opt == 'transforms':
            self.numberOfTransforms = len(self.inputs.transforms)
            return self._formatRegistration()
        elif opt == 'initial_moving_transform':
            if self.inputs.invert_initial_moving_transform:
                return '--initial-moving-transform [%s,1]' % self.inputs.initial_moving_transform
            else:
                return '--initial-moving-transform [%s,0]' % self.inputs.initial_moving_transform
        elif opt == 'output_transform_prefix':
            if isdefined(self.inputs.output_inverse_warped_image) and self.inputs.output_inverse_warped_image:
                return '--output [%s,%s,%s]' % (self.inputs.output_transform_prefix, self.inputs.output_warped_image, self.inputs.output_inverse_warped_image )
            elif isdefined(self.inputs.output_warped_image) and self.inputs.output_warped_image:
                return '--output [%s,%s]'     % (self.inputs.output_transform_prefix, self.inputs.output_warped_image )
            else:
                return '--output %s' % self.inputs.output_transform_prefix
        return super(antsRegistration, self)._format_arg(opt, spec, val)

    def _outputFileNames(self, prefix, count, transform, inverse=False):
        self.transformMap = {'Rigid':'Rigid.mat',
                        'Affine':'Affine.mat',
                        'CompositeAffine':'Affine.mat',
                        'Similarity':'Similarity.mat',
                        'Translation':'Translation.mat',
                        'BSpline':'BSpline.txt'}
        if transform in self.transformMap.keys():
            suffix = self.transformMap[transform]
            return ['%s%d%s' % (prefix, count, suffix)]
        else:
            suffix = 'Warp.nii.gz'
            if inverse:
                # Happens only on recursive call below.
                # Return a string, NOT a list!
                return '%s%dInverse%s' % (prefix, count, suffix)
        return [ self._outputFileNames(prefix, count, transform, True),
                '%s%d%s' % (prefix, count, suffix)]

    def _list_outputs(self):
        outputs = self._outputs().get()
        transformCount = 0
        outputs['forward_transforms'] = []
        outputs['forward_invert_flags'] = []
        outputs['reverse_transforms'] = []
        outputs['reverse_invert_flags'] = []
        if isdefined(self.inputs.initial_moving_transform):
            outputs['forward_transforms'].append(self.inputs.initial_moving_transform)
            outputs['forward_invert_flags'].append(self.inputs.invert_initial_moving_transform)
            outputs['reverse_transforms'].append(self.inputs.initial_moving_transform)
            outputs['reverse_invert_flags'].append(not self.inputs.invert_initial_moving_transform)
            transformCount += 1
        for count in range(self.numberOfTransforms):
            fileNames = self._outputFileNames(self.inputs.output_transform_prefix,
                                              transformCount,
                                              self.inputs.transforms[count])
            if len(fileNames) == 1:
                is_invertable = True
                outputs['forward_transforms'].append(os.path.abspath(fileNames[0]))
            elif len(fileNames) == 2:
                is_invertable = False
                outputs['forward_transforms'].append(os.path.abspath(fileNames[1]))
            else:
                assert len(fileNames) <= 2
                assert len(fileNames) > 0
            outputs['forward_invert_flags'].append(not is_invertable)
            outputs['reverse_transforms'].append(os.path.abspath(fileNames[0]))
            outputs['reverse_invert_flags'].append(is_invertable)
            # if self.inputs.invert_initial_moving_transform:
            #     outputs['forward_invert_flags'].append(True)
            # else:
            #     outputs['forward_invert_flags'].append(False)
            transformCount += 1
        outputs['reverse_transforms'].reverse()
        outputs['reverse_invert_flags'].reverse()
        if self.inputs.write_composite_transform:
            fileName = self.inputs.output_transform_prefix + 'Composite.h5'
            outputs['composite_transform'] = [os.path.abspath(fileName)]
            fileName = self.inputs.output_transform_prefix + 'InverseComposite.h5'
            outputs['inverse_composite_transform'] = [os.path.abspath(fileName)]

        return outputs
