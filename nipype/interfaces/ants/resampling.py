"""ANTS Apply Transforms interface

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)
"""

from builtins import range
import os

from .base import ANTSCommand, ANTSCommandInputSpec
from ..base import TraitedSpec, File, traits, isdefined, InputMultiPath
from ...utils.filemanip import split_filename


class WarpTimeSeriesImageMultiTransformInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(4, 3, argstr='%d', usedefault=True,
                            desc='image dimension (3 or 4)', position=1)
    input_image = File(
        argstr='%s', mandatory=True, copyfile=True,
        desc='image to apply transformation to (generally a coregistered functional)')
    output_image = File(name_source='input_image', name_template='%s_wtsimt', argstr='%s',
                        keep_extension=True, desc='filename of output warped image')
    out_postfix = traits.Str(
        '_wtsimt', argstr='%s', deprecated=True, new_name='output_image',
        desc='Postfix that is prepended to all output files (default = _wtsimt)')
    reference_image = File(argstr='-R %s', xor=['tightest_box'],
                           desc='reference image space that you wish to warp INTO')
    tightest_box = traits.Bool(argstr='--tightest-bounding-box',
                               desc=('computes tightest bounding box (overrided by '
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

    def _format_arg(self, opt, spec, val):
        if opt == 'transformation_series':
            series = []
            affine_counter = 0
            for transformation in val:
                if 'Affine' in transformation and \
                        isdefined(self.invert_affine):
                    affine_counter += 1
                    if affine_counter in self.invert_affine:
                        series += ['-i'],
                series += [transformation]
            return ' '.join(series)
        return super(
            WarpTimeSeriesImageMultiTransformInputSpec, self)._format_arg(opt, spec, val)

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
    'WarpTimeSeriesImageMultiTransform 4 resting.nii resting_wtsimt.nii -R ants_deformed.nii.gz ants_Warp.nii.gz \
ants_Affine.txt'

    """

    _cmd = 'WarpTimeSeriesImageMultiTransform'
    _input_spec = WarpTimeSeriesImageMultiTransformInputSpec
    _output_spec = WarpTimeSeriesImageMultiTransformOutputSpec

    def _run_interface(self, runtime, correct_return_codes=[0]):
        runtime = super(WarpTimeSeriesImageMultiTransform, self)._run_interface(runtime, correct_return_codes=[0, 1])
        if "100 % complete" not in runtime.stdout:
            self.raise_exception(runtime)
        return runtime


class WarpImageMultiTransformInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='%d', usedefault=True,
                            desc='image dimension (2 or 3)', position=1)
    input_image = File(argstr='%s', mandatory=True,
                       desc=('image to apply transformation to (generally a '
                              'coregistered functional)'), position=2)
    output_image = File(name_source='input_image', name_template='%s_wimt', argstr='%s',
                        keep_extension=True, desc='filename of output warped image')
    out_postfix = File(
        "_wimt", usedefault=True, hash_files=False, deprecated=True, new_name='output_image',
        desc=('Postfix that is prepended to all output files (default = _wimt)'),
        xor=['output_image'])
    reference_image = File(argstr='-R %s', xor=['tightest_box'],
                           desc='reference image space that you wish to warp INTO')
    tightest_box = traits.Bool(argstr='--tightest-bounding-box',
                               desc=('computes tightest bounding box (overrided by '
                                     'reference_image if given)'),
                               xor=['reference_image'])
    reslice_by_header = traits.Bool(argstr='--reslice-by-header',
                                    desc=('Uses orientation matrix and origin encoded in '
                                          'reference image file header. Not typically used '
                                          'with additional transforms'))
    use_nearest = traits.Bool(argstr='--use-NN',
                              desc='Use nearest neighbor interpolation')
    use_bspline = traits.Bool(argstr='--use-BSpline',
                              desc='Use 3rd order B-Spline interpolation')
    transformation_series = InputMultiPath(File(exists=True), argstr='%s',
                                           desc='transformation file(s) to be applied',
                                           mandatory=True, position=-1)
    invert_affine = traits.List(traits.Int,
                                desc=('List of Affine transformations to invert.'
                                      'E.g.: [1,4,5] inverts the 1st, 4th, and 5th Affines '
                                      'found in transformation_series. Note that indexing '
                                      'starts with 1 and does not include warp fields. Affine '
                                      'transformations are distinguished '
                                      'from warp fields by the word "affine" included in their filenames.'))

    def _format_arg(self, opt, spec, val):
        if opt == 'transformation_series':
            series = []
            affine_counter = 0
            for transformation in val:
                if "affine" in transformation.lower() and \
                        isdefined(self.invert_affine):
                    affine_counter += 1
                    if affine_counter in self.invert_affine:
                        series += '-i',
                series += [transformation]
            return ' '.join(series)
        return super(WarpImageMultiTransformInputSpec, self)._format_arg(opt, spec, val)


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
    'WarpImageMultiTransform 3 structural.nii structural_wimt.nii -R ants_deformed.nii.gz ants_Warp.nii.gz \
ants_Affine.txt'

    >>> wimt = WarpImageMultiTransform()
    >>> wimt.inputs.input_image = 'diffusion_weighted.nii'
    >>> wimt.inputs.reference_image = 'functional.nii'
    >>> wimt.inputs.transformation_series = ['func2anat_coreg_Affine.txt','func2anat_InverseWarp.nii.gz', \
    'dwi2anat_Warp.nii.gz','dwi2anat_coreg_Affine.txt']
    >>> wimt.inputs.invert_affine = [1]
    >>> wimt.cmdline
    'WarpImageMultiTransform 3 diffusion_weighted.nii diffusion_weighted_wimt.nii -R functional.nii \
-i func2anat_coreg_Affine.txt func2anat_InverseWarp.nii.gz dwi2anat_Warp.nii.gz dwi2anat_coreg_Affine.txt'

    """

    _cmd = 'WarpImageMultiTransform'
    _input_spec = WarpImageMultiTransformInputSpec
    _output_spec = WarpImageMultiTransformOutputSpec


class ApplyTransformsInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(2, 3, 4, argstr='--dimensionality %d',
                            desc=('This option forces the image to be treated '
                                  'as a specified-dimensional image. If not '
                                  'specified, antsWarp tries to infer the '
                                  'dimensionality from the input image.'))
    input_image_type = traits.Enum(0, 1, 2, 3,
                                   argstr='--input-image-type %d',
                                   desc=('Option specifying the input image '
                                         'type of scalar (default), vector, '
                                         'tensor, or time series.'))
    input_image = File(argstr='--input %s', mandatory=True,
                       desc=('image to apply transformation to (generally a '
                              'coregistered functional)'),
                       exists=True)
    output_image = File(name_source='input_image', name_template='%s_warped', keep_extension=True,
                        argstr='--output %s', desc='output file name', hash_files=False)
    out_postfix = traits.Str("_trans", usedefault=True,
                             desc=('Postfix that is appended to all output '
                                   'files (default = _trans)'))
    reference_image = File(argstr='--reference-image %s', mandatory=True,
                           desc='reference image space that you wish to warp INTO',
                           exists=True)
    interpolation = traits.Enum('Linear',
                                'NearestNeighbor',
                                'CosineWindowedSinc',
                                'WelchWindowedSinc',
                                'HammingWindowedSinc',
                                'LanczosWindowedSinc',
                                'MultiLabel',
                                'Gaussian',
                                'BSpline',
                                argstr='%s', usedefault=True)
    interpolation_parameters = traits.Either(traits.Tuple(traits.Int()),  # BSpline (order)
                                             traits.Tuple(traits.Float(),  # Gaussian/MultiLabel (sigma, alpha)
                                                          traits.Float())
                                             )
    transforms = InputMultiPath(
        File(exists=True), argstr='%s', mandatory=True, desc='transform files: will be applied in reverse order. For example, the last specified transform will be applied first')
    invert_transform_flags = InputMultiPath(traits.Bool())
    default_value = traits.Float(0.0, argstr='--default-value %g', usedefault=True)
    print_out_composite_warp_file = traits.Bool(
        False, usedefault=True, desc='output a composite warp file instead of a transformed image')
    float = traits.Bool(argstr='--float %d', default=False, desc='Use float instead of double for computations.')

    def _get_transform_filenames(self):
        retval = []
        for ii in range(len(self.transforms)):
            if isdefined(self.invert_transform_flags):
                if len(self.transforms) == len(self.invert_transform_flags):
                    invert_code = 1 if self.invert_transform_flags[
                        ii] else 0
                    retval.append("--transform [ %s, %d ]" %
                                  (self.transforms[ii], invert_code))
                else:
                    raise Exception(("ERROR: The useInverse list must have the same number "
                                     "of entries as the transformsFileName list."))
            else:
                retval.append("--transform %s" % self.transforms[ii])
        return " ".join(retval)

    def _format_arg(self, opt, spec, val):
        retval = super(ApplyTransformsInputSpec, self)._format_arg(opt, spec, val)

        if opt == "output_image":
            if self.print_out_composite_warp_file:
                modval = super(ApplyTransformsInputSpec,
                               self)._format_arg('print_out_composite_warp_file')
                return '--output [ ' + retval[6:] + ', ' + modval + ' ]'
        elif opt == "transforms":
            return self._get_transform_filenames()
        elif opt == 'interpolation':
            if self.interpolation in ['BSpline', 'MultiLabel', 'Gaussian'] and \
                    isdefined(self.interpolation_parameters):
                return '--interpolation %s[ %s ]' % (self.interpolation,
                                                     ', '.join([str(param)
                                                                for param in self.interpolation_parameters]))
            else:
                return '--interpolation %s' % self.interpolation
        return retval


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
    >>> at.inputs.transforms = ['ants_Warp.nii.gz', 'trans.mat']
    >>> at.inputs.invert_transform_flags = [False, False]
    >>> at.cmdline
    'antsApplyTransforms --default-value 0 --dimensionality 3 --input moving1.nii --interpolation Linear \
--output deformed_moving1.nii --reference-image fixed1.nii --transform [ ants_Warp.nii.gz, 0 ] \
--transform [ trans.mat, 0 ]'

    >>> at1 = ApplyTransforms()
    >>> at1.inputs.dimension = 3
    >>> at1.inputs.input_image = 'moving1.nii'
    >>> at1.inputs.reference_image = 'fixed1.nii'
    >>> at1.inputs.output_image = 'deformed_moving1.nii'
    >>> at1.inputs.interpolation = 'BSpline'
    >>> at1.inputs.interpolation_parameters = (5,)
    >>> at1.inputs.default_value = 0
    >>> at1.inputs.transforms = ['ants_Warp.nii.gz', 'trans.mat']
    >>> at1.inputs.invert_transform_flags = [False, False]
    >>> at1.cmdline
    'antsApplyTransforms --default-value 0 --dimensionality 3 --input moving1.nii --interpolation BSpline[ 5 ] \
--output deformed_moving1.nii --reference-image fixed1.nii --transform [ ants_Warp.nii.gz, 0 ] \
--transform [ trans.mat, 0 ]'


    """
    _cmd = 'antsApplyTransforms'
    _input_spec = ApplyTransformsInputSpec
    _output_spec = ApplyTransformsOutputSpec


class ApplyTransformsToPointsInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(2, 3, 4, argstr='--dimensionality %d',
                            desc=('This option forces the image to be treated '
                                  'as a specified-dimensional image. If not '
                                  'specified, antsWarp tries to infer the '
                                  'dimensionality from the input image.'))
    input_file = File(argstr='--input %s', mandatory=True,
                      desc=("Currently, the only input supported is a csv file with "
                            "columns including x,y (2D), x,y,z (3D) or x,y,z,t,label (4D) column headers."
                            "The points should be defined in physical space."
                            "If in doubt how to convert coordinates from your files to the space"
                            "required by antsApplyTransformsToPoints try creating/drawing a simple"
                            "label volume with only one voxel set to 1 and all others set to 0."
                            "Write down the voxel coordinates. Then use ImageMaths LabelStats to find"
                            "out what coordinates for this voxel antsApplyTransformsToPoints is"
                            "expecting."),
                      exists=True)
    output_file = traits.Str(argstr='--output %s',
                             desc='Name of the output CSV file', name_source=['input_file'],
                             hash_files=False, name_template='%s_transformed.csv')
    transforms = traits.List(File(exists=True), argstr='%s', mandatory=True,
                             desc='transforms that will be applied to the points')
    invert_transform_flags = traits.List(traits.Bool(),
                                         desc='list indicating if a transform should be reversed')

    def _get_transform_filenames(self):
        retval = []
        for ii in range(len(self.transforms)):
            if isdefined(self.invert_transform_flags):
                if len(self.transforms) == len(self.invert_transform_flags):
                    invert_code = 1 if self.invert_transform_flags[
                        ii] else 0
                    retval.append("--transform [ %s, %d ]" %
                                  (self.transforms[ii], invert_code))
                else:
                    raise Exception(("ERROR: The useInverse list must have the same number "
                                     "of entries as the transformsFileName list."))
            else:
                retval.append("--transform %s" % self.transforms[ii])
        return " ".join(retval)

    def _format_arg(self, opt, spec, val):
        if opt == "transforms":
            return self._get_transform_filenames()
        return super(ApplyTransformsToPointsInputSpec, self)._format_arg(opt, spec, val)


class ApplyTransformsToPointsOutputSpec(TraitedSpec):
    output_file = File(exists=True, desc='csv file with transformed coordinates')


class ApplyTransformsToPoints(ANTSCommand):
    """ApplyTransformsToPoints, applied to an CSV file, transforms coordinates
    using provided transform (or a set of transforms).

    Examples
    --------

    >>> from nipype.interfaces.ants import ApplyTransforms
    >>> at = ApplyTransformsToPoints()
    >>> at.inputs.dimension = 3
    >>> at.inputs.input_file = 'moving.csv'
    >>> at.inputs.transforms = ['trans.mat', 'ants_Warp.nii.gz']
    >>> at.inputs.invert_transform_flags = [False, False]
    >>> at.cmdline
    'antsApplyTransformsToPoints --dimensionality 3 --input moving.csv --output moving_transformed.csv \
--transform [ trans.mat, 0 ] --transform [ ants_Warp.nii.gz, 0 ]'


    """
    _cmd = 'antsApplyTransformsToPoints'
    _input_spec = ApplyTransformsToPointsInputSpec
    _output_spec = ApplyTransformsToPointsOutputSpec
