# Local imports
from ..base import (TraitedSpec, File, traits, InputMultiPath, OutputMultiPath,
                    isdefined)
from ...utils.filemanip import split_filename
from .base import ANTSCommand, ANTSCommandInputSpec


class ApplyTransformInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='--dimensionality %d', usedefault=True,
                            desc='image dimension (2 or 3)')
    input_image = File(argstr='--input %s', mandatory=True, 
                        desc=('image to apply transformation to (generally a '
                              'coregistered functional)'))
    output_image = traits.Str(argstr='--output %s',
                             desc=('output file name'), genfile=True)
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
    "voxel value to be used with input images only. Specifies the voxel value "+
          "when the input point maps outside the output domain")


class ApplyTransformOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc='Warped image')


class ApplyTransform(ANTSCommand):
    """Warps an image from one space to another

    Examples
    --------

    >>> from nipype.interfaces.ants import ApplyTransform
    >>> wimt = ApplyTransform()
    >>> wimt.inputs.input_image = 'structural.nii'
    >>> wimt.inputs.reference_image = 'ants_deformed.nii.gz'
    >>> wimt.inputs.transformation_files = ['ants_Warp.nii.gz','ants_Affine.txt']
    >>> wimt.cmdline
    'antsApplyTransforms --dimensionality 3 --input structural.nii --output structural_trans.nii --reference-image ants_deformed.nii.gz --transform ants_Warp.nii.gz --transform ants_Affine.txt'

    """

    _cmd = 'antsApplyTransforms'
    input_spec = ApplyTransformInputSpec
    output_spec = ApplyTransformOutputSpec

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
                if isdefined(self.inputs.invert_transforms) and i+1 in self.inputs.invert_transforms:
                    series.append(tmpl + "[%s,1]"%transformation_file)
                else:
                    series.append(tmpl + "%s"%transformation_file)
            return ' '.join(series)
        return super(ApplyTransform, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output_image'] = self._gen_filename('output_image')
        return outputs


class N4BiasFieldCorrectionInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='--image-dimension %d', usedefault=True,
                            desc='image dimension (2 or 3)')
    input_image = File(argstr='--input-image %s', mandatory=True, 
                        desc=('image to apply transformation to (generally a '
                              'coregistered functional)'))
    output_image = traits.Str(argstr='--output %s',
                             desc=('output file name'), genfile=True)
    bspline_fitting_distance = traits.Float(argstr="--bsline-fitting [%g]")
    shrink_factor = traits.Int(argstr="--shrink-factor %d")
    n_iterations = traits.List(traits.Int(), argstr="--convergence [ %s", sep="x", requires=['convergence_threshold'], position=1)
    convergence_threshold = traits.Float(argstr=",%g]", requires=['n_iterations'], position=2)


class N4BiasFieldCorrectionOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc='Warped image')


class N4BiasFieldCorrection(ANTSCommand):
    """Warps an image from one space to another

    Examples
    --------

    >>> from nipype.interfaces.ants.utils import N4BiasFieldCorrection
    >>> n4 = N4BiasFieldCorrection()
    >>> n4.inputs.dimension = 3
    >>> n4.inputs.input_image = 'structural.nii'
    >>> n4.inputs.bspline_fitting_distance = 300
    >>> n4.inputs.shrink_factor = 3
    >>> n4.inputs.n_iterations = [50,50,30,20]
    >>> n4.inputs.convergence_threshold = 1e-6
    >>> n4.cmdline
    'N4BiasFieldCorrection --convergence [ 50x50x30x20 ,1e-06] --bsline-fitting [300] --image-dimension 3 --input-image structural.nii --output structural_corrected.nii --shrink-factor 3'
    """

    _cmd = 'N4BiasFieldCorrection'
    input_spec = N4BiasFieldCorrectionInputSpec
    output_spec = N4BiasFieldCorrectionOutputSpec

    def _gen_filename(self, name):
        if name == 'output_image':
            output = self.inputs.output_image
            if not isdefined(output):
                _, name, ext = split_filename(self.inputs.input_image)
                output = name + '_corrected' + ext
            return output
        return None

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output_image'] = self._gen_filename('output_image')
        return outputs
