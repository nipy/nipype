# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft = python sts = 4 ts = 4 sw = 4 et:
"""ANTS Apply Transforms interface

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)
"""
import os

from .base import ANTSCommand, ANTSCommandInputSpec
from ..base import (TraitedSpec, File, traits,
                    isdefined)
from ...utils.filemanip import split_filename
from nipype.interfaces.base import InputMultiPath


class WarpTimeSeriesImageMultiTransformInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(4, 3, argstr='%d', usedefault=True,
                            desc='image dimension (3 or 4)', position=1)
    input_image = File(argstr='%s', mandatory=True, copyfile=True,
                        desc=('image to apply transformation to (generally a '
                              'coregistered functional)'))
    out_postfix = traits.Str('_wtsimt', argstr='%s', usedefault=True,
                             desc=('Postfix that is prepended to all output '
                                   'files (default = _wtsimt)'))
    reference_image = File(argstr='-R %s', xor=['tightest_box'],
                       desc='reference image space that you wish to warp INTO')
    tightest_box = traits.Bool(argstr='--tightest-bounding-box',
                          desc=('computes tightest bounding box (overrided by '  \
                                'reference_image if given)'),
                          xor=['reference_image'])
    reslice_by_header = traits.Bool(argstr='--reslice-by-header',
                     desc=('Uses orientation matrix and origin encoded in '
                           'reference image file header. Not typically used '
                           'with additional transforms'))
    use_nearest = traits.Bool(argstr='--use-NN',
                              desc='Use nearest neighbor interpolation')
    use_bspline = traits.Bool(argstr='--use-Bspline',
                              desc='Use 3rd order B-Spline interpolation')
    transformation_series = InputMultiPath(File(exists=True), argstr='%s',
                             desc='transformation file(s) to be applied',
                             mandatory=True, copyfile=False)
    invert_affine = traits.List(traits.Int,
                    desc=('List of Affine transformations to invert. '
                          'E.g.: [1,4,5] inverts the 1st, 4th, and 5th Affines '
                          'found in transformation_series'))


class WarpTimeSeriesImageMultiTransformOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc='Warped image')


class WarpTimeSeriesImageMultiTransform(ANTSCommand):
    """Warps a time-series from one space to another

    Examples
    --------

    >>> from nipype.interfaces.ants import WarpTimeSeriesImageMultiTransform
    >>> wtsimt = WarpTimeSeriesImageMultiTransform()
    >>> wtsimt.inputs.input_image = 'resting.nii'
    >>> wtsimt.inputs.reference_image = 'ants_deformed.nii.gz'
    >>> wtsimt.inputs.transformation_series = ['ants_Warp.nii.gz','ants_Affine.txt']
    >>> wtsimt.cmdline
    'WarpTimeSeriesImageMultiTransform 4 resting.nii resting_wtsimt.nii -R ants_deformed.nii.gz ants_Warp.nii.gz ants_Affine.txt'

    """

    _cmd = 'WarpTimeSeriesImageMultiTransform'
    input_spec = WarpTimeSeriesImageMultiTransformInputSpec
    output_spec = WarpTimeSeriesImageMultiTransformOutputSpec

    def _format_arg(self, opt, spec, val):
        if opt == 'out_postfix':
            _, name, ext = split_filename(os.path.abspath(self.inputs.input_image))
            return name + val + ext
        if opt == 'transformation_series':
            series = []
            affine_counter = 0
            for transformation in val:
                if 'Affine' in transformation and \
                    isdefined(self.inputs.invert_affine):
                    affine_counter += 1
                    if affine_counter in self.inputs.invert_affine:
                        series += ['-i'],
                series += [transformation]
            return ' '.join(series)
        return super(WarpTimeSeriesImageMultiTransform, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        _, name, ext = split_filename(os.path.abspath(self.inputs.input_image))
        outputs['output_image'] = os.path.join(os.getcwd(),
                                             ''.join((name,
                                                      self.inputs.out_postfix,
                                                      ext)))
        return outputs


class WarpImageMultiTransformInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='%d', usedefault=True,
                            desc='image dimension (2 or 3)', position=1)
    input_image = File(argstr='%s', mandatory=True, copyfile=True,
                        desc=('image to apply transformation to (generally a '
                              'coregistered functional)') )
    out_postfix = traits.Str('_wimt', argstr='%s', usedefault=True,
                             desc=('Postfix that is prepended to all output '
                                   'files (default = _wimt)'))
    reference_image = File(argstr='-R %s', xor=['tightest_box'],
                       desc='reference image space that you wish to warp INTO')
    tightest_box = traits.Bool(argstr='--tightest-bounding-box',
                          desc=('computes tightest bounding box (overrided by '  \
                                'reference_image if given)'),
                          xor=['reference_image'])
    reslice_by_header = traits.Bool(argstr='--reslice-by-header',
                     desc=('Uses orientation matrix and origin encoded in '
                           'reference image file header. Not typically used '
                           'with additional transforms'))
    use_nearest = traits.Bool(argstr='--use-NN',
                              desc='Use nearest neighbor interpolation')
    use_bspline = traits.Bool(argstr='--use-Bspline',
                              desc='Use 3rd order B-Spline interpolation')
    transformation_series = InputMultiPath(File(exists=True, copyfile=False), argstr='%s',
                             desc='transformation file(s) to be applied',
                             mandatory=True, copyfile=False)
    invert_affine = traits.List(traits.Int,
                    desc=('List of Affine transformations to invert. '
                          'E.g.: [1,4,5] inverts the 1st, 4th, and 5th Affines '
                          'found in transformation_series'))

class WarpImageMultiTransformOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc='Warped image')

class WarpImageMultiTransform(ANTSCommand):
    """Warps an image from one space to another

    Examples
    --------

    >>> from nipype.interfaces.ants import WarpImageMultiTransform
    >>> wimt = WarpImageMultiTransform()
    >>> wimt.inputs.input_image = 'structural.nii'
    >>> wimt.inputs.reference_image = 'ants_deformed.nii.gz'
    >>> wimt.inputs.transformation_series = ['ants_Warp.nii.gz','ants_Affine.txt']
    >>> wimt.cmdline
    'WarpImageMultiTransform 3 structural.nii structural_wimt.nii -R ants_deformed.nii.gz ants_Warp.nii.gz ants_Affine.txt'

    >>> wimt = WarpImageMultiTransform()
    >>> wimt.inputs.input_image = 'diffusion_weighted.nii'
    >>> wimt.inputs.reference_image = 'functional.nii'
    >>> wimt.inputs.transformation_series = ['func2anat_coreg_Affine.txt','func2anat_InverseWarp.nii.gz','dwi2anat_Warp.nii.gz','dwi2anat_coreg_Affine.txt']
    >>> wimt.inputs.invert_affine = [1]
    >>> wimt.cmdline
    'WarpImageMultiTransform 3 diffusion_weighted.nii diffusion_weighted_wimt.nii -R functional.nii -i func2anat_coreg_Affine.txt func2anat_InverseWarp.nii.gz dwi2anat_Warp.nii.gz dwi2anat_coreg_Affine.txt'

    """

    _cmd = 'WarpImageMultiTransform'
    input_spec = WarpImageMultiTransformInputSpec
    output_spec = WarpImageMultiTransformOutputSpec

    def _format_arg(self, opt, spec, val):
        if opt == 'out_postfix':
            _, name, ext = split_filename(os.path.abspath(self.inputs.input_image))
            return name + val + ext
        if opt == 'transformation_series':
            series = []
            affine_counter = 0
            for transformation in val:
                if 'Affine' in transformation and \
                    isdefined(self.inputs.invert_affine):
                    affine_counter += 1
                    if affine_counter in self.inputs.invert_affine:
                        series += '-i',
                series += [transformation]
            return ' '.join(series)
        return super(WarpImageMultiTransform, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        _, name, ext = split_filename(os.path.abspath(self.inputs.input_image))
        outputs['output_image'] = os.path.join(os.getcwd(),
                                             ''.join((name,
                                                      self.inputs.out_postfix,
                                                      ext)))
        return outputs


class ApplyTransformsInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='--dimensionality %d', usedefault=True,
                            desc='image dimension (2 or 3)')
    input_image = File(argstr='--input %s', mandatory=True,
                        desc=('image to apply transformation to (generally a '
                              'coregistered functional)'),
        exists=True)
    output_image = traits.Str(argstr='--output %s',
                             desc=('output file name'), genfile=True,
                             hash_file=False)
    reference_image = File(argstr='--reference-image %s', mandatory=True,
                       desc='reference image space that you wish to warp INTO',
                       exists=True)
    interpolation = traits.Enum('Linear',
                                'NearestNeighbor',
                                'CosineWindowedSinc',
                                'WelchWindowedSinc',
                                'HammingWindowedSinc',
                                'LanczosWindowedSinc',
                                # 'MultiLabel',
                                # 'Gaussian',
                                # 'BSpline',
                                argstr='%s', usedefault = True)
    # TODO: Implement these options for multilabel, gaussian, and bspline
    # interpolation_sigma = traits.Float(requires=['interpolation'])
    # interpolation_alpha = traits.Float(requires=['interpolation_sigma'])
    # bspline_order = traits.Int(3, requires=['interpolation'])
    transforms = traits.List(File(exists=True), argstr='%s', mandatory=True, desc=(''))
    invert_transform_flags = traits.List(traits.Bool())
    default_value = traits.Float(0.0,argstr='--default-value %d', usedefault = True)
    print_out_composite_warp_file = traits.Enum(0, 1, requires=["output_image"], desc=('')) # TODO: Change to boolean

class ApplyTransformsOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc='Warped image')

class ApplyTransforms(ANTSCommand):
    """ApplyTransforms, applied to an input image, transforms it according to a
    reference image and a transform (or a set of transforms).

    Examples
    --------

    >>> from nipype.interfaces.ants import ApplyTransforms
    >>> at = ApplyTransforms()
    >>> at.inputs.dimension = 3
    >>> at.inputs.input_image = 'moving1.nii'
    >>> at.inputs.reference_image = 'fixed1.nii'
    >>> at.inputs.output_image = 'deformed_moving1.nii'
    >>> at.inputs.interpolation = 'Linear'
    >>> at.inputs.default_value = 0
    >>> at.inputs.transforms = ['trans.mat', 'ants_Warp.nii.gz']
    >>> at.inputs.invert_transform_flags = [False, False]
    >>> at.cmdline
    'antsApplyTransforms --default-value 0 --dimensionality 3 --input moving1.nii --interpolation Linear --output deformed_moving1.nii --reference-image fixed1.nii --transform [trans.mat,0] --transform [ants_Warp.nii.gz,0]'


    """
    _cmd = 'antsApplyTransforms'
    input_spec = ApplyTransformsInputSpec
    output_spec = ApplyTransformsOutputSpec

    def _gen_filename(self, name):
        if name == 'output_image':
            output = self.inputs.output_image
            if not isdefined(output):
                _, name, ext = split_filename(self.inputs.input_image)
                output = name + '_trans' + ext
            return output
        return None

    def _getTransformFileNames(self):
        retval = []
        for ii in range(len(self.inputs.transforms)):
            if isdefined(self.inputs.invert_transform_flags):
                if len(self.inputs.transforms) == len(self.inputs.invert_transform_flags):
                    invert_code=1 if self.inputs.invert_transform_flags[ii] else 0
                    retval.append("--transform [%s,%d]"%(self.inputs.transforms[ii], invert_code))
                else:
                    raise Exception("ERROR: The useInverse list must have the same number of entries as the transformsFileName list.")
            else:
                retval.append("--transform %s" % self.inputs.transforms[ii])
        return " ".join(retval)

    def _getOutputWarpedFileName(self):
        if isdefined(self.inputs.print_out_composite_warp_file):
            return "--output [%s,%s]"%(self._gen_filename("output_image"), self.inputs.print_out_composite_warp_file)
        else:
            return "--output %s"%(self._gen_filename("output_image"))

    def _format_arg(self, opt, spec, val):
        if opt == "output_image":
            return self._getOutputWarpedFileName()
        elif opt == "transforms":
            return self._getTransformFileNames()
        elif opt == 'interpolation':
            # TODO: handle multilabel, gaussian, and bspline options
            return '--interpolation %s' % self.inputs.interpolation
        return super(ApplyTransforms, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output_image'] = os.path.abspath(self._gen_filename('output_image'))
        return outputs
