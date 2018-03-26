# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""DTITK registration interfaces

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)
"""

from ..base import TraitedSpec, CommandLineInputSpec, traits, isdefined, File
from ...utils.filemanip import fname_presuffix
import os
from .base import CommandLineDtitk


class RigidInputSpec(CommandLineInputSpec):
    fixed_file = File(desc="fixed diffusion tensor image",
                      exists=True, mandatory=True,
                      position=0, argstr="%s")
    moving_file = File(desc="diffusion tensor image path", exists=True,
                       mandatory=True, position=1, argstr="%s", copyfile=False)
    similarity_metric = traits.Enum('EDS', 'GDS', 'DDS', 'NMI',
                                    mandatory=True, position=2, argstr="%s",
                                    desc="similarity metric", usedefault=True)
    samplingXYZ = traits.Tuple((4, 4, 4), mandatory=True, position=3,
                               argstr="%g %g %g", usedefault=True,
                               desc="dist between samp points (mm) (x,y,z)")
    ftol = traits.Float(mandatory=True, position=4, argstr="%g",
                        desc="cost function tolerance", default_value=0.01,
                        usedefault=True)
    useInTrans = traits.Bool(position=5, argstr="1",
                             desc="to initialize with existing xfm set as 1")


class RigidOutputSpec(TraitedSpec):
    out_file = File(exists=True)
    out_file_xfm = File(exists=True)


class RigidTask(CommandLineDtitk):
    """Performs rigid registration between two tensor volumes

    Example
    -------

    >>> import nipype.interfaces.dtitk as dtitk
    >>> node = dtitk.RigidTask()
    >>> node.inputs.fixed_file = 'ten1.nii.gz'
    >>> node.inputs.moving_file = 'ten2.nii.gz'
    >>> node.inputs.similarity_metric = 'EDS'
    >>> node.inputs.samplingXYZ = (4,4,4)
    >>> node.inputs.ftol = 0.01
    >>> node.inputs.useInTrans = True
    >>> node.cmdline # doctest: +ELLIPSIS
    'dti_rigid_reg ten1.nii.gz ten2.nii.gz EDS 4 4 4 0.01 1'
    >>> node.run() # doctest: +SKIP
    """
    input_spec = RigidInputSpec
    output_spec = RigidOutputSpec
    _cmd = 'dti_rigid_reg'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file_xfm'] = self.inputs.moving_file.replace('.nii.gz',
                                                                  '.aff')
        outputs['out_file'] = self.inputs.moving_file.replace('.nii.gz',
                                                              '_aff.nii.gz')
        return outputs


class AffineInputSpec(CommandLineInputSpec):
    fixed_file = File(desc="fixed diffusion tensor image",
                      exists=True, mandatory=True,
                      position=0, argstr="%s")
    moving_file = File(desc="diffusion tensor image path", exists=True,
                       mandatory=True, position=1, argstr="%s", copyfile=False)
    similarity_metric = traits.Enum('EDS', 'GDS', 'DDS', 'NMI',
                                    mandatory=True, position=2, argstr="%s",
                                    desc="similarity metric", usedefault=True)
    samplingXYZ = traits.Tuple((4, 4, 4), mandatory=True, position=3,
                               argstr="%g %g %g", usedefault=True,
                               desc="dist between samp points (mm) (x,y,z)")
    ftol = traits.Float(mandatory=True, position=4, argstr="%s",
                        desc="cost function tolerance", default_value=0.01,
                        usedefault=True)
    useInTrans = traits.Bool(position=5, argstr="1",
                             desc="to initialize with existing xfm set as 1",
                             default_value=True)


class AffineOutputSpec(TraitedSpec):
    out_file = File(exists=True)
    out_file_xfm = File(exists=True)


class AffineTask(CommandLineDtitk):
    """Performs affine registration between two tensor volumes

    Example
    -------

    >>> import nipype.interfaces.dtitk as dtitk
    >>> node = dtitk.AffineTask()
    >>> node.inputs.fixed_file = 'ten1.nii.gz'
    >>> node.inputs.moving_file = 'ten2.nii.gz'
    >>> node.inputs.similarity_metric = 'EDS'
    >>> node.inputs.samplingXYZ = (4,4,4)
    >>> node.inputs.ftol = 0.01
    >>> node.inputs.useInTrans = True
    >>> node.cmdline # doctest: +ELLIPSIS
    'dti_affine_reg ten1.nii.gz ten2.nii.gz EDS 4 4 4 0.01 1'
    >>> node.run() # doctest: +SKIP
    """
    input_spec = AffineInputSpec
    output_spec = AffineOutputSpec
    _cmd = 'dti_affine_reg'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file_xfm'] = self.inputs.moving_file.replace('.nii.gz',
                                                                  '.aff')
        outputs['out_file'] = self.inputs.moving_file.replace('.nii.gz',
                                                              '_aff.nii.gz')
        return outputs


class DiffeoInputSpec(CommandLineInputSpec):
    fixed_file = File(desc="fixed diffusion tensor image",
                      exists=True,  position=0, argstr="%s")
    moving_file = File(desc="moving diffusion tensor image",
                       exists=True, position=1, argstr="%s", copyfile=False)
    mask_file = File(desc="mask", exists=True,  position=2, argstr="%s")
    legacy = traits.Int(desc="legacy parameter; always set to 1",
                        exists=True, mandatory=True,
                        position=3, default_value=1, argstr="%s",
                        usedefault=True)
    n_iters = traits.Int(desc="number of iterations",
                         exists=True, mandatory=True,
                         position=4, default_value=6, argstr="%s",
                         usedefault=True)
    ftol = traits.Float(desc="iteration for the optimization to stop",
                        exists=True, mandatory=True,
                        position=5, default_value=0.002, argstr="%s",
                        usedefault=True)


class DiffeoOutputSpec(TraitedSpec):
    out_file = File(exists=True)
    out_file_xfm = File(exists=True)


class DiffeoTask(CommandLineDtitk):
    """Performs diffeomorphic registration between two tensor volumes

    Example
    -------

    >>> import nipype.interfaces.dtitk as dtitk
    >>> node = dtitk.DiffeoTask()
    >>> node.inputs.fixed_file = 'ten1.nii.gz'
    >>> node.inputs.moving_file = 'ten2.nii.gz'
    >>> node.inputs.mask = 'mask.nii.gz'
    >>> node.inputs.legacy = 1
    >>> node.inputs.n_iters = 6
    >>> node.inputs.ftol = 0.002
    >>> node.cmdline # doctest: +ELLIPSIS
    dti_diffeomorphic_reg ten1.nii.gz ten2.nii.gz mask.nii.gz 1 6 0.002
    >>> node.run() # doctest: +SKIP
    """
    input_spec = DiffeoInputSpec
    output_spec = DiffeoOutputSpec
    _cmd = 'dti_diffeomorphic_reg'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file_xfm'] = self.inputs.moving_file.replace(
            '.nii.gz', '_diffeo.df.nii.gz')
        outputs['out_file'] = self.inputs.moving_file.replace(
            '.nii.gz', '_diffeo.nii.gz')
        return outputs


class ComposeXfmInputSpec(CommandLineInputSpec):
    in_df = File(desc='diffeomorphic warp diffeo_xfm.df.nii.gz', exists=True,
                 argstr="-df %s", copyfile=False, mandatory=True)
    in_aff = File(desc='affine_xfm.aff', exists=True,
                  argstr="-aff %s", mandatory=True)
    out_file = traits.Str(desc='output_path', exists=True,
                          argstr="-out %s",  name_source="in_df",
                          name_template="%s_aff.df.nii.gz")


class ComposeXfmOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class ComposeXfmTask(CommandLineDtitk):
    """
     Combines diffeomorphic and affine transforms

    Example
    -------

    >>> import nipype.interfaces.dtitk as dtitk
    >>> node = dtitk.ComposeXfmTask()
    >>> node.inputs.in_df = 'myxfm.df.nii.gz'
    >>> node.inputs.in_aff= 'myxfm.aff'
    >>> node.cmdline # doctest: +ELLIPSIS
    'dfRightComposeAffine -df myxfm.df.nii.gz -aff myxfm.aff -out myxfm.df_aff.df.nii.gz'
    >>> node.run() # doctest: +SKIP
    """
    input_spec = ComposeXfmInputSpec
    output_spec = ComposeXfmOutputSpec
    _cmd = 'dfRightComposeAffine'


class affSymTensor3DVolInputSpec(CommandLineInputSpec):
    in_file = File(desc='moving tensor volume', exists=True,
                   argstr="-in %s", mandatory=True)
    out_file = traits.Str(desc='output filename', exists=True,
                          argstr="-out %s", name_source="in_file",
                          name_template="%s_affxfmd", keep_extension=True)
    transform = File(exists=True, argstr="-trans %s",
                     xor=['target', 'translation', 'euler', 'deformation'], desc='transform to apply: specify an input transformation  file; parameters input will be ignored',)
    interpolation = traits.Enum('LEI', 'EI', usedefault=True,
                                argstr="-interp %s",
                                desc='Log Euclidean Euclidean Interpolation')
    target = File(exists=True, argstr="-target %s", xor=['transform'],
                  desc='output volume specification read from the target volume if specified')
    reorient = traits.Enum('PPD', 'NO', 'FS', argstr='-reorient %s',
                           usedefault=True)
    translation = traits.Tuple((0, 0, 0), desc='translation (x,y,z) in mm',
                               argstr='-translation %g %g %g',
                               xor=['transform'])
    euler = traits.Tuple((0, 0, 0), desc='(theta, phi, psi) in degrees',
                         xor=['transform'], argstr='-euler %g %g %g')
    deformation = traits.Tuple((1, 1, 1, 0, 0, 0), desc='(xx,yy,zz,xy,yz,xz)',
                               xor=['transform'],
                               argstr='-deformation %g %g %g %g %g %g')


class affSymTensor3DVolOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class affSymTensor3DVolTask(CommandLineDtitk):
    """
    Applies affine transform to a tensor volume

    Example
    -------

    >>> import nipype.interfaces.dtitk as dtitk
    >>> node = dtitk.affSymTensor3DVolTask()
    >>> node.inputs.in_file = 'ten.nii'
    >>> node.inputs.transform = 'aff.txt'
    >>> node.cmdline # doctest: +ELLIPSIS
    'affineSymTensor3DVolume -in ten.nii -interp LEI -out Ptensor_affxfmd.nii.gz -reorient PPD -trans aff.aff'
    >>> node.run() # doctest: +SKIP
    """
    input_spec = affSymTensor3DVolInputSpec
    output_spec = affSymTensor3DVolOutputSpec
    _cmd = 'affineSymTensor3DVolume'


class affScalarVolInputSpec(CommandLineInputSpec):
    in_file = File(desc='moving scalar volume', exists=True,
                   argstr="-in %s", mandatory=True)
    out_file = traits.Str(desc='output filename', exists=True,
                          argstr="-out %s", name_source="in_file",
                          name_template="%s_affxfmd", keep_extension=True)
    transform = File(exists=True, argstr="-trans %s",
                     xor=['target', 'translation', 'euler', 'deformation'], desc='transform to apply: specify an input transformation  file; parameters input will be ignored',)
    interpolation = traits.Enum(0, 1, usedefault=True,
                                argstr="-interp %s",
                                desc='0=trilinear (def); 1=nearest neighbor')
    target = File(exists=True, argstr="-target %s", xor=['transform'],
                  desc='output volume specification read from the target volume if specified')
    translation = traits.Tuple((0, 0, 0), desc='translation (x,y,z) in mm',
                               argstr='-translation %g %g %g',
                               xor=['transform'])
    euler = traits.Tuple((0, 0, 0), desc='(theta, phi, psi) in degrees',
                         xor=['transform'], argstr='-euler %g %g %g')
    deformation = traits.Tuple((1, 1, 1, 0, 0, 0), desc='(xx,yy,zz,xy,yz,xz)',
                               xor=['transform'],
                               argstr='-deformation %g %g %g %g %g %g')



class affScalarVolOutputSpec(TraitedSpec):
    out_file = File(desc='moved volume', exists=True)


class affScalarVolTask(CommandLineDtitk):
    """
    Applies affine transform to a scalar volume

    Example
    -------

    >>> import nipype.interfaces.dtitk as dtitk
    >>> node = dtitk.affScalarVolTask()
    >>> node.inputs.in_volume = 'myvol.nii'
    >>> node.inputs.in_xfm = 'myxfm.aff'
    >>> node.cmdline # doctest: +ELLIPSIS
    affineScalarVolume -in myvol.nii -interp 0 -out myvol_affxfmd.nii -trans myxfm.aff
    >>> node.run() # doctest: +SKIP
    """
    input_spec = affScalarVolInputSpec
    output_spec = affScalarVolOutputSpec
    _cmd = 'affineScalarVolume'


# TODO: these haven't been used yet; need to be tested (ALL BELOW)


class diffeoSymTensor3DVolInputSpec(CommandLineInputSpec):
    in_tensor = File(desc='moving tensor', exists=True,
                     argstr="-in %s")
    in_xfm = File(desc='transform to apply', exists=True,
                  argstr="-trans %s")
    in_target = File(desc='', exists=True,
                     argstr="-target %s")
    out_file = traits.Str(desc='', exists=True,
                          argstr="-out %s", name_source="in_tensor",
                          name_template="%s_diffeoxfmd.nii.gz")


class diffeoSymTensor3DVolOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class diffeoSymTensor3DVolTask(CommandLineDtitk):
    """
    Applies diffeomorphic transform to a tensor volume

    Example
    -------

    >>> import nipype.interfaces.dtitk as dtitk
    >>> node = dtitk.diffeoSymTensor3DVolTask()
    >>> node.inputs.in_tensor = 'ten.nii'
    >>> node.inputs.in_xfm = 'myxfm.df.nii.gz'
    >>> node.cmdline # doctest: +ELLIPSIS

    >>> node.run() # doctest: +SKIP
    """

    input_spec = diffeoSymTensor3DVolInputSpec
    output_spec = diffeoSymTensor3DVolOutputSpec
    _cmd = 'deformationSymTensor3DVolume'


class diffeoScalarVolInputSpec(CommandLineInputSpec):
    in_volume = File(desc='moving volume', exists=True, argstr="-in %s",
                     mandatory=True)
    in_xfm = File(desc='transform to apply', exists=True, argstr="-trans %s",
                  mandatory=True)
    in_target = File(desc='', exists=True, argstr="-target %s", mandatory=True)
    out_file = traits.Str(desc='', argstr="-out %s", name_source="in_volume",
                          name_template="%s_diffeoxfmd", keep_extension=True)
    voxel_size = File(desc='', exists=True, argstr="-vsize %g")
    flip = File(desc='', exists=True,  argstr="-flip %s")
    resampling_type = traits.Enum(1, 0, desc='1=backward(def), 0=forward',
                                  exists=True,  argstr="-type %s")
    interp = traits.Enum(0, 1, desc='0=trilinear(def), 1=nearest neighbor',
                         exists=True, argstr="-interp %s", usedefault=True)


class diffeoScalarVolOutputSpec(TraitedSpec):
    out_file = File(desc='moved volume', exists=True)


class diffeoScalarVolTask(CommandLineDtitk):
    """
    Applies diffeomorphic transform to a scalar volume

    Example
    -------

    >>> import nipype.interfaces.dtitk as dtitk
    >>> node = dtitk.diffeoScalarVolTask()
    >>> node.inputs.in_volume = 'fa.nii.gz'
    >>> node.inputs.in_xfm = 'ants_Warp.nii.gz'
    >>> node.cmdline # doctest: +ELLIPSIS

    >>> node.run() # doctest: +SKIP
    """

    input_spec = diffeoScalarVolInputSpec
    output_spec = diffeoScalarVolOutputSpec
    _cmd = 'deformationScalarVolume'
