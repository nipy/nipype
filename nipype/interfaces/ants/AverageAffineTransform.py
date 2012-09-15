"""
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)

"""
# Standard library imports
import os

# Local imports
from ..base import TraitedSpec, File, traits, InputMultiPath
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
    >>> from nipype.interfaces.ants.AverageAffineTransform import AverageAffineTransform
    >>> avg = AverageAffineTransform()
    >>> avg.inputs.dimension = 3
    >>> avg.inputs.transforms = ['trans.mat', 'func_to_struct.mat']
    >>> avg.inputs.output_affine_transform = 'MYtemplatewarp.mat'
    >>> avg.cmdline
    'AverageAffineTransform 3 MYtemplatewarp.mat trans.mat func_to_struct.mat'
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
