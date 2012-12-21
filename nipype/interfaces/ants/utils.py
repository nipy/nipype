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


class AverageAffineTransformInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='%d', usedefault=False, mandatory=True, position=0, desc='image dimension (2 or 3)')
    output_affine_transform = File(argstr='%s', mandatory=True, position=1, desc='Outputfname.txt: the name of the resulting transform.')
    transforms = InputMultiPath(File(exists=True), argstr='%s', mandatory=True,
                                position=3, desc=('transforms to average'))


class AverageAffineTransformOutputSpec(TraitedSpec):
    affine_transform = File(exists=True, desc='average transform file')


class AverageAffineTransform(ANTSCommand):
    """
    Examples
    --------
    >>> from nipype.interfaces.ants import AverageAffineTransform
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
        outputs['affine_transform'] = os.path.abspath(
            self.inputs.output_affine_transform)
        return outputs


class AverageImagesInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='%d', mandatory=True,
                            position=0, desc='image dimension (2 or 3)')
    output_average_image = File("average.nii", argstr='%s', position=1, desc='the name of the resulting image.', usedefault=True, hash_files=False)
    normalize = traits.Bool(argstr="%d", mandatory=True, position=2, desc='Normalize: if true, the 2nd image' +
                            'is divided by its mean. This will select the largest image to average into.')
    images = InputMultiPath(File(exists=True), argstr='%s', mandatory=True, position=3, desc=('image to apply transformation to (generally a coregistered functional)'))


class AverageImagesOutputSpec(TraitedSpec):
    output_average_image = File(exists=True, desc='average image file')


class AverageImages(ANTSCommand):
    """
    Examples
    --------
    >>> from nipype.interfaces.ants import AverageImages
    >>> avg = AverageImages()
    >>> avg.inputs.dimension = 3
    >>> avg.inputs.output_average_image = "average.nii.gz"
    >>> avg.inputs.normalize = True
    >>> avg.inputs.images = ['rc1s1.nii', 'rc1s1.nii']
    >>> avg.cmdline
    'AverageImages 3 average.nii.gz 1 rc1s1.nii rc1s1.nii'
    """
    _cmd = 'AverageImages'
    input_spec = AverageImagesInputSpec
    output_spec = AverageImagesOutputSpec

    def _format_arg(self, opt, spec, val):
        return super(AverageImages, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output_average_image'] = os.path.realpath(
            self.inputs.output_average_image)
        return outputs


class MultiplyImagesInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='%d', usedefault=False, mandatory=True, position=0, desc='image dimension (2 or 3)')
    first_input = File(
        argstr='%s', exists=True, mandatory=True, position=1, desc='image 1')
    second_input = traits.Either(File(exists=True), traits.Float, argstr='%s', mandatory=True, position=2, desc='image 2 or multiplication weight')
    output_product_image = File(argstr='%s', mandatory=True, position=3, desc='Outputfname.nii.gz: the name of the resulting image.')


class MultiplyImagesOutputSpec(TraitedSpec):
    output_product_image = File(exists=True, desc='average image file')


class MultiplyImages(ANTSCommand):
    """
    Examples
    --------
    >>> from nipype.interfaces.ants import MultiplyImages
    >>> test = MultiplyImages()
    >>> test.inputs.dimension = 3
    >>> test.inputs.first_input = 'moving2.nii'
    >>> test.inputs.second_input = 0.25
    >>> test.inputs.output_product_image = "out.nii"
    >>> test.cmdline
    'MultiplyImages 3 moving2.nii 0.25 out.nii'
    """
    _cmd = 'MultiplyImages'
    input_spec = MultiplyImagesInputSpec
    output_spec = MultiplyImagesOutputSpec

    def _format_arg(self, opt, spec, val):
        return super(MultiplyImages, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output_product_image'] = os.path.abspath(
            self.inputs.output_product_image)
        return outputs


class JacobianDeterminantInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='%d', usedefault=False, mandatory=True, position=0, desc='image dimension (2 or 3)')
    warp_file = File(argstr='%s', exists=True, mandatory=True,
                     position=1, desc='input warp file')
    output_prefix = File(argstr='%s', genfile=True, hash_files=False, position=2, desc='prefix of the output image filename: PREFIX(log)jacobian.nii.gz')
    use_log = traits.Enum(0, 1, argstr='%d', mandatory=False, position=3,
                          desc='log transform the jacobian determinant')
    template_mask = File(argstr='%s', exists=True, mandatory=False, position=4,
                         desc='template mask to adjust for head size')
    norm_by_total = traits.Enum(0, 1, argstr='%d', mandatory=False, position=5, desc='normalize jacobian by total in mask to adjust for head size')
    projection_vector = traits.List(traits.Float(), argstr='%s', sep='x', mandatory=False, position=6, desc='vector to project warp against')


class JacobianDeterminantOutputSpec(TraitedSpec):
    jacobian_image = File(exists=True, desc='(log transformed) jacobian image')


class JacobianDeterminant(ANTSCommand):
    """
    Examples
    --------
    >>> from nipype.interfaces.ants import JacobianDeterminant
    >>> jacobian = JacobianDeterminant()
    >>> jacobian.inputs.dimension = 3
    >>> jacobian.inputs.warp_file = 'ants_Warp.nii.gz'
    >>> jacobian.inputs.output_prefix = 'Sub001_'
    >>> jacobian.inputs.use_log = 1
    >>> jacobian.cmdline
    'ANTSJacobian 3 ants_Warp.nii.gz Sub001_ 1'
    """

    _cmd = 'ANTSJacobian'
    input_spec = JacobianDeterminantInputSpec
    output_spec = JacobianDeterminantOutputSpec

    def _gen_filename(self, name):
        if name == 'output_prefix':
            output = self.inputs.output_prefix
            if not isdefined(output):
                _, name, ext = split_filename(self.inputs.warp_file)
                output = name + '_'
            return output
        return None

    def _list_outputs(self):
        outputs = self._outputs().get()
        if self.inputs.use_log == 1:
            outputs['jacobian_image'] = os.path.abspath(
                self._gen_filename('output_prefix') + 'logjacobian.nii.gz')
        else:
            outputs['jacobian_image'] = os.path.abspath(
                self._gen_filename('output_prefix') + 'jacobian.nii.gz')
        return outputs
