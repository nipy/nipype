# -*- coding: utf-8 -*-
"""The ants module provides basic functions for interfacing with ants
    functions.
"""
import csv
import os

import numpy as np
import nibabel as nb
from nibabel.eulerangles import mat2euler

from ..base import (BaseInterface, BaseInterfaceInputSpec, TraitedSpec, File,
                    traits, isdefined, Str)
from .base import ANTSCommand, ANTSCommandInputSpec
from ...utils.filemanip import split_filename


ITK_TFM_HEADER = "#Insight Transform File V1.0"
ITK_TFM_TPL = """\
#Transform {tf_id}
Transform: {tf_type}
Parameters: {tf_params}
FixedParameters: {fixed_params}""".format


class MotionCorrStatsInputSpec(ANTSCommandInputSpec):
    ''' Input spec for the antsMotionCorrStats command '''
    mask = File(argstr="-x %s", mandatory=True,
                desc="compute displacements within specified mask.")
    moco = File(
        argstr="-m %s", mandatory=True,
        desc="motion correction parameter file to calculate statistics on"
    )
    output = File(name_source=['moco'], name_template='%s_fd.csv', keep_ext=False,
                  argstr="-o %s", hash_files=False,
                  desc="csv file to output calculated statistics into")
    framewise = traits.Bool(argstr="-f %d",
                            desc="do framwise summarywise stats")
    output_spatial_map = File(argstr='-s %s', hash_files=False,
                              desc="File to output displacement magnitude to.")

class MotionCorrStatsOutputSpec(TraitedSpec):
    ''' Output spec for the antsMotionCorrStats command '''
    spatial_map = File(desc="output image of displacement magnitude", exists=True)
    output = File(desc="CSV file containg motion correction statistics", exists=True)

class MotionCorrStats(ANTSCommand):
    """
    Interface for the antsMotionCorrStats command

    Example
    -------

    >>> from nipype.interfaces.ants import MotionCorrStats
    >>> stats = MotionCorrStats(framewise=True)
    >>> stats.inputs.mask = 'brain_mask.nii'
    >>> stats.inputs.moco = 'ants_moco.csv'
    >>> stats.cmdline  # doctest: +ALLOW_UNICODE
    'antsMotionCorrStats -f 1 -x brain_mask.nii -m ants_moco.csv -o ants_moco_fd.csv'

    """

    _cmd = 'antsMotionCorrStats'
    input_spec = MotionCorrStatsInputSpec
    output_spec = MotionCorrStatsOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.output_spatial_map):
            outputs['spatial_map'] = (
                os.path.abspath(self.inputs.output_spatial_map)
            )
        return outputs

class MotionCorrInputSpec(ANTSCommandInputSpec):
    '''Input spec for the antsMotionCorr command.'''

    dimensionality = traits.Enum(
        3, 2, argstr='-d %d', usedefault=True, position=0,
        desc=(
            "This option forces the image to be treated as a "
            "specified-dimensional image. If not specified, N4 tries to infer "
            "the dimensionality from the input image."
    ))

    average_image = File(argstr='-a %s', position=1, exists=False,
                         desc="4D image to take an average of.")

    output_average_image = traits.File(desc="Filename to save average of input image as.",
                                       genfile=True, hash_files=False, argstr='%s')

    output_transform_prefix = Str(
        '', desc="string to prepend to file containg the transformation parameters"
    )
    output_warped_image = Str(desc="Name to save motion corrected image as.")
    metric_type = traits.Enum(
        "CC", "MeanSquares", "Demons", "GC", "MI", "Mattes", argstr="%s",
        desc=(
            "GC : global correlation, CC: ANTS neighborhood cross correlation, "
            "MI: Mutual information, and Demons: Thirion's Demons "
            "(modified mean-squares). Note that the metricWeight is currently not "
            "used. Rather, it is a temporary place holder until multivariate "
            "metrics are available for a single stage."
    ))
    fixed_image = File(requires=['metric_type'],
                       desc="Fixed image to do motion correction with respect to.")
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

    iterations = traits.List(traits.Int, argstr='-i %s', sep='x',
                             desc="Specify the number of iterations at each level.")

    smoothing_sigmas = traits.List(traits.Float, argstr='-s %s', sep='x',
                                   desc="Specify the amount of smoothing at each level.")

    shrink_factors = traits.List(
        traits.Int,
        argstr='-f %s',
        sep='x',
        desc=("Specify the shrink factor for the virtual domain (typically "
              "the fixed image) at each level.")
    )

    n_images = traits.Int(
        argstr="-n %d",
        desc=("This option sets the number of images to use to construct the "
              "template image.")
    )

    use_fixed_reference_image = traits.Bool(
        True,
        argstr="-u %d",
        desc=("use a fixed reference image instead of the neighor in the time "
              "series.")
    )

    use_scales_estimator = traits.Bool(
        True,
        argstr="-e %d",
        desc="use the scale estimator to control optimization."
    )

    use_estimate_learning_rate_once = traits.Bool(
        False,
        argstr="-l %d",
        desc=("turn on the option that lets you estimate the learning rate "
              "step size only at the beginning of each level. Useful as a "
              "second stage of fine-scale registration.")
    )

    write_displacement = traits.Bool(
        False,
        argstr="-w %d",
        desc="Write the low-dimensional 3D transforms to a 4D displacement field"
    )

    out_composite_transform = File(
        name_source=['output_transform_prefix'], name_template='%sMOCOparams.csv',
        output_name='composite_transform', desc='output file containing head-motion transforms')



