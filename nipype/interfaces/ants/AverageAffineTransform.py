# Standard library imports
import os

# Local imports
from ..base import (TraitedSpec, File, traits, InputMultiPath, OutputMultiPath, isdefined)
from ...utils.filemanip import split_filename
from .base import ANTSCommand, ANTSCommandInputSpec

class AverageAffineTransformInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='%d', usedefault=False, mandatory=True, position=0, desc='image dimension (2 or 3)')
    output_affine_transform = File(argstr='%s', mandatory=True, position=1, desc='Outputfname.txt: the name of the resulting transform.')
    transforms = InputMultiPath(File(exists=True), argstr='%s', mandatory=True, position=3, desc=('transforms to average') )

class AverageAffineTransformOutputSpec(TraitedSpec):
    affine_transform = File(exists=True, desc='average transform file')

class AverageAffineTransform(ANTSCommand):
    """
    Examples
    --------
    >>>
    """
    _cmd = 'AverageAffineTransform'
    input_spec = AverageAffineTransformInputSpec
    output_spec = AverageAffineTransformOutputSpec

    def _format_arg(self, opt, spec, val):
        return super(AverageAffineTransform, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['affine_transform'] = os.path.abspath(self.inputs.output_affine_transform)
        return outputs

"""
Usage:

AverageAffineTransform ImageDimension output_affine_transform [-R reference_affine_transform] {[-i] affine_transform_txt [weight(=1)] ]}

Compute weighted average of input affine transforms.
For 2D and 3D transform, the affine transform is first decomposed into scale x shearing
x rotation. Then these parameters are averaged, using the weights if they provided. For
3D transform, the rotation component is the quaternion. After averaging, the quaternion
will also be normalized to have unit norm. For 2D transform, the rotation component is
the rotation angle. The weight for each transform is a non-negative number. The sum of
all weights will be normalized to 1 before averaging. The default value for each weight
is 1.0.

All affine transforms is a "centerd" transform, following ITK convention. A
reference_affine_transform defines the center for the output transform. The first provided
transform is the default reference transform

Output affine transform is a MatrixOffsetBaseTransform.

 -i option takes the inverse of the affine mapping.

 For example:

 2 output_affine.txt -R A.txt A1.txt 1.0 -i A2.txt 2.0 A3.txt A4.txt 6.0 A5.txt

This computes: (1*A1 + 2*(A2)^-1 + A3 + A4*6 + A5 ) / (1+2+1+6+5)
"""
