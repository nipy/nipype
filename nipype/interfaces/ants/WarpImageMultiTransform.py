"""The ants module provides basic functions for interfacing with ants functions.

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)

"""
# Standard library imports
import os

# Local imports
from .base import ANTSCommand, ANTSCommandInputSpec
from ..base import TraitedSpec, File, traits, InputMultiPath, isdefined
from ...utils.filemanip import split_filename


class WarpImageMultiTransformInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='%d', usedefault=True,
                            desc='image dimension (2 or 3)', position=1)
    moving_image = File(argstr='%s', mandatory=True, copyfile=True,
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

    >>> from nipype.interfaces.ants.WarpImageMultiTransform import WarpImageMultiTransform
    >>> wimt = WarpImageMultiTransform()
    >>> wimt.inputs.moving_image = 'structural.nii'
    >>> wimt.inputs.reference_image = 'ants_deformed.nii.gz'
    >>> wimt.inputs.transformation_series = ['ants_Warp.nii.gz','ants_Affine.txt']
    >>> wimt.cmdline
    'WarpImageMultiTransform 3 structural.nii structural_wimt.nii -R ants_deformed.nii.gz ants_Warp.nii.gz ants_Affine.txt'

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

"""
Usage:

WarpImageMultiTransform ImageDimension moving_image output_image  -R reference_image --use-NN   SeriesOfTransformations--(See Below)
 SeriesOfTransformations --- WarpImageMultiTransform can apply, via concatenation, an unlimited number of transformations to your data .
 Thus, SeriesOfTransformations may be  an Affine transform followed by a warp  another affine and then another warp.
  Inverse affine transformations are invoked by calling   -i MyAffine.txt
 InverseWarps are invoked by passing the InverseWarp.nii.gz  filename (see below for a note about this).

 Example 1: Mapping a warped image into the reference_image domain by applying abcdWarp.nii.gz and then abcdAffine.txt

WarpImageMultiTransform 3 moving_image output_image -R reference_image abcdWarp.nii.gz abcdAffine.txt

 Example 2: To map the fixed/reference_image warped into the moving_image domain by applying the inversion of abcdAffine.txt and then abcdInverseWarp.nii.gz .

WarpImageMultiTransform 3 reference_image output_image -R moving_image -i  abcdAffine.txt abcdInverseWarp.nii.gz


  Note that the inverse maps (Ex. 2) are passed to this program in the reverse order of the forward maps (Ex. 1).
 This makes sense, geometrically ... see ANTS.pdf for visualization of this syntax.

 Compulsory arguments:

 ImageDimension: 2 or 3 (for 2 or 3 Dimensional registration)

 moving_image: the image to apply the transformation to

 output_image: the resulting image


 Optional arguments:

 -R: reference_image space that you wish to warp INTO.
       --tightest-bounding-box: Computes the tightest bounding box using all the affine transformations. It will be overrided by -R reference_image if given.
       --reslice-by-header: equivalient to -i -mh, or -fh -i -mh if used together with -R. It uses the orientation matrix and origin encoded in the image file header.
       It can be used together with -R. This is typically not used together with any other transforms.

 --use-NN: Use Nearest Neighbor Interpolation.

 --use-BSpline: Use 3rd order B-Spline Interpolation.

 --use-ML sigma: Use anti-aliasing interpolation for multi-label images, with Gaussian smoothing with standard deviation sigma.

                 Sigma can be specified in physical or voxel units, as in Convert3D. It can be a scalar or a vector.

                 Examples:  --use-ML 0.4mm    -use-ML 0.8x0.8x0.8vox
 -i: will use the inversion of the following affine transform.



 Other Example Usages:
 Reslice the image: WarpImageMultiTransform 3 Imov.nii.gz Iout.nii.gz --tightest-bounding-box --reslice-by-header
 Reslice the image to a reference image: WarpImageMultiTransform 3 Imov.nii.gz Iout.nii.gz -R Iref.nii.gz --tightest-bounding-box --reslice-by-header

 Important Notes:
 Prefixname "abcd" without any extension will use ".nii.gz" by default
 The abcdWarp and abcdInverseWarp do not exist. They are formed on the basis of abcd(Inverse)Warp.nii.gz when calling WarpImageMultiTransform, yet you have to use them as if they exist.
"""
