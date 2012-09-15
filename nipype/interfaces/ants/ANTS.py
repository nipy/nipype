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

    output_transform_prefix = traits.Str('out', usedefault=True, argstr='--output-naming %s', mandatory=True, desc='')
    transformation_model = traits.Enum('Diff', 'Elast', 'Exp', 'Greedy Exp', 'SyN', argstr='%s', mandatory=True, desc='')
    gradient_step_length = traits.Float(requires=['transformation_model'], desc='')
    number_of_time_steps = traits.Float(requires=['gradient_step_length'], desc='')
    delta_time = traits.Float(requires=['number_of_time_steps'], desc='')
    symmetry_type = traits.Float(requires=['delta_time'], desc='')

    use_histogram_matching = traits.Bool(argstr='--use-Histogram-Matching %d', default=True, usedefault=True)
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
        elif opt == 'transformation_model':
            return self._transformation_constructor()
        elif opt == 'regularization':
            return self._regularization_constructor()
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