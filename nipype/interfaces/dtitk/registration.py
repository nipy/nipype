from ..base import TraitedSpec, CommandLineInputSpec, traits, isdefined
from ...utils.filemanip import fname_presuffix
import os
from .base import CommandLineDtitk


class RigidInputSpec(CommandLineInputSpec):
    fixed_file = traits.Str(desc="fixed diffusion tensor image",
                            exists=True, mandatory=True,
                            position=0, argstr="%s")
    moving_file = traits.Str(desc="diffusion tensor image path", exists=True,
                             mandatory=True, position=1, argstr="%s")
    similarity_metric = traits.Enum('EDS', 'GDS', 'DDS', 'NMI', exists=True,
                                    mandatory=True, position=2, argstr="%s",
                                    desc="similarity metric")
    samplingX = traits.Float(mandatory=True, position=3, argstr="%s",
                             desc="dist between samp points (mm)",
                             default_value=4)
    samplingY = traits.Float(mandatory=True, position=4, argstr="%s",
                             desc="dist between samp points (mm)",
                             default_value=4)
    samplingZ = traits.Float(mandatory=True, position=5, argstr="%s",
                             desc="dist between samp points (mm)",
                             default_value=4)
    ftol = traits.Float(mandatory=True, position=6, argstr="%s",
                        desc="cost function tolerance", default_value=0.01)
    useInTrans = traits.Float(mandatory=False, position=7, argstr="%s",
                              desc="to initialize with existing xfm set as 1",
                              default_value=1)


class RigidOutputSpec(TraitedSpec):
    out_file = traits.File(exists=True)
    out_file_xfm = traits.File(exists=True)


class RigidTask(CommandLineDtitk):
    """
    Performs rigid registration between two tensor volumes

        Example
        -------

        >>> import nipype.interfaces.dtitk as dtitk
        >>> node = dtitk.RigidTask()
        >>> node.inputs.fixed_file = 'diffusion.nii.gz'
        >>> node.inputs.moving_file = 'diffusion2.nii.gz'
        >>> node.inputs.similarity_metric = 'EDS'
        >>> node.inputs.samplingX = 4
        >>> node.inputs.samplingY = 4
        >>> node.inputs.samplingZ = 4
        >>> node.inputs.ftol = 0.01
        >>> node.inputs.useInTrans = 1
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
    fixed_file = traits.Str(desc="fixed diffusion tensor image",
                            exists=True, mandatory=True,
                            position=0, argstr="%s")
    moving_file = traits.Str(desc="diffusion tensor image path", exists=True,
                             mandatory=True, position=1, argstr="%s")
    similarity_metric = traits.Enum('EDS', 'GDS', 'DDS', 'NMI', exists=True,
                                    mandatory=True, position=2, argstr="%s",
                                    desc="similarity metric")
    samplingX = traits.Float(mandatory=True, position=3, argstr="%s",
                             desc="dist between samp points (mm)",
                             default_value=4)
    samplingY = traits.Float(mandatory=True, position=4, argstr="%s",
                             desc="dist between samp points (mm)",
                             default_value=4)
    samplingZ = traits.Float(mandatory=True, position=5, argstr="%s",
                             desc="dist between samp points (mm)",
                             default_value=4)
    ftol = traits.Float(mandatory=True, position=6, argstr="%s",
                        desc="cost function tolerance", default_value=0.01)
    useInTrans = traits.Float(mandatory=False, position=7, argstr="%s",
                              desc="to initialize with existing xfm set as 1",
                              default_value=1)


class AffineOutputSpec(TraitedSpec):
    out_file = traits.File(exists=True)
    out_file_xfm = traits.File(exists=True)


class AffineTask(CommandLineDtitk):
    """
    Performs affine registration between two tensor volumes

        Example
        -------

        >>> import nipype.interfaces.dtitk as dtitk
        >>> node = dtitk.AffineTask()
        >>> node.inputs.fixed_file = 'diffusion.nii.gz'
        >>> node.inputs.moving_file = 'diffusion2.nii.gz'
        >>> node.inputs.similarity_metric = 'EDS'
        >>> node.inputs.samplingX = 4
        >>> node.inputs.samplingY = 4
        >>> node.inputs.samplingZ = 4
        >>> node.inputs.ftol = 0.01
        >>> node.inputs.useInTrans = 1
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
    fixed_file = traits.Str(desc="fixed diffusion tensor image",
                            exists=True, mandatory=False, position=0,
                            argstr="%s")
    moving_file = traits.Str(desc="moving diffusion tensor image",
                             exists=True, mandatory=False,
                             position=1, argstr="%s")
    mask = traits.Str(desc="mask", exists=True, mandatory=False, position=2,
                      argstr="%s")
    legacy = traits.Float(desc="legacy parameter; always set to 1",
                          exists=True, mandatory=True,
                          position=3, default_value=1, argstr="%s")
    n_iters = traits.Float(desc="number of iterations",
                           exists=True, mandatory=True,
                           position=4, default_value=6, argstr="%s")
    ftol = traits.Float(desc="iteration for the optimization to stop",
                        exists=True, mandatory=True,
                        position=5, default_value=0.002, argstr="%s")


