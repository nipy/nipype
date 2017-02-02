# -*- coding: utf-8 -*-
"""The ants module provides basic functions for interfacing with ants
    functions.

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)
"""
import os

from ..base import TraitedSpec, File, traits, isdefined
from .base import ANTSCommand, ANTSCommandInputSpec
from ...utils.filemanip import split_filename


def _extant(field):
    return (field is not None) and isdefined(field)

class AntsMotionCorrStatsInputSpec(ANTSCommandInputSpec):
    ''' Input spec for the antsMotionCorrStats command '''
    mask = File(argstr="-x %s", mandatory=True,
                desc="compute displacements within specified mask.")
    moco = File(
        argstr="-m %s", mandatory=True,
        desc="motion correction parameter file to calculate statistics on"
    )
    output = File(argstr="-o %s", hash_files=False, mandatory=True,
                  desc="csv file to output calculated statistics into")
    framewise = traits.Bool(argstr="-f %d",
                            desc="do framwise summarywise stats")
    output_spatial_map = File(argstr='-s %s', hash_files=False,
                              desc="File to output displacement magnitude to.")

class AntsMotionCorrStatsOutputSpec(TraitedSpec):
    ''' Output spec for the antsMotionCorrStats command '''
    spatial_map = File(exists=True)
    output = File(exists=True)

class AntsMotionCorrStats(ANTSCommand):
    ''' Interface for the antsMotionCorrStats command '''

    def _gen_filename(self, name):
        return None

    def _list_outputs(self):
        outputs = self._outputs().get()
        if _extant(self.inputs.output_spatial_map):
            outputs['spatial_map'] = (
                os.path.abspath(self.inputs.output_spatial_map)
            )
        if _extant(self.inputs.output):
            outputs['output'] = os.path.abspath(self.inputs.output)
        return outputs

class AntsMotionCorrInputSpec(ANTSCommandInputSpec):
    '''Input spec for the antsMotionCorr command.'''
    dimension_desc = (
        "This option forces the image to be treated as a "
        "specified-dimensional image. If not specified, N4 tries to infer "
        "the dimensionality from the input image."
    )
    dimensionality = traits.Enum(3, 2, argstr='-d %d', usedefault=True,
                                 position=0, desc=dimension_desc, default=3)

    average_image = File(argstr='-a %s', position=1, exists=False,
                         desc="Average the input time series image.")

    output_average_image = File(hash_files=False, desc="", argstr="%s",
                                genfile=True, exists=False, usedefault=True)
    output_transform_prefix = traits.Str()
    output_warped_image = File(hash_files=False, desc="",
                               exists=False)

    metric_type = traits.Enum("CC", "MeanSquares", "Demons", "GC", "MI",
                              "Mattes", argstr="%s")
    fixed_image = File(requires=['metric_type'], desc="")
    moving_image = File(requires=['metric_type'],
                        desc="This is the 4d image to be motion corrected")
    metric_weight = traits.Float(1.0, requires=['metric_type'])
    radius_or_bins = traits.Int(desc="", requires=['metric_type'])
    sampling_strategy = traits.Enum("None", "Regular", "Random", None,
                                    requires=['metric_type'])
    sampling_percentage = traits.Either(traits.Range(low=0.0, high=1.0), None,
                                        requires=['metric_type'])

    transformation_model = traits.Enum("Affine", "Rigid", argstr="%s")
    gradient_step_length = traits.Float(requires=['transformation_model'],
                                        desc='')

    iterations = traits.Int(
        argstr="-i %d",
        desc="Specify the number of iterations at each level."
    )
    smoothing_sigmas = traits.Int(
        argstr="-s %d",
        desc="Specify the amount of smoothing at each level."
    )
    shrink_factors = traits.Int(
        argstr="-f %d",
        desc=("Specify the shrink factor for the virtual domain (typically "
              "the fixed image) at each level.")
    )
    n_images = traits.Int(
        argstr="-n %d",
        desc=("This option sets the number of images to use to construct the "
              "template image.")
    )
    use_fixed_reference_image = traits.Bool(
        argstr="-u %d",
        default=True,
        desc=("use a fixed reference image instead of the neighor in the time "
              "series.")
    )
    use_scales_estimator = traits.Bool(
        argstr="-e %d",
        default=True,
        desc="use the scale estimator to control optimization."
    )

class AntsMotionCorrOutputSpec(TraitedSpec):
    '''Output spec for the antsMotionCorr command'''
    average_image = File(exists=True, desc='Average of an image')
    composite_transform = File(desc='Composite transform file')
    inverse_composite_transform = File(desc='Inverse composite transform file')
    warped_image = File(desc="Outputs warped image")
    inverse_warped_image = File(desc="Outputs the inverse of the warped image")
    save_state = File(desc="The saved registration state to be restored")

