import os

from .base import ANTSCommand, ANTSCommandInputSpec
from ..base import (TraitedSpec, File, traits,
                    InputMultiPath, OutputMultiPath, isdefined)
from ...utils.filemanip import split_filename

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
                        series += ['-i'],
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
