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
                    InputMultiPath, OutputMultiPath, isdefined)
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

    >>> from nipype.interfaces.ants import antsApplyTransforms
    >>> atms = antsApplyTransforms()
    >>> atms.inputs.input_image = 'structural.nii'
    >>> atms.inputs.reference_image = 'ants_deformed.nii.gz'
    >>> atms.inputs.transforms = ['ants_Warp.nii.gz','ants_Affine.txt']
    >>> atms.cmdline
    'antsApplyTransforms --dimensionality 3 --input structural.nii --output structural_trans.nii --reference-image ants_deformed.nii.gz --transform ants_Warp.nii.gz --transform ants_Affine.txt'

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
            return "--output [%s,%s]"%(self.inputs.output_image, self.inputs.print_out_composite_warp_file)
        else:
            return "--output %s"%(self.inputs.output_image)

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

"""
COMMAND:
     antsApplyTransforms
          antsApplyTransforms, applied to an input image, transforms it according to a
          reference image and a transform (or a set of transforms).

OPTIONS:
     -d, --dimensionality 2/3
          This option forces the image to be treated as a specified-dimensional image. If
          not specified, antsWarp tries to infer the dimensionality from the input image.

     -i, --input inputFileName
          Currently, the only input objects supported are image objects. However, the
          current framework allows for warping of other objects such as meshes and point
          sets.

     -r, --reference-image imageFileName
          For warping input images, the reference image defines the spacing, origin, size,
          and direction of the output warped image.

     -o, --output warpedOutputFileName
                  [compositeDisplacementField,<printOutCompositeWarpFile=0>]
          One can either output the warped image or, if the boolean is set, one can print
          out the displacement field based on thecomposite transform and the reference
          image.

     -n, --interpolation Linear
                         NearestNeighbor
                         MultiLabel[<sigma=imageSpacing>,<alpha=4.0>]
                         Gaussian[<sigma=imageSpacing>,<alpha=1.0>]
                         BSpline[<order=3>]
                         CosineWindowedSinc
                         WelchWindowedSinc
                         HammingWindowedSinc
                         LanczosWindowedSinc
          Several interpolation options are available in ITK. These have all been made
          available.

     -t, --transform transformFileName
                     [transformFileName,useInverse]
          Several transform options are supported including all those defined in the ITK
          library in addition to a deformation field transform. The ordering of the
          transformations follows the ordering specified on the command line. An identity
          transform is pushed onto the transformation stack. Each new transform
          encountered on the command line is also pushed onto the transformation stack.
          Then, to warp the input object, each point comprising the input object is warped
          first according to the last transform pushed onto the stack followed by the
          second to last transform, etc. until the last transform encountered which is the
          identity transform. Also, it should be noted that the inverse transform can be
          accommodated with the usual caveat that such an inverse must be defined by the
          specified transform class

     -v, --default-value value
          Default voxel value to be used with input images only. Specifies the voxel value
          when the input point maps outside the output domain

     -h
          Print the help menu (short version).
          <VALUES>: 0

     --help
          Print the help menu.
          <VALUES>: 0
======================================================

## Forward direction
##   BtoA( X_A ) ~= B( AffineTfm(WarpTfm( X_A ) ) ),        Where X_A represents physical points from the space of image A
{BINARIES_DIRECTORY}/bin/antsApplyTransforms \
   --dimensionality 3 \
   --input SUBJ_B_T1_resampled.nii.gz \
   --reference-image SUBJ_A_T1_resampled.nii.gz \
   --output antsResampleBtoA.nii.gz \
   --interpolation Linear \
   --default-value 0 \
   --transforms [20120430_1348_ANTS6_1Warp.nii.gz, 20120430_1348_txfmv2fv_affine.mat] \
   --invert_transforms_flags [True, True]

## Reverse direction
##   AtoB( X_B ) ~= A( InvWarpTfm( InvAffineTfm( X_B ) ) )  Where X_B represents physical points from the space of image B
{BINARIES_DIRECTORY}/bin/antsApplyTransforms \
   --dimensionality 3 \
   --input SUBJ_B_T1_resampled.nii.gz \
   --reference-image SUBJ_A_T1_resampled.nii.gz \
   --output antsResampleBtoA.nii.gz \
   --interpolation Linear \
   --default-value 0 \
   --transforms [20120430_1348_txfmv2fv_affine.mat, 20120430_1348_ANTS6_1InverseWarp.nii.gz] \
   --invert_transforms_flags [True, False]

======================================================
    antsApplyTransforms.inputs  most of these are self explanatory.

    ## For the transform list definition, there needs to be a vector of input images, and a corresponding vector of inversion commands.
    antsApplyTransforms.inputs.transforms=[20120430_1348_ANTS6_1InverseWarp.nii.gz,20120430_1348_txfmv2fv_affine.mat]
    antsApplyTransforms.inputs.invertTransformsList=[0,1]

"""
