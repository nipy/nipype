## NOTE:  This implementation has been superceeded buy the antsApplyTransform
##        implmeentation that more closely follows the strucutre and capabilities
##        of the antsApplyTransform program.  This implementation is here
##        for backwards compatibility.

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
