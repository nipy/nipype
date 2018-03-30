# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""DTITK registration interfaces

DTI-TK developed by Gary Hui Zhang, gary.zhang@ucl.ac.uk
For additional help, visit http://dti-tk.sf.net

The high-dimensional tensor-based DTI registration algorithm

Zhang, H., Avants, B.B, Yushkevich, P.A., Woo, J.H., Wang, S., McCluskey, L.H.,
 Elman, L.B., Melhem, E.R., Gee, J.C., High-dimensional spatial normalization
 of diffusion tensor images improves the detection of white matter differences
 in amyotrophic lateral sclerosis, IEEE Transactions on Medical Imaging,
 26(11):1585-1597, November 2007. PMID: 18041273.

The original piecewise-affine tensor-based DTI registration algorithm at the
core of DTI-TK

Zhang, H., Yushkevich, P.A., Alexander, D.C., Gee, J.C., Deformable
 registration of diffusion tensor MR images with explicit orientation
 optimization, Medical Image Analysis, 10(5):764-785, October 2006. PMID:
 16899392.

"""

from ..base import TraitedSpec, CommandLineInputSpec, traits, File
from ...utils.filemanip import fname_presuffix
from .base import CommandLineDtitk

__docformat__ = 'restructuredtext'


class RigidInputSpec(CommandLineInputSpec):
    fixed_file = File(desc="fixed tensor volume", exists=True,
                      mandatory=True, position=0, argstr="%s")
    moving_file = File(desc="moving tensor volume", exists=True,
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


class Rigid(CommandLineDtitk):
    """Performs rigid registration between two tensor volumes

    Example
    -------

    >>> from nipype.interfaces import dtitk
    >>> node = dtitk.Rigid()
    >>> node.inputs.fixed_file = 'im1.nii'
    >>> node.inputs.moving_file = 'im2.nii'
    >>> node.inputs.similarity_metric = 'EDS'
    >>> node.inputs.samplingXYZ = (4,4,4)
    >>> node.inputs.ftol = 0.01
    >>> node.inputs.useInTrans = True
    >>> node.cmdline
    'dti_rigid_reg im1.nii im2.nii EDS 4 4 4 0.01 1'
    >>> node.run() # doctest: +SKIP
    """
    input_spec = RigidInputSpec
    output_spec = RigidOutputSpec
    _cmd = 'dti_rigid_reg'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        moving = self.inputs.moving_file
        outputs['out_file_xfm'] = fname_presuffix(moving, suffix='.aff',
                                                  use_ext=False)
        outputs['out_file'] = fname_presuffix(moving, suffix='_aff')
        return outputs


class Affine(Rigid):
    """Performs affine registration between two tensor volumes

    Example
    -------

    >>> from nipype.interfaces import dtitk
    >>> node = dtitk.Affine()
    >>> node.inputs.fixed_file = 'im1.nii'
    >>> node.inputs.moving_file = 'im2.nii'
    >>> node.inputs.similarity_metric = 'EDS'
    >>> node.inputs.samplingXYZ = (4,4,4)
    >>> node.inputs.ftol = 0.01
    >>> node.inputs.useInTrans = True
    >>> node.cmdline
    'dti_affine_reg im1.nii im2.nii EDS 4 4 4 0.01 1'
    >>> node.run() # doctest: +SKIP
    """
    _cmd = 'dti_affine_reg'


class DiffeoInputSpec(CommandLineInputSpec):
    fixed_file = File(desc="fixed tensor volume",
                      exists=True, position=0, argstr="%s")
    moving_file = File(desc="moving tensor volume",
                       exists=True, position=1, argstr="%s", copyfile=False)
    mask_file = File(desc="mask", exists=True,  position=2, argstr="%s")
    legacy = traits.Enum(1, desc="legacy parameter; always set to 1",
                         usedefault=True, mandatory=True,
                         position=3, argstr="%d")
    n_iters = traits.Int(6, desc="number of iterations",
                         exists=True, mandatory=True,
                         position=4, argstr="%d", usedefault=True)
    ftol = traits.Float(0.002, desc="iteration for the optimization to stop",
                        exists=True, mandatory=True, position=5, argstr="%g",
                        usedefault=True)


class DiffeoOutputSpec(TraitedSpec):
    out_file = File(exists=True)
    out_file_xfm = File(exists=True)


class Diffeo(CommandLineDtitk):
    """Performs diffeomorphic registration between two tensor volumes

    Example
    -------

    >>> from nipype.interfaces import dtitk
    >>> node = dtitk.Diffeo()
    >>> node.inputs.fixed_file = 'im1.nii'
    >>> node.inputs.moving_file = 'im2.nii'
    >>> node.inputs.mask_file = 'mask.nii'
    >>> node.inputs.legacy = 1
    >>> node.inputs.n_iters = 6
    >>> node.inputs.ftol = 0.002
    >>> node.cmdline
    'dti_diffeomorphic_reg im1.nii im2.nii mask.nii 1 6 0.002'
    >>> node.run() # doctest: +SKIP
    """
    input_spec = DiffeoInputSpec
    output_spec = DiffeoOutputSpec
    _cmd = 'dti_diffeomorphic_reg'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        moving = self.inputs.moving_file()
        outputs['out_file_xfm'] = fname_presuffix(moving, suffix='_diffeo.df')
        outputs['out_file'] = fname_presuffix(moving, suffix='_diffeo')
        return outputs


class ComposeXfmInputSpec(CommandLineInputSpec):
    in_df = File(desc='diffeomorphic warp file', exists=True,
                 argstr="-df %s", copyfile=False, mandatory=True)
    in_aff = File(desc='affine transform file', exists=True,
                  argstr="-aff %s", mandatory=True)
    out_file = File(desc='output path',
                    argstr="-out %s",  name_source="in_df",
                    name_template="%s_affdf.nii")
    # keep_extension is keeping the .df but not .nii; need to figure out


class ComposeXfmOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class ComposeXfm(CommandLineDtitk):
    """
     Combines diffeomorphic and affine transforms

    Example
    -------

    >>> from nipype.interfaces import dtitk
    >>> node = dtitk.ComposeXfm()
    >>> node.inputs.in_df = 'im_warp.df.nii'
    >>> node.inputs.in_aff= 'im_affine.aff'
    >>> node.cmdline #doctest:
    'dfRightComposeAffine -aff im_affine.aff -df im_warp.df.nii -out\
     im_warp.df_affdf.nii'
    >>> node.run() # doctest: +SKIP
    """
    input_spec = ComposeXfmInputSpec
    output_spec = ComposeXfmOutputSpec
    _cmd = 'dfRightComposeAffine'


class affSymTensor3DVolInputSpec(CommandLineInputSpec):
    in_file = File(desc='moving tensor volume', exists=True,
                   argstr="-in %s", mandatory=True)
    out_file = File(desc='output filename',
                    argstr="-out %s", name_source="in_file",
                    name_template="%s_affxfmd", keep_extension=True)
    transform = File(exists=True, argstr="-trans %s",
                     xor=['target', 'translation', 'euler', 'deformation'],
                     desc='transform to apply: specify an input transformation'
                     ' file; parameters input will be ignored',)
    interpolation = traits.Enum('LEI', 'EI', usedefault=True,
                                argstr="-interp %s",
                                desc='Log Euclidean/Euclidean Interpolation')
    reorient = traits.Enum('PPD', 'NO', 'FS', argstr='-reorient %s',
                           usedefault=True, desc='Reorientation strategy: '
                           'preservation of principal direction, no '
                           'reorientation, or finite strain')
    target = File(exists=True, argstr="-target %s", xor=['transform'],
                  desc='output volume specification read from the target '
                  'volume if specified')
    translation = traits.Tuple((traits.Float(), traits.Float(),
                               traits.Float()),
                               desc='translation (x,y,z) in mm',
                               argstr='-translation %g %g %g',
                               xor=['transform'])
    euler = traits.Tuple((traits.Float(), traits.Float(), traits.Float()),
                         desc='(theta, phi, psi) in degrees',
                         xor=['transform'], argstr='-euler %g %g %g')
    deformation = traits.Tuple((traits.Float(),) * 6,
                               desc='(xx,yy,zz,xy,yz,xz)', xor=['transform'],
                               argstr='-deformation %g %g %g %g %g %g')


class affSymTensor3DVolOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class affSymTensor3DVol(CommandLineDtitk):
    """
    Applies affine transform to a tensor volume

    Example
    -------

    >>> from nipype.interfaces import dtitk
    >>> node = dtitk.affSymTensor3DVol()
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.transform = 'im_affine.aff'
    >>> node.cmdline #doctest:
    'affineSymTensor3DVolume -in im1.nii -interp LEI -out im1_affxfmd.nii\
     -reorient PPD -trans im_affine.aff'
    >>> node.run() # doctest: +SKIP
    """
    input_spec = affSymTensor3DVolInputSpec
    output_spec = affSymTensor3DVolOutputSpec
    _cmd = 'affineSymTensor3DVolume'


class affScalarVolInputSpec(CommandLineInputSpec):
    in_file = File(desc='moving scalar volume', exists=True,
                   argstr="-in %s", mandatory=True)
    out_file = File(desc='output filename',
                    argstr="-out %s", name_source="in_file",
                    name_template="%s_affxfmd", keep_extension=True)
    transform = File(exists=True, argstr="-trans %s",
                     xor=['target', 'translation', 'euler', 'deformation'],
                     desc='transform to apply: specify an input transformation'
                     ' file; parameters input will be ignored',)
    interpolation = traits.Enum('trilinear', 'NN',
                                usedefault=True, argstr="-interp %s",
                                desc='trilinear or nearest neighbor'
                                ' interpolation')
    target = File(exists=True, argstr="-target %s", xor=['transform'],
                  desc='output volume specification read from the target '
                  'volume if specified')
    translation = traits.Tuple((traits.Float(), traits.Float(),
                               traits.Float()),
                               desc='translation (x,y,z) in mm',
                               argstr='-translation %g %g %g',
                               xor=['transform'])
    euler = traits.Tuple((traits.Float(), traits.Float(), traits.Float()),
                         desc='(theta, phi, psi) in degrees',
                         xor=['transform'], argstr='-euler %g %g %g')
    deformation = traits.Tuple((traits.Float(),) * 6,
                               desc='(xx,yy,zz,xy,yz,xz)', xor=['transform'],
                               argstr='-deformation %g %g %g %g %g %g')


class affScalarVolOutputSpec(TraitedSpec):
    out_file = File(desc='moved volume', exists=True)


class affScalarVol(CommandLineDtitk):
    """
    Applies affine transform to a scalar volume

    Example
    -------

    >>> from nipype.interfaces import dtitk
    >>> node = dtitk.affScalarVol()
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.transform = 'im_affine.aff'
    >>> node.cmdline #doctest:
    'affineScalarVolume -in im1.nii -interp 0 -out im1_affxfmd.nii -trans\
     im_affine.aff'
    >>> node.run() # doctest: +SKIP
    """
    input_spec = affScalarVolInputSpec
    output_spec = affScalarVolOutputSpec
    _cmd = 'affineScalarVolume'

    def _format_arg(self, name, spec, value):
        if name == 'interpolation':
            value = {'trilinear': 0, 'NN': 1}[value]
        return super(affScalarVol, self)._format_arg(name, spec, value)


class diffeoSymTensor3DVolInputSpec(CommandLineInputSpec):
    in_file = File(desc='moving tensor volume', exists=True,
                   argstr="-in %s", mandatory=True)
    out_file = File(desc='output filename',
                    argstr="-out %s", name_source="in_file",
                    name_template="%s_diffeoxfmd", keep_extension=True)
    transform = File(exists=True, argstr="-trans %s",
                     mandatory=True, desc='transform to apply')
    df = traits.Str('FD', argstr="-df %s", usedefault=True)
    interpolation = traits.Enum('LEI', 'EI', usedefault=True,
                                argstr="-interp %s",
                                desc='Log Euclidean/Euclidean Interpolation')
    reorient = traits.Enum('PPD', 'FS', argstr='-reorient %s',
                           usedefault=True, desc='Reorientation strategy: '
                           'preservation of principal direction or finite '
                           'strain')
    target = File(exists=True, argstr="-target %s", xor=['voxel_size'],
                  desc='output volume specification read from the target '
                  'volume if specified')
    voxel_size = traits.Tuple((traits.Float(), traits.Float(), traits.Float()),
                              desc='xyz voxel size (superseded by target)',
                              argstr="-vsize %g %g %g", xor=['target'])
    flip = traits.Tuple((traits.Int(), traits.Int(), traits.Int()),
                        exists=True, argstr="-flip %d %d %d")
    resampling_type = traits.Enum('backward', 'forward',
                                  desc='use backward or forward resampling',
                                  exists=True,  argstr="-type %s")


class diffeoSymTensor3DVolOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class diffeoSymTensor3DVol(CommandLineDtitk):
    """
    Applies diffeomorphic transform to a tensor volume

    Example
    -------

    >>> from nipype.interfaces import dtitk
    >>> node = dtitk.diffeoSymTensor3DVol()
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.transform = 'im_warp.df.nii'
    >>> node.cmdline #doctest:
    'deformationSymTensor3DVolume -df FD -in im1.nii -interp LEI -out\
     im1_diffeoxfmd.nii -reorient PPD -trans im_warp.df.nii'
    >>> node.run() # doctest: +SKIP
    """

    input_spec = diffeoSymTensor3DVolInputSpec
    output_spec = diffeoSymTensor3DVolOutputSpec
    _cmd = 'deformationSymTensor3DVolume'

    def _format_arg(self, name, spec, value):
        if name == 'resampling_type':
            value = {'forward': 0, 'backward': 1}[value]
        return super(diffeoSymTensor3DVol, self)._format_arg(name, spec, value)


class diffeoScalarVolInputSpec(CommandLineInputSpec):
    in_file = File(desc='moving scalar volume', exists=True,
                   argstr="-in %s", mandatory=True)
    out_file = File(desc='output filename',
                    argstr="-out %s", name_source="in_file",
                    name_template="%s_diffeoxfmd", keep_extension=True)
    transform = transform = File(exists=True, argstr="-trans %s",
                                 mandatory=True, desc='transform to apply')
    target = File(exists=True, argstr="-target %s", xor=['voxel_size'],
                  desc='output volume specification read from the target '
                  'volume if specified')
    voxel_size = traits.Tuple((traits.Float(), traits.Float(), traits.Float()),
                              desc='xyz voxel size (superseded by target)',
                              argstr="-vsize %g %g %g", xor=['target'])
    flip = traits.Tuple((traits.Int(), traits.Int(), traits.Int()),
                        exists=True, argstr="-flip %d %d %d")
    resampling_type = traits.Enum('backward', 'forward',
                                  desc='use backward or forward resampling',
                                  exists=True,  argstr="-type %s")
    interpolation = traits.Enum('trilinear', 'NN',
                                desc='trilinear, or nearest neighbor',
                                exists=True, argstr="-interp %s",
                                usedefault=True)


class diffeoScalarVolOutputSpec(TraitedSpec):
    out_file = File(desc='moved volume', exists=True)


class diffeoScalarVol(CommandLineDtitk):
    """
    Applies diffeomorphic transform to a scalar volume

    Example
    -------

    >>> from nipype.interfaces import dtitk
    >>> node = dtitk.diffeoScalarVol()
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.transform = 'im_warp.df.nii'
    >>> node.cmdline
    'deformationScalarVolume -in im1.nii -interp 0 -out im1_diffeoxfmd.nii\
     -trans im_warp.df.nii'
    >>> node.run() # doctest: +SKIP
    """

    input_spec = diffeoScalarVolInputSpec
    output_spec = diffeoScalarVolOutputSpec
    _cmd = 'deformationScalarVolume'

    def _format_arg(self, name, spec, value):
        if name == 'resampling_type':
            value = {'forward': 0, 'backward': 1}[value]
        super(diffeoScalarVol, self)._format_arg(name, spec, value)
        if name == 'interpolation':
            value = {'trilinear': 0, 'NN': 1}[value]
        return super(diffeoScalarVol, self)._format_arg(name, spec, value)