class DiffeoOutputSpec(TraitedSpec):
    out_file = traits.File(exists=True)
    out_file_xfm = traits.File(exists=True)


class DiffeoTask(CommandLineDtitk):
    """
            Performs diffeomorphic registration between two tensor volumes

                Example
                -------

                >>> import nipype.interfaces.dtitk as dtitk
                >>> node = dtitk.DiffeoTask()
                >>> node.inputs.fixed_file = 'diffusion.nii.gz'
                >>> node.inputs.moving_file = 'diffusion2.nii.gz'
                >>> node.inputs.mask = 'mask.nii.gz'
                >>> node.inputs.legacy = 1
                >>> node.inputs.n_iters = 6
                >>> node.inputs.ftol = 0.002
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
    in_df = traits.Str(desc='diffeomorphic file.df.nii.gz', exists=True,
                       mandatory=False, position=1, argstr="-df %s")
    in_aff = traits.Str(desc='affine file.aff', exists=True, mandatory=False,
                        position=0, argstr="-aff %s")
    out_file = traits.Str(desc='output_path', exists=True, mandatory=False,
                          position=2, argstr="-out %s",  name_source="in_df",
                          name_template="%s_comboaff.nii.gz")


class ComposeXfmOutputSpec(TraitedSpec):
    out_file = traits.File(desc='cheese', exists=True)


class ComposeXfmTask(CommandLineDtitk):
    """
     Combines diffeomorphic and affine transforms

                Example
                -------

                >>> import nipype.interfaces.dtitk as dtitk
                >>> node = dtitk.ComposeXfmTask()
                >>> node.inputs.in_df = 'ants_Warp.nii.gz'
                >>> node.inputs.in_aff= 'ants_Affine.txt'
                >>> node.run() # doctest: +SKIP
                """
    input_spec = ComposeXfmInputSpec
    output_spec = ComposeXfmOutputSpec
    _cmd = 'dfRightComposeAffine'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.in_df.replace('.df.nii.gz',
                                                        '_combo.df.nii.gz')
        return outputs


class diffeoSymTensor3DVolInputSpec(CommandLineInputSpec):
    in_tensor = traits.Str(desc='moving tensor', exists=True, mandatory=False,
                           position=0, argstr="-in %s")
    in_xfm = traits.Str(desc='transform to apply', exists=True,
                        mandatory=False,
                        position=1, argstr="-trans %s")
    in_target = traits.Str(desc='', exists=True, mandatory=False, position=2,
                           argstr="-target %s")
    out_file = traits.Str(desc='', exists=True, mandatory=False, position=3,
                          argstr="-out %s", name_source="in_tensor",
                          name_template="%s_diffeoxfmd.nii.gz")


class diffeoSymTensor3DVolOutputSpec(TraitedSpec):
    out_file = traits.File(desc='cheese', exists=True)


class diffeoSymTensor3DVolTask(CommandLineDtitk):
    """
    Applies diffeomorphic transform to a tensor volume

                Example
                -------

                >>> import nipype.interfaces.dtitk as dtitk
                >>> node = dtitk.diffeoSymTensor3DVolTask()
                >>> node.inputs.in_tensor = 'diffusion.nii'
                >>> node.inputs.in_xfm = 'ants_Warp.nii.gz'
                >>> node.run() # doctest: +SKIP
                """

    input_spec = diffeoSymTensor3DVolInputSpec
    output_spec = diffeoSymTensor3DVolOutputSpec
    _cmd = 'deformationSymTensor3DVolume'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        return outputs


class affSymTensor3DVolInputSpec(CommandLineInputSpec):
    in_tensor = traits.Str(desc='moving tensor', exists=True, mandatory=False,
                           position=0, argstr="-in %s")
    in_xfm = traits.Str(desc='transform to apply', exists=True,
                        mandatory=False, position=1, argstr="-trans %s")
    in_target = traits.Str(desc='', exists=True, mandatory=False, position=2,
                           argstr="-target %s")
    out_file = traits.Str(desc='', exists=True, mandatory=False, position=3,
                          argstr="-out %s", name_source="in_tensor",
                          name_template="%s_affxfmd.nii.gz")


class affSymTensor3DVolOutputSpec(TraitedSpec):
    out_file = traits.File(desc='cheese', exists=True)


class affSymTensor3DVolTask(CommandLineDtitk):
    """
    Applies affine transform to a tensor volume

                Example
                -------

                >>> import nipype.interfaces.dtitk as dtitk
                >>> node = dtitk.affSymTensor3DVolTask()
                >>> node.inputs.in_tensor = 'diffusion.nii'
                >>> node.inputs.in_xfm = 'ants_Affine.txt'
                >>> node.run() # doctest: +SKIP
                """
    input_spec = affSymTensor3DVolInputSpec
    output_spec = affSymTensor3DVolOutputSpec
    _cmd = 'affineSymTensor3DVolume'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class affScalarVolInputSpec(CommandLineInputSpec):
    in_volume = traits.Str(desc='moving volume', exists=True, mandatory=False,
                           position=0, argstr="-in %s")
    in_xfm = traits.Str(desc='transform to apply', exists=True,
                        mandatory=False,
                        position=1, argstr="-trans %s")
    in_target = traits.Str(desc='', position=2, argstr="-target %s")
    out_file = traits.Str(desc='', mandatory=False, position=3,
                          argstr="-out %s", name_source="in_volume",
                          name_template="%s_affxfmd.nii.gz")


class affScalarVolOutputSpec(TraitedSpec):
    out_file = traits.File(desc='moved volume', exists=True)


class affScalarVolTask(CommandLineDtitk):
    """
    Applies affine transform to a scalar volume

                Example
                -------

                >>> import nipype.interfaces.dtitk as dtitk
                >>> node = dtitk.affScalarVolTask()
                >>> node.inputs.in_volume = 'fa.nii.gz'
                >>> node.inputs.in_xfm = 'ants_Affine.txt'
                >>> node.run() # doctest: +SKIP
                """
    input_spec = affScalarVolInputSpec
    output_spec = affScalarVolOutputSpec
    _cmd = 'affineScalarVolume'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class diffeoScalarVolInputSpec(CommandLineInputSpec):
    in_volume = traits.Str(desc='moving volume', exists=True, mandatory=False,
                           position=0, argstr="-in %s")
    in_xfm = traits.Str(desc='transform to apply', exists=True,
                        mandatory=False,
                        position=2, argstr="-trans %s")
    in_target = traits.Str(desc='', exists=True, mandatory=False, position=3,
                           argstr="-target %s")
    out_file = traits.Str(desc='', position=1, argstr="-out %s",
                          name_source="in_volume",
                          name_template="%s_diffeoxfmd.nii.gz")
    in_vsize = traits.Str(desc='', exists=True, mandatory=False, position=4,
                          argstr="-vsize %s")
    in_flip = traits.Str(desc='', exists=True, mandatory=False, position=5,
                         argstr="-flip %s")
    in_type = traits.Str(desc='', exists=True, mandatory=False, position=6,
                         argstr="-type %s")
    in_interp = traits.Str(desc='0 trilin, 1 NN', exists=True, mandatory=False,
                           position=7, argstr="-interp %s")


class diffeoScalarVolOutputSpec(TraitedSpec):
    out_file = traits.File(desc='moved volume', exists=True)


class diffeoScalarVolTask(CommandLineDtitk):
    """
    Applies diffeomorphic transform to a scalar volume

                Example
                -------

                >>> import nipype.interfaces.dtitk as dtitk
                >>> node = dtitk.diffeoScalarVolTask()
                >>> node.inputs.in_volume = 'fa.nii.gz'
                >>> node.inputs.in_xfm = 'ants_Warp.nii.gz'
                >>> node.run() # doctest: +SKIP
                """

    input_spec = diffeoScalarVolInputSpec
    output_spec = diffeoScalarVolOutputSpec
    _cmd = 'deformationScalarVolume'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            self.inputs.out_file = fname_presuffix(self.inputs.in_volume,
                                                   suffix="_diffeoxfmd",
                                                   newpath=os.path.abspath(
                                                        "."))
        outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs
