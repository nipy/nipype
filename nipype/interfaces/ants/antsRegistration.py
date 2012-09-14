#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
# \authors David M. Welch, Jessica Forbes, Hans Johnson

"""The antsRegistration module provides basic functions for interfacing with ants functions.
"""
# Standard library imports
import os
from glob import glob

# Local imports
from ..base import (CommandLine, CommandLineInputSpec,
                                    InputMultiPath, traits, TraitedSpec,
                                    OutputMultiPath, isdefined,
                                    File, Directory)
from ...utils.filemanip import split_filename


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
    write_composite_transform = traits.Bool(argstr='%s', default=False, usedefault=True, desc='')
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
    >>>
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
        elif opt == 'write_composite_transform':
            if self.inputs.write_composite_transform:
                return '--write-composite-transform 1'
            else:
                return '--write-composite-transform 0'
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


"""
COMMAND:
     antsRegistration
          This program is a user-level registration application meant to utilize
          ITKv4-only classes. The user can specify any number of "stages" where a stage
          consists of a transform; an image metric; and iterations, shrink factors, and
          smoothing sigmas for each level.

OPTIONS:
     -d, --dimensionality 2/3
          This option forces the image to be treated as a specified-dimensional image. If
          not specified, N4 tries to infer the dimensionality from the input image.

     -o, --output outputTransformPrefix
                  [outputTransformPrefix,<outputWarpedImage>,<outputInverseWarpedImage>]
          Specify the output transform prefix (output format is .nii.gz ). Optionally, one
          can choose to warp the moving image to the fixed space and, if the inverse
          transform exists, one can also output the warped fixed image.

     -q, --initial-fixed-transform initialTransform
                                   [initialTransform,<useInverse>]
          Specify the initial fixed transform(s) which get immediately incorporated into
          the composite transform. The order of the transforms is stack-esque in that the
          last transform specified on the command line is the first to be applied. See
          antsApplyTransforms for additional information.

     -a, --composite-transform-file compositeFile
          Specify name of a composite transform file to write out after registration

     -r, --initial-moving-transform initialTransform
                                    [initialTransform,<useInverse>]
          Specify the initial moving transform(s) which get immediately incorporated into
          the composite transform. The order of the transforms is stack-esque in that the
          last transform specified on the command line is the first to be applied. See
          antsApplyTransforms for additional information.

     -m, --metric          CC[fixedImage,movingImage,metricWeight,radius,      <samplingStrategy={Regular,Random}>,<samplingPercentage=[0,1]>]
                  MeanSquares[fixedImage,movingImage,metricWeight,radius,      <samplingStrategy={Regular,Random}>,<samplingPercentage=[0,1]>]
                       Demons[fixedImage,movingImage,metricWeight,radius,      <samplingStrategy={Regular,Random}>,<samplingPercentage=[0,1]>]
                           GC[fixedImage,movingImage,metricWeight,radius,      <samplingStrategy={Regular,Random}>,<samplingPercentage=[0,1]>]
                           MI[fixedImage,movingImage,metricWeight,numberOfBins,<samplingStrategy={Regular,Random}>,<samplingPercentage=[0,1]>]
                       Mattes[fixedImage,movingImage,metricWeight,numberOfBins,<samplingStrategy={Regular,Random}>,<samplingPercentage=[0,1]>]
          These image metrics are available--- CC: ANTS neighborhood cross correlation,
          MI: Mutual information, Demons: (Thirion), MeanSquares, and GC: Global
          Correlation. Note that the metricWeight is currently not used. Rather, it is a
          temporary place holder until multivariate metrics are available for a single
          stage. The metrics can also employ a sampling strategy defined by a sampling
          percentage. The sampling strategy defaults to dense, otherwise it defines a
          point set over which to optimize the metric. The point set can be on a regular
          lattice or a random lattice of points slightly perturbed to minimize aliasing
          artifacts. samplingPercentage defines the fraction of points to select from the
          domain.

     -t, --transform Rigid[gradientStep]
                     Affine[gradientStep]
                     CompositeAffine[gradientStep]
                     Similarity[gradientStep]
                     Translation[gradientStep]
                     BSpline[gradientStep,meshSizeAtBaseLevel]
                     GaussianDisplacementField[gradientStep,updateFieldVarianceInVoxelSpace,totalFieldVarianceInVoxelSpace]
                     BSplineDisplacementField[gradientStep,updateFieldMeshSizeAtBaseLevel,totalFieldMeshSizeAtBaseLevel,<splineOrder=3>]
                     TimeVaryingVelocityField[gradientStep,numberOfTimeIndices,updateFieldVarianceInVoxelSpace,updateFieldTimeVariance,totalFieldVarianceInVoxelSpace,totalFieldTimeVariance]
                     TimeVaryingBSplineVelocityField[gradientStep,velocityFieldMeshSize,<numberOfTimePointSamples=4>,<splineOrder=3>]
                     SyN[gradientStep,updateFieldVarianceInVoxelSpace,totalFieldVarianceInVoxelSpace]
                     BSplineSyN[gradientStep,updateFieldMeshSizeAtBaseLevel,totalFieldMeshSizeAtBaseLevel,<splineOrder=3>]
          Several transform options are available. The gradientStep or learningRate
          characterizes the gradient descent optimization and is scaled appropriately for
          each transform using the shift scales estimator. Subsequent parameters are
          transform-specific and can be determined from the usage.

     -c, --convergence MxNxO
                       [MxNxO,<convergenceThreshold=1e-6>,<convergenceWindowSize=10>]
          Convergence is determined from the number of iterations per leveland is
          determined by fitting a line to the normalized energy profile of the last N
          iterations (where N is specified by the window size) and determining the slope
          which is then compared with the convergence threshold.

     -s, --smoothing-sigmas MxNxO...
          Specify the amount of smoothing at each level.

     -f, --shrink-factors MxNxO...
          Specify the shrink factor for the virtual domain (typically the fixed image) at
          each level.

     -u, --use-histogram-matching
          Histogram match the images before registration.

     -l, --use-estimate-learning-rate-once
          turn on the option that lets you estimate the learning rate step size only at
          the beginning of each level. * useful as a second stage of fine-scale
          registration.

     -w, --winsorize-image-intensities [lowerQuantile,upperQuantile]
          Winsorize data based on specified quantiles.

     -x, --masks [fixedImageMask,movingImageMask]
          Image masks to limit voxels considered by the metric.

     -h
          Print the help menu (short version).
          <VALUES>: 0

     --help
          Print the help menu.
          <VALUES>: 0

=======================================================================

How to run the test case:

cd {TEST_DATA}/EXPERIEMENTS/ANTS_NIPYPE_SMALL_TEST
{BINARIES_DIRECTORY}/bin/antsRegistration \
    -d 3 \
    --mask '[SUBJ_A_small_T2_mask.nii.gz,SUBJ_B_small_T2_mask.nii.gz]' \
    -r '[20120430_1348_txfmv2fv_affine.mat,0]' \
    -o '[20120430_1348_ANTS6_,BtoA.nii.gz,AtoB.nii.gz]' \
    -m 'CC[SUBJ_A_T1_resampled.nii.gz,SUBJ_B_T1_resampled.nii.gz,1,5]' \
    -t 'SyN[0.25,3.0,0.0]' \
    -c '[100x70x20,1e-6,10]' \
    -f 3x2x1 \
    -s 0x0x0 \
    -u 1

//OPTIONAL INTERFACE FOR MULTI_MODAL_REGISTRATION:
#    -m 'CC[SUBJ_A_T2.nii.gz,SUBJ_B_T2.nii.gz,1,5]' \

=======================================================================

  Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)

"""
