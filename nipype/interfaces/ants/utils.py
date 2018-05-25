# -*- coding: utf-8 -*-
"""ANTS Apply Transforms interface
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import os

from ..base import TraitedSpec, File, traits, InputMultiPath
from .base import ANTSCommand, ANTSCommandInputSpec


class AverageAffineTransformInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3,
        2,
        argstr='%d',
        mandatory=True,
        position=0,
        desc='image dimension (2 or 3)')
    output_affine_transform = File(
        argstr='%s',
        mandatory=True,
        position=1,
        desc='Outputfname.txt: the name of the resulting transform.')
    transforms = InputMultiPath(
        File(exists=True),
        argstr='%s',
        mandatory=True,
        position=3,
        desc='transforms to average')


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
    dimension = traits.Enum(
        3,
        2,
        argstr='%d',
        mandatory=True,
        position=0,
        desc='image dimension (2 or 3)')
    output_average_image = File(
        "average.nii",
        argstr='%s',
        position=1,
        usedefault=True,
        hash_files=False,
        desc='the name of the resulting image.')
    normalize = traits.Bool(
        argstr="%d",
        mandatory=True,
        position=2,
        desc='Normalize: if true, the 2nd image is divided by its mean. '
        'This will select the largest image to average into.')
    images = InputMultiPath(
        File(exists=True),
        argstr='%s',
        mandatory=True,
        position=3,
        desc=
        'image to apply transformation to (generally a coregistered functional)'
    )


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
    dimension = traits.Enum(
        3,
        2,
        argstr='%d',
        mandatory=True,
        position=0,
        desc='image dimension (2 or 3)')
    first_input = File(
        argstr='%s', exists=True, mandatory=True, position=1, desc='image 1')
    second_input = traits.Either(
        File(exists=True),
        traits.Float,
        argstr='%s',
        mandatory=True,
        position=2,
        desc='image 2 or multiplication weight')
    output_product_image = File(
        argstr='%s',
        mandatory=True,
        position=3,
        desc='Outputfname.nii.gz: the name of the resulting image.')


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


class CreateJacobianDeterminantImageInputSpec(ANTSCommandInputSpec):
    imageDimension = traits.Enum(
        3,
        2,
        argstr='%d',
        mandatory=True,
        position=0,
        desc='image dimension (2 or 3)')
    deformationField = File(
        argstr='%s',
        exists=True,
        mandatory=True,
        position=1,
        desc='deformation transformation file')
    outputImage = File(
        argstr='%s', mandatory=True, position=2, desc='output filename')
    doLogJacobian = traits.Enum(
        0, 1, argstr='%d', position=3, desc='return the log jacobian')
    useGeometric = traits.Enum(
        0, 1, argstr='%d', position=4, desc='return the geometric jacobian')


class CreateJacobianDeterminantImageOutputSpec(TraitedSpec):
    jacobian_image = File(exists=True, desc='jacobian image')


class CreateJacobianDeterminantImage(ANTSCommand):
    """
    Examples
    --------
    >>> from nipype.interfaces.ants import CreateJacobianDeterminantImage
    >>> jacobian = CreateJacobianDeterminantImage()
    >>> jacobian.inputs.imageDimension = 3
    >>> jacobian.inputs.deformationField = 'ants_Warp.nii.gz'
    >>> jacobian.inputs.outputImage = 'out_name.nii.gz'
    >>> jacobian.cmdline
    'CreateJacobianDeterminantImage 3 ants_Warp.nii.gz out_name.nii.gz'
    """

    _cmd = 'CreateJacobianDeterminantImage'
    input_spec = CreateJacobianDeterminantImageInputSpec
    output_spec = CreateJacobianDeterminantImageOutputSpec

    def _format_arg(self, opt, spec, val):
        return super(CreateJacobianDeterminantImage, self)._format_arg(
            opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['jacobian_image'] = os.path.abspath(self.inputs.outputImage)
        return outputs


class AffineInitializerInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3, 2, usedefault=True, position=0, argstr='%s', desc='dimension')
    fixed_image = File(
        exists=True,
        mandatory=True,
        position=1,
        argstr='%s',
        desc='reference image')
    moving_image = File(
        exists=True,
        mandatory=True,
        position=2,
        argstr='%s',
        desc='moving image')
    out_file = File(
        'transform.mat',
        usedefault=True,
        position=3,
        argstr='%s',
        desc='output transform file')
    # Defaults in antsBrainExtraction.sh -> 15 0.1 0 10
    search_factor = traits.Float(
        15.0,
        usedefault=True,
        position=4,
        argstr='%f',
        desc='increments (degrees) for affine search')
    radian_fraction = traits.Range(
        0.0,
        1.0,
        value=0.1,
        usedefault=True,
        position=5,
        argstr='%f',
        desc='search this arc +/- principal axes')
    principal_axes = traits.Bool(
        False,
        usedefault=True,
        position=6,
        argstr='%d',
        desc=
        'whether the rotation is searched around an initial principal axis alignment.'
    )
    local_search = traits.Int(
        10,
        usedefault=True,
        position=7,
        argstr='%d',
        desc=
        ' determines if a local optimization is run at each search point for the set '
        'number of iterations')


class AffineInitializerOutputSpec(TraitedSpec):
    out_file = File(desc='output transform file')


class AffineInitializer(ANTSCommand):
    """
    Initialize an affine transform (as in antsBrainExtraction.sh)

    >>> from nipype.interfaces.ants import AffineInitializer
    >>> init = AffineInitializer()
    >>> init.inputs.fixed_image = 'fixed1.nii'
    >>> init.inputs.moving_image = 'moving1.nii'
    >>> init.cmdline
    'antsAffineInitializer 3 fixed1.nii moving1.nii transform.mat 15.000000 0.100000 0 10'

    """
    _cmd = 'antsAffineInitializer'
    input_spec = AffineInitializerInputSpec
    output_spec = AffineInitializerOutputSpec

    def _list_outputs(self):
        return {'out_file': os.path.abspath(self.inputs.out_file)}


class ComposeMultiTransformInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3,
        2,
        argstr='%d',
        usedefault=True,
        position=0,
        desc='image dimension (2 or 3)')
    output_transform = File(
        argstr='%s',
        position=1,
        name_source=['transforms'],
        name_template='%s_composed',
        keep_extension=True,
        desc='the name of the resulting transform.')
    reference_image = File(
        argstr='%s',
        position=2,
        desc='Reference image (only necessary when output is warpfield)')
    transforms = InputMultiPath(
        File(exists=True),
        argstr='%s',
        mandatory=True,
        position=3,
        desc='transforms to average')


class ComposeMultiTransformOutputSpec(TraitedSpec):
    output_transform = File(exists=True, desc='Composed transform file')


class ComposeMultiTransform(ANTSCommand):
    """
    Take a set of transformations and convert them to a single transformation matrix/warpfield.

    Examples
    --------
    >>> from nipype.interfaces.ants import ComposeMultiTransform
    >>> compose_transform = ComposeMultiTransform()
    >>> compose_transform.inputs.dimension = 3
    >>> compose_transform.inputs.transforms = ['struct_to_template.mat', 'func_to_struct.mat']
    >>> compose_transform.cmdline
    'ComposeMultiTransform 3 struct_to_template_composed.mat struct_to_template.mat func_to_struct.mat'

    """
    _cmd = 'ComposeMultiTransform'
    input_spec = ComposeMultiTransformInputSpec
    output_spec = ComposeMultiTransformOutputSpec


class LabelGeometryInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3,
        2,
        argstr='%d',
        usedefault=True,
        position=0,
        desc='image dimension (2 or 3)')
    label_image = File(
        argstr='%s',
        position=1,
        mandatory=True,
        desc='label image to use for extracting geometry measures')
    intensity_image = File(
        value='[]',
        exists=True,
        argstr='%s',
        mandatory=True,
        usedefault=True,
        position=2,
        desc='Intensity image to extract values from. '
             'This is an optional input')
    output_file = traits.Str(
        name_source=['label_image'],
        name_template='%s.csv',
        argstr='%s',
        position=3,
        desc='name of output file')


class LabelGeometryOutputSpec(TraitedSpec):
    output_file = File(exists=True, desc='CSV file of geometry measures')


class LabelGeometry(ANTSCommand):
    """
    Extracts geometry measures using a label file and an optional image file

    Examples
    --------
    >>> from nipype.interfaces.ants import LabelGeometry
    >>> label_extract = LabelGeometry()
    >>> label_extract.inputs.dimension = 3
    >>> label_extract.inputs.label_image = 'atlas.nii.gz'
    >>> label_extract.cmdline
    'LabelGeometryMeasures 3 atlas.nii.gz [] atlas.csv'

    >>> label_extract.inputs.intensity_image = 'ants_Warp.nii.gz'
    >>> label_extract.cmdline
    'LabelGeometryMeasures 3 atlas.nii.gz ants_Warp.nii.gz atlas.csv'

    """
    _cmd = 'LabelGeometryMeasures'
    input_spec = LabelGeometryInputSpec
    output_spec = LabelGeometryOutputSpec