class MotionCorrOutputSpec(TraitedSpec):
    '''Output spec for the antsMotionCorr command'''
    average_image = File(exists=True, desc="Average of an image")
    composite_transform = File(desc="Composite transform file")
    inverse_composite_transform = File(desc="Inverse composite transform file")
    warped_image = File(desc="Outputs warped image")
    inverse_warped_image = File(desc="Outputs the inverse of the warped image")
    save_state = File(desc="The saved registration state to be restored")
    displacement_field = File(desc=("4D displacement field that captures the "
                                    "affine induced motion at each voxel"))
    out_tfm = File(desc='write transforms in the Insight transform format')

class MotionCorr(ANTSCommand):
    '''
    Format and description of the affine motion correction parameters can be
    found in this PDF starting on page 555 section 3.9.16 AffineTransform:
    https://itk.org/ItkSoftwareGuide.pdf

    https://github.com/stnava/ANTs/blob/master/Scripts/antsMotionCorrExample

    Examples
    -------

    >>> from nipype.interfaces.ants.preprocess import MotionCorr
    >>> ants_mc = MotionCorr()
    >>> ants_mc.inputs.metric_type = 'GC'
    >>> ants_mc.inputs.metric_weight = 1
    >>> ants_mc.inputs.radius_or_bins = 1
    >>> ants_mc.inputs.sampling_strategy = "Random"
    >>> ants_mc.inputs.sampling_percentage = 0.05
    >>> ants_mc.inputs.iterations = [10,3]
    >>> ants_mc.inputs.smoothing_sigmas = [0,0]
    >>> ants_mc.inputs.shrink_factors = [1,1]
    >>> ants_mc.inputs.n_images = 10
    >>> ants_mc.inputs.use_fixed_reference_image = True
    >>> ants_mc.inputs.use_scales_estimator = True
    >>> ants_mc.inputs.output_average_image = 'wat'
    >>> ants_mc.inputs.output_warped_image = 'warped.nii.gz'
    >>> ants_mc.inputs.output_transform_prefix = 'motcorr'
    >>> ants_mc.inputs.transformation_model = 'Affine'
    >>> ants_mc.inputs.gradient_step_length = 0.005
    >>> ants_mc.inputs.fixed_image = "average_image.nii.gz"
    >>> ants_mc.inputs.moving_image = "input.nii.gz"
    >>> ants_mc.cmdline  # doctest: +ALLOW_UNICODE
    'antsMotionCorr -d 3 -i 10x3 -m GC[average_image.nii.gz,input.nii.gz,1.0,1,Random,0.05] -n\
 10 -o [motcorr,warped.nii.gz,average_image.nii.gz] -f 1x1 -s 0.0x0.0 -t Affine[0.005] -u 1 -e 1'

    >>> from nipype.interfaces.ants.preprocess import MotionCorr
    >>> ants_avg = MotionCorr()
    >>> ants_avg.inputs.average_image = 'input.nii.gz'
    >>> ants_avg.inputs.output_average_image = 'avg_out.nii.gz'
    >>> ants_mc.cmdline  # doctest: +ALLOW_UNICODE
    'antsMotionCorr -d 3 -a input.nii.gz -o avg_out.nii.gz'

    >>> ants_avg = MotionCorr()
    >>> ants_avg.inputs.average_image = 'input.nii.gz'
    >>> ants_mc.cmdline  # doctest: +ALLOW_UNICODE
    'antsMotionCorr -d 3 -a input.nii.gz -o input_avg.nii.gz'

    '''
    _cmd = 'antsMotionCorr'
    input_spec = MotionCorrInputSpec
    output_spec = MotionCorrOutputSpec

    def _gen_filename(self, name):
        '''
        If a fixed image is specified we are not going to be outputting
        a newly created averaged image. The output flag for calls to
        antsMotionCorr with a fixed image have a value set for an average
        image. In all of the examples this value always matches the fixed
        image name.
        '''
        if name == 'output_average_image':
            if isdefined(self.inputs.fixed_image):
                return self.inputs.fixed_image
            if not isdefined(self.inputs.average_image):
                raise ValueError("Either fixed_image or average_image must be defined")
            if isdefined(self.inputs.output_average_image):
                return self.inputs.output_average_image
            pth, fname, ext = split_filename(self.inputs.average_image)
            new_fname = '{}{}{}'.format(fname, '_avg', ext)
            return os.path.join(pth, new_fname)
        if name == 'ouput_warped_image' and isdefined(self.inputs.fixed_image):
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
        return super(MotionCorr, self)._format_arg(opt, spec, val)

    def _format_metric(self):
        metric_str = ("-m {metric_type}[{fixed_image},{moving_image},"
                      "{metric_weight},{radius_or_bins},{sampling_strategy},"
                      "{sampling_percentage}]")
        format_args = {}
        metric_args = ["metric_type", "fixed_image", "moving_image",
                       "metric_weight", "radius_or_bins", "sampling_strategy",
                       "sampling_percentage"]
        for metric_arg in metric_args:
            if isdefined(getattr(self.inputs, metric_arg)):
                format_args[metric_arg] = getattr(self.inputs, metric_arg)
        return metric_str.format(**format_args)

    def _format_transform(self):
        transform_str = "-t {}[{}]"
        if (isdefined(self.inputs.transformation_model)
                and isdefined(self.inputs.gradient_step_length)):
            return transform_str.format(self.inputs.transformation_model,
                                        self.inputs.gradient_step_length)
        raise ValueError("Unable to format transformation_model argument")

    def _format_output(self):
        if (isdefined(self.inputs.output_transform_prefix)
                and isdefined(self.inputs.output_warped_image)
                and isdefined(self.inputs.output_average_image)):
            return "-o [{},{},{}]".format(
                self.inputs.output_transform_prefix,
                self.inputs.output_warped_image,
                self.inputs.output_average_image
            )
        elif isdefined(self.inputs.output_average_image):
            return "-o {}".format(self.inputs.output_average_image)
        else:
            raise ValueError("Unable to format output due to lack of inputs.")

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.output_average_image):
            outputs['average_image'] = (
                os.path.abspath(self.inputs.output_average_image)
            )
        if isdefined(self.inputs.output_warped_image):
            outputs['warped_image'] = (
                os.path.abspath(self.inputs.output_warped_image)
            )
        if (isdefined(self.inputs.write_displacement) and
                isdefined(self.inputs.output_transform_prefix) and
                self.inputs.write_displacement is True):
            fname = '{}Warp.nii.gz'.format(self.inputs.output_transform_prefix)
            outputs['displacement_field'] = os.path.abspath(fname)
        return outputs


class MotionCorr2FSLParamsInputSpec(BaseInterfaceInputSpec):
    ants_moco = File(
        exists=True,
        desc='Motion correction matrices to be converted into FSL style motion parameters',
        mandatory=True
    )

class MotionCorr2FSLParamsOutputSpec(TraitedSpec):
    fsl_params = File(exists=True, desc="FSL parameters file to be output")


class MotionCorr2FSLParams(BaseInterface):
    '''
    Take antsMotionCorr motion output as input, convert to FSL-style
    parameter files. Currently does not output origin of rotation.
    '''
    input_spec = MotionCorr2FSLParamsInputSpec
    output_spec = MotionCorr2FSLParamsOutputSpec

    def __init__(self, **inputs):
        self._results = {}
        super(MotionCorr2FSLParams, self).__init__(**inputs)

    def _list_outputs(self):
        return self._results

    def _run_interface(self, runtime):
        # Ants motion correction output has a single line header that we ignore
        in_data = np.loadtxt(self.inputs.ants_moco,
                             delimiter=',', skiprows=1, dtype=np.float32)[:, 2:]
        pars = []
        for row in in_data:
            mat = row[:9].reshape(3, 3)
            param_z, param_y, param_x = mat2euler(mat)
            pars.append([param_x, param_y, param_z] + row[9:].tolist())

        _, fname, _ = split_filename(self.inputs.ants_moco)
        self._results['fsl_params'] = os.path.abspath('{}_fsl{}'.format(fname, '.par'))
        np.savetxt(self._results['fsl_params'], pars, delimiter=' ')

        return runtime

def moco2itk(in_csv, in_reference, out_file=None):
    """
    Generates an Insight Transform File V1.0 from the motion correction
    CSV file.

    Would be replaced if finally `this issue <https://github.com/stnava/ANTs/issues/419>`_
    is fixed.

    """
    from scipy.ndimage.measurements import center_of_mass

    movpar = np.loadtxt(in_csv, dtype=float, skiprows=1,
                        delimiter=',')[2:]

    nii = nb.load(in_reference)

    # Convert first to RAS, then to LPS
    cmfixed = np.diag([-1, -1, 1, 1]).dot(nii.affine).dot(
        list(center_of_mass(nii.get_data())) + [1])

    tf_type = ('AffineTransform_double_3_3' if movpar.shape[1] == 12
               else 'Euler3DTransform_double_3_3')

    xfm_file = [ITK_TFM_HEADER]
    for i, param in enumerate(movpar):
        xfm_file.append(ITK_TFM_TPL(
            tf_id=i, tf_type=tf_type,
            tf_params=' '.join(['%.8f' % p for p in param]),
            fixed_params=' '.join(['%.8f' % p for p in cmfixed[:3]])
        ))
    xfm_file += ['']

    if out_file is None:
        _, fname, _ = split_filename(in_reference)
        out_file = os.path.abspath('{}_ants.tfm'.format(fname))

    with open(out_file, 'w') as outfh:
        outfh.write("\n".join(xfm_file))

    return out_file