class AntsMotionCorr(ANTSCommand):
    '''
    Examples
    -------
    >>> from nipype.interfaces.ants.preprocess import AntsMotionCorr
    >>> ants_mc = AntsMotionCorr()
    >>> ants_mc.inputs.dimensionality = 3
    >>> ants_mc.inputs.output_transform_prefix = "motcorr"
    >>> ants_mc.inputs.output_warped_image = "warped.nii.gz"
    >>> ants_mc.inputs.output_average_image = "average_image.nii.gz"
    >>> ants_mc.inputs.metric_type = "GC"
    >>> ants_mc.inputs.fixed_image = "average_image.nii.gz"
    >>> ants_mc.inputs.moving_image = "input.nii.gz"
    >>> ants_mc.inputs.metric_weight = 1
    >>> ants_mc.inputs.radius_or_bins = 1
    >>> ants_mc.inputs.sampling_strategy = "Random"
    >>> ants_mc.inputs.sampling_percentage = 0.05
    >>> ants_mc.inputs.transformation_model = "Affine"
    >>> ants_mc.inputs.gradient_step_length = 0.005
    >>> ants_mc.inputs.iterations = 10
    >>> ants_mc.inputs.smoothing_sigmas = 0
    >>> ants_mc.inputs.shrink_factors = 1
    >>> ants_mc.inputs.n_images = 10
    >>> ants_mc.inputs.use_fixed_reference_image = True
    >>> ants_mc.inputs.use_scales_estimator = True
    >>> print(ants_mc.cmdline)
    antsMotionCorr -d 3 -i 10 -m GC[average_image.nii.gz,input.nii.gz,1.0,1,Random,0.05] -n 10 -o [motcorr,warped.nii.gz,average_image.nii.gz] -f 1 -s 0 -t Affine[0.005] -u 1 -e 1

    Format and description of the affine motion correction parameters can be
    found in this PDF starting on page 555 section 3.9.16 AffineTransform:
    https://itk.org/ItkSoftwareGuide.pdf
    '''
    _cmd = 'antsMotionCorr'
    input_spec = AntsMotionCorrInputSpec
    output_spec = AntsMotionCorrOutputSpec


    def _gen_filename(self, name):
        if name == 'output_average_image':
            if _extant(self.inputs.average_image):
                pth, fname, ext = split_filename(self.inputs.average_image)
            else:
                pth, fname, ext = split_filename(self.inputs.fixed_image)
            new_fname = '{}{}{}'.format(fname, '_avg', ext)
            return os.path.join(pth, new_fname)
        if name == 'ouput_warped_image' and _extant(self.inputs.fixed_image):
            pth, fname, ext = split_filename(self.inputs.fixed_image)
            new_fname = '{}{}{}'.format(fname, '_warped', ext)
            return os.path.join(pth, new_fname)
        return None

    def _format_arg(self, opt, spec, val):
        if opt == 'metric_type':
            return self._format_metric()
        if opt == 'transformation_model':
            return self._format_transform()
        if opt == 'output_average_image':
            self.inputs.output_average_image = self._gen_filename("output_average_image")
            return self._format_output()
        return super(AntsMotionCorr, self)._format_arg(opt, spec, val)

    def _format_metric(self):
        metric_str = ("-m {metric_type}[{fixed_image},{moving_image},"
                      "{metric_weight},{radius_or_bins},{sampling_strategy},"
                      "{sampling_percentage}]")
        format_args = {}
        metric_args = ["metric_type", "fixed_image", "moving_image",
                       "metric_weight", "radius_or_bins", "sampling_strategy",
                       "sampling_percentage"]
        for metric_arg in metric_args:
            if _extant(getattr(self.inputs, metric_arg)):
                format_args[metric_arg] = getattr(self.inputs, metric_arg)
        return metric_str.format(**format_args)

    def _format_transform(self):
        transform_str = "-t {}[{}]"
        if (_extant(self.inputs.transformation_model)
                and _extant(self.inputs.gradient_step_length)):
            return transform_str.format(self.inputs.transformation_model,
                                        self.inputs.gradient_step_length)
        return " bad format "

    def _format_output(self):
        if (_extant(self.inputs.output_transform_prefix)
                and _extant(self.inputs.output_warped_image)
                and _extant(self.inputs.output_average_image)):
            return "-o [{},{},{}]".format(
                self.inputs.output_transform_prefix,
                self.inputs.output_warped_image,
                self.inputs.output_average_image
            )
        elif _extant(self.inputs.output_average_image):
            return "-o {}".format(self.inputs.output_average_image)
        return ""

    # motcorr_avg.nii.gz  motcorrMOCOparams.csv  motcorr.nii.gz
    def _list_outputs(self):
        outputs = self._outputs().get()
        if _extant(self.inputs.output_average_image):
            outputs['average_image'] = (
                os.path.abspath(self.inputs.output_average_image)
            )
        if _extant(self.inputs.output_warped_image):
            outputs['warped_image'] = (
                os.path.abspath(self.inputs.output_warped_image)
            )
        if _extant(self.inputs.output_transform_prefix):
            outputs['composite_transform'] = '{}MOCOparams.csv'.format(
                self.inputs.output_transform_prefix
            )
        return outputs
