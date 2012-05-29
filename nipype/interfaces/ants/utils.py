# Local imports
from ..base import (TraitedSpec, File, traits, InputMultiPath,
                    isdefined)
from ...utils.filemanip import split_filename
from .base import ANTSCommand, ANTSCommandInputSpec
import os


class ApplyTransformsInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='--dimensionality %d', usedefault=True,
                            desc='image dimension (2 or 3)')
    input_image = File(argstr='--input %s', mandatory=True,
                        desc=('image to apply transformation to (generally a '
                              'coregistered functional)'))
    output_image = traits.Str(argstr='--output %s',
                             desc=('output file name'), genfile=True,
                             hash_file=False)
    reference_image = File(argstr='--reference-image %s',
                       desc='reference image space that you wish to warp INTO')
    interpolation = traits.Str(argstr='--interpolation %s',
                              desc='Use nearest neighbor interpolation')
    transformation_files = InputMultiPath(File(exists=True), argstr='%s',
                             desc='transformation file(s) to be applied',
                             mandatory=True)
    invert_transforms = traits.List(traits.Int,
                    desc=('List of Affine transformations to invert. '
                          'E.g.: [1,4,5] inverts the 1st, 4th, and 5th Affines '
                          'found in transformation_series'))
    default_value = traits.Float(argstr="--default-value %g", desc="Default " +
    "voxel value to be used with input images only. Specifies the voxel value " +
          "when the input point maps outside the output domain")


class ApplyTransformsOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc='Warped image')


class ApplyTransforms(ANTSCommand):
    """antsApplyTransforms, applied to an input image, transforms it according to a
    reference image and a transform (or a set of transforms).

    Examples
    --------

    >>> from nipype.interfaces.ants import ApplyTransforms
    >>> atms = ApplyTransforms()
    >>> atms.inputs.input_image = 'structural.nii'
    >>> atms.inputs.reference_image = 'ants_deformed.nii.gz'
    >>> atms.inputs.transformation_files = ['ants_Warp.nii.gz','ants_Affine.txt']
    >>> atms.cmdline
    'antsApplyTransforms --dimensionality 3 --input structural.nii --output structural_trans.nii --reference-image ants_deformed.nii.gz --transform ants_Warp.nii.gz --transform ants_Affine.txt'

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

    def _format_arg(self, opt, spec, val):
        if opt == 'transformation_files':
            series = []
            tmpl = "--transform "
            for i, transformation_file in enumerate(val):
                tmpl
                if isdefined(self.inputs.invert_transforms) and i + 1 in self.inputs.invert_transforms:
                    series.append(tmpl + "[%s,1]" % transformation_file)
                else:
                    series.append(tmpl + "%s" % transformation_file)
            return ' '.join(series)
        return super(ApplyTransforms, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output_image'] = os.path.abspath(self._gen_filename('output_image'))
        return outputs


class WarpImageMultiTransformInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='%d', usedefault=True,
                            desc='image dimension (2 or 3)', position=1)
    moving_image = File(argstr='%s', mandatory=True, copyfile=True,
                        desc=('image to apply transformation to (generally a '
                              'coregistered functional)'))
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
    transformation_series = InputMultiPath(File(exists=True), argstr='%s',
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
    >>> wimt.inputs.moving_image = 'structural.nii'
    >>> wimt.inputs.reference_image = 'ants_deformed.nii.gz'
    >>> wimt.inputs.transformation_series = ['ants_Warp.nii.gz','ants_Affine.txt']
    >>> wimt.cmdline
    'WarpImageMultiTransform 3 structural.nii structural_wimt.nii -R ants_deformed.nii.gz ants_Warp.nii.gz ants_Affine.txt'


    >>> from nipype.interfaces.ants import WarpImageMultiTransform
    >>> wimt = WarpImageMultiTransform()
    >>> wimt.inputs.moving_image = 'diffusion_weighted.nii'
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
            _, name, ext = split_filename(os.path.abspath(self.inputs.moving_image))
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
        _, name, ext = split_filename(os.path.abspath(self.inputs.moving_image))
        outputs['output_image'] = os.path.join(os.getcwd(),
                                             ''.join((name,
                                                      self.inputs.out_postfix,
                                                      ext)))
        return outputs


class WarpTimeSeriesImageMultiTransformInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(4, 3, argstr='%d', usedefault=True,
                            desc='image dimension (3 or 4)', position=1)
    moving_image = File(argstr='%s', mandatory=True, copyfile=True,
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
    >>> wtsimt.inputs.moving_image = 'resting.nii'
    >>> wtsimt.inputs.reference_image = 'ants_deformed.nii.gz'
    >>> wtsimt.inputs.transformation_series = ['ants_Warp.nii.gz','ants_Affine.txt']
    >>> wtsimt.cmdline
    'WarpTimeSeriesImageMultiTransform 4 resting.nii resting_wtsimt.nii -R ants_deformed.nii.gz ants_Warp.nii.gz ants_Affine.txt'

    >>> from nipype.interfaces.ants import WarpTimeSeriesImageMultiTransform
    >>> wtsimt = WarpTimeSeriesImageMultiTransform()
    >>> wtsimt.inputs.moving_image = 'resting.nii'
    >>> wtsimt.inputs.reference_image = 'diffusion_weighted.nii'
    >>> wtsimt.inputs.transformation_series = ['dwi2anat_coreg_Affine.txt','dwi2anat_InverseWarp.nii.gz','resting2anat_Warp.nii.gz','resting2anat_coreg_Affine.txt']
    >>> wtsimt.inputs.invert_affine = [1]
    >>> wtsimt.cmdline
    'WarpTimeSeriesImageMultiTransform 4 resting.nii resting_wtsimt.nii -R diffusion_weighted.nii -i dwi2anat_coreg_Affine.txt dwi2anat_InverseWarp.nii.gz resting2anat_Warp.nii.gz resting2anat_coreg_Affine.txt'
    """

    _cmd = 'WarpTimeSeriesImageMultiTransform'
    input_spec = WarpTimeSeriesImageMultiTransformInputSpec
    output_spec = WarpTimeSeriesImageMultiTransformOutputSpec

    def _format_arg(self, opt, spec, val):
        if opt == 'out_postfix':
            _, name, ext = split_filename(os.path.abspath(self.inputs.moving_image))
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
        return super(WarpTimeSeriesImageMultiTransform, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        _, name, ext = split_filename(os.path.abspath(self.inputs.moving_image))
        outputs['output_image'] = os.path.join(os.getcwd(),
                                             ''.join((name,
                                                      self.inputs.out_postfix,
                                                      ext)))
        return outputs
