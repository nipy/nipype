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


class antsApplyTransformsInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='--dimensionality %d', usedefault=True,
                            desc='image dimension (2 or 3)')
    input_image = File(argstr='--input %s', mandatory=True,
                        desc=('image to apply transformation to (generally a '
                              'coregistered functional)'),
        exists=True)
    output_image = traits.Str(argstr='--output %s',
                             desc=('output file name'), genfile=True,
                             hash_file=False)
    reference_image = File(argstr='--reference-image %s', mandatory=True,
                       desc='reference image space that you wish to warp INTO',
                       exists=True)
    interpolation = traits.Enum('Linear',
                                'NearestNeighbor',
                                'CosineWindowedSinc',
                                'WelchWindowedSinc',
                                'HammingWindowedSinc',
                                'LanczosWindowedSinc',
                                # 'MultiLabel',
                                # 'Gaussian',
                                # 'BSpline',
                                argstr='%s', mandatory = True)
    # TODO: Implement these options for multilabel, gaussian, and bspline
    # interpolation_sigma = traits.Float(requires=['interpolation'])
    # interpolation_alpha = traits.Float(requires=['interpolation_sigma'])
    # bspline_order = traits.Int(3, requires=['interpolation'])
    transforms = traits.List(File(exists=True), argstr='%s', mandatory=True, desc=(''))
    invert_transforms_flags = traits.List(traits.Bool(), requires=["transforms"])
    default_value = traits.Int(argstr='--default-value %d', mandatory = True)
    print_out_composite_warp_file = traits.Enum(0, 1, requires=["output_image"], desc=('')) # TODO: Change to boolean

class antsApplyTransformsOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc='Warped image')

class antsApplyTransforms(ANTSCommand):
    """antsApplyTransforms, applied to an input image, transforms it according to a
    reference image and a transform (or a set of transforms).

    Examples
    --------

    >>> from nipype.interfaces.ants.antsApplyTransforms import antsApplyTransforms
    >>> at = antsApplyTransforms()
    >>> at.inputs.dimension = 3
    >>> at.inputs.input_image = 'moving1.nii'
    >>> at.inputs.reference_image = 'fixed1.nii'
    >>> at.inputs.interpolation = 'Linear'
    >>> at.inputs.default_value = 0
    >>> at.inputs.transforms = ['trans.mat', 'ants_Warp.nii.gz']
    >>> at.cmdline
    'antsApplyTransforms --default-value 0 --dimensionality 3 --input moving1.nii --interpolation Linear --output moving1_trans.nii --reference-image fixed1.nii --transform trans.mat --transform ants_Warp.nii.gz'


    """
    _cmd = 'antsApplyTransforms'
    input_spec = antsApplyTransformsInputSpec
    output_spec = antsApplyTransformsOutputSpec

    def _gen_filename(self, name):
        if name == 'output_image':
            output = self.inputs.output_image
            if not isdefined(output):
                _, name, ext = split_filename(self.inputs.input_image)
                output = name + '_trans' + ext
            return output
        return None

    def _getTransformFileNames(self):
        retval = []
        for ii in range(len(self.inputs.transforms)):
            if isdefined(self.inputs.invert_transforms_flags):
                if len(self.inputs.transforms) == len(self.inputs.invert_transforms_flags):
                    retval.append("--transform [%s,%s]"%(self.inputs.transforms[ii], self.inputs.invert_transforms_flags[ii]))
                else:
                    raise Exception("ERROR: The useInverse list must have the same number of entries as the transformsFileName list.")
            else:
                retval.append("--transform %s" % self.inputs.transforms[ii])
        return " ".join(retval)

    def _getOutputWarpedFileName(self):
        if isdefined(self.inputs.print_out_composite_warp_file):
            return "--output [%s,%s]"%(self._gen_filename("output_image"), self.inputs.print_out_composite_warp_file)
        else:
            return "--output %s"%(self._gen_filename("output_image"))

    def _format_arg(self, opt, spec, val):
        if opt == "output_image":
            return self._getOutputWarpedFileName()
        elif opt == "transforms":
            return self._getTransformFileNames()
        elif opt == 'interpolation':
            # TODO: handle multilabel, gaussian, and bspline options
            return '--interpolation %s' % self.inputs.interpolation
        return super(antsApplyTransforms, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output_image'] = os.path.abspath(self._gen_filename('output_image'))
        return outputs