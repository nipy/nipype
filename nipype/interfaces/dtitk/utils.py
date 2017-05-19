__author__ = 'kjordan'

from nipype.interfaces.base import TraitedSpec, CommandLineInputSpec, CommandLine, File, traits, isdefined, split_filename
from nipype.utils.filemanip import fname_presuffix
import os
from nipype.interfaces.fsl.base import Info



# TODO: fix all wrappers to reflect the one with ScalarVol

class CommandLineDtitk(CommandLine):

    def _gen_fname(self, basename, cwd=None, suffix=None, change_ext=True,
                   ext=None):
        """Generate a filename based on the given parameters.

        The filename will take the form: cwd/basename<suffix><ext>.
        If change_ext is True, it will use the extentions specified in
        <instance>intputs.output_type.

        Parameters
        ----------
        basename : str
            Filename to base the new filename on.
        cwd : str
            Path to prefix to the new filename. (default is os.getcwd())
        suffix : str
            Suffix to add to the `basename`.  (defaults is '' )
        change_ext : bool
            Flag to change the filename extension to the FSL output type.
            (default True)

        Returns
        -------
        fname : str
            New filename based on given parameters.

        """

        if basename == '':
            msg = 'Unable to generate filename for command %s. ' % self.cmd
            msg += 'basename is not set!'
            raise ValueError(msg)
        if cwd is None:
            cwd = os.getcwd()
        if ext is None:
            #print "AAA"
            #print self.inputs.output_type
            ext = Info.output_type_to_ext(self.inputs.output_type)
        if change_ext:
            if suffix:
                suffix = ''.join((suffix, ext))
            else:
                suffix = ext
        if suffix is None:
            suffix = ''
        fname = fname_presuffix(basename, suffix=suffix,
                                use_ext=False, newpath=cwd)
        return fname


class TVAdjustOriginInputSpec(CommandLineInputSpec):
    in_file = File(desc="image to resample", exists=True, mandatory=True, position=0, argstr="-in %s")
    out_file = traits.Str(genfile=True, desc='output path', position=1, argstr="-out %s")
    origin = traits.Str(desc='xyz voxel size', exists=True, mandatory=False, position=4, argstr='-origin %s')


class TVAdjustOriginOutputSpec(TraitedSpec):
    out_file = traits.Str(exists=True)


class TVAdjustOriginTask(CommandLineDtitk):
    input_spec = TVAdjustOriginInputSpec
    output_spec = TVAdjustOriginOutputSpec
    _cmd = 'TVAdjustVoxelspace'
    _suffix = "_originzero"

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs["out_file"] = self._gen_fname(self.inputs.in_file, suffix=self._suffix, ext='.'+'.'.join(self.inputs.in_file.split(".")[1:]))
        outputs["out_file"] = os.path.abspath(outputs["out_file"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None

class TVAdjustVoxSpInputSpec(CommandLineInputSpec):
    in_file = File(desc="image to resample", exists=True, mandatory=True, position=0, argstr="-in %s")
    out_file = traits.Str(genfile=True, desc='output path', position=1, argstr="-out %s")
    origin = traits.Str(desc='xyz voxel size', exists=True, mandatory=False, position=4, argstr='-origin %s')
    target = traits.Str(desc='target volume', exists=True, mandatory=False, position=2, \
                            argstr="-target %s")
    vsize = traits.Str(desc='resampled voxel size', exists=True, mandatory=False, position=3, \
                          argstr="-vsize %s")

class TVAdjustVoxSpOutputSpec(TraitedSpec):
    out_file = traits.Str(exists=True)


class TVAdjustVoxSpTask(CommandLineDtitk):
    input_spec = TVAdjustVoxSpInputSpec
    output_spec = TVAdjustVoxSpOutputSpec
    _cmd = 'TVAdjustVoxelspace'
    _suffix = '_reslice'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs["out_file"] = self._gen_fname(self.inputs.in_file, suffix=self._suffix, ext='.'+'.'.join(self.inputs.in_file.split(".")[1:]))
        outputs["out_file"] = os.path.abspath(outputs["out_file"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None


class RigidInputSpec(CommandLineInputSpec):
    fixed_file = traits.Str(desc="fixed diffusion tensor image", exists=True, mandatory=True, \
                    position=0, argstr="%s")
    moving_file = traits.Str(desc="diffusion tensor image path", exists=True, mandatory=True, \
                     position=1, argstr="%s")
    similarity_metric = traits.Enum('EDS', 'GDS', 'DDS', 'NMI', \
                                exists=True, mandatory=True, position=2,
                                    argstr="%s", desc="similarity metric")

class RigidOutputSpec(TraitedSpec):
    out_file = traits.File(exists=True)
    out_file_xfm = traits.File(exists=True)


class RigidTask(CommandLineDtitk):
    input_spec = RigidInputSpec
    output_spec = RigidOutputSpec
    _cmd = 'dti_rigid_sn'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file_xfm'] = self.inputs.in_file.replace('.nii.gz','.aff')
        outputs['out_file'] = self.inputs.in_file.replace('.nii.gz', '_aff.nii.gz')
        return outputs


class AffineInputSpec(CommandLineInputSpec):
    in_fixed_tensor = traits.Str(desc="fixed diffusion tensor image", exists=True, mandatory=False, \
                    position=0, argstr="%s")
    in_moving_txt = traits.Str(desc="moving list of diffusion tensor image paths", exists=True, mandatory=False, \
                     position=1, argstr="%s")
    in_similarity_metric = traits.Enum('EDS', 'GDS', 'DDS', 'NMI', \
                                exists=True, mandatory=False, position=3, argstr="%s", desc = "similarity metric")
    in_usetrans_flag = traits.Enum('--useTrans', '', exists=True, mandatory=False, position=4, argstr="%s", \
                                   desc="initialize using rigid transform??")


class AffineOutputSpec(TraitedSpec):
    out_file = traits.File(exists=True)
    out_file_xfm = traits.File(exists=True)


class AffineTask(CommandLineDtitk):
    input_spec = AffineInputSpec
    output_spec = AffineOutputSpec
    _cmd = 'dti_affine_sn'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file_xfm'] = self.inputs.in_fixed_tensor.replace('.nii.gz','.aff')
        outputs['out_file'] = self.inputs.in_fixed_tensor.replace('.nii.gz', '_aff.nii.gz')
        return outputs


class DiffeoInputSpec(CommandLineInputSpec):
    in_fixed_tensor = traits.Str(desc="fixed diffusion tensor image", exists=True, mandatory=False, \
                    position=0, argstr="%s")
    in_moving_txt = traits.Str(desc="moving list of diffusion tensor image paths", exists=True, mandatory=False, \
                     position=1, argstr="%s")
    in_mask = traits.Str(desc="mask", exists=True, mandatory=False, position=2, argstr="%s")
    in_numbers = traits.Str(desc='#iters ftol', exists=True, mandatory=False, position=3, argstr="%s")


class DiffeoOutputSpec(TraitedSpec):
    out_file = traits.File(exists=True)
    out_file_xfm = traits.File(exists=True)


class DiffeoTask(CommandLineDtitk):
    input_spec = DiffeoInputSpec
    output_spec = DiffeoOutputSpec
    _cmd = 'dti_diffeomorphic_sn'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file_xfm'] = self.inputs.in_fixed_tensor.replace('.nii.gz','_aff_diffeo.df.nii.gz')
        outputs['out_file'] = self.inputs.in_fixed_tensor.replace('.nii.gz', '_aff_diffeo.nii.gz')
        return outputs


class ComposeXfmInputSpec(CommandLineInputSpec):
    in_df = traits.Str(desc='diffeomorphic file.df.nii.gz', exists=True, mandatory=False, position=1, argstr="-df %s")
    in_aff = traits.Str(desc='affine file.aff', exists=True, mandatory=False, position=0, argstr="-aff %s")
    out_path = traits.Str(desc='output_path', exists=True, mandatory=False, position=2, argstr="-out %s", \
                          name_source="in_df", name_template="%s_comboaff.nii.gz")


class ComposeXfmOutputSpec(TraitedSpec):
    out_file = traits.File(desc='cheese', exists=True)


class ComposeXfmTask(CommandLineDtitk):
    input_spec = ComposeXfmInputSpec
    output_spec = ComposeXfmOutputSpec
    _cmd = 'dfRightComposeAffine'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.in_df.replace('.df.nii.gz', '_combo.df.nii.gz')
        return outputs


class diffeoSymTensor3DVolInputSpec(CommandLineInputSpec):
    in_tensor = traits.Str(desc='moving tensor', exists=True, mandatory=False, position=0, argstr="-in %s")
    in_xfm = traits.Str(desc='transform to apply', exists=True, mandatory=False, position=1, argstr="-trans %s")
    in_target = traits.Str(desc='', exists=True, mandatory=False, position=2, argstr="-target %s")
    out_path = traits.Str(desc='', exists=True, mandatory=False, position=3, argstr="-out %s", \
                          name_source="in_tensor", name_template="%s_diffeoxfmd.nii.gz")


class diffeoSymTensor3DVolOutputSpec(TraitedSpec):
    out_file = traits.File(desc='cheese', exists=True)


class diffeoSymTensor3DVolTask(CommandLineDtitk):
    input_spec = diffeoSymTensor3DVolInputSpec
    output_spec = diffeoSymTensor3DVolOutputSpec
    _cmd = 'deformationSymTensor3DVolume'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_path
        return outputs


class affSymTensor3DVolInputSpec(CommandLineInputSpec):
    in_tensor = traits.Str(desc='moving tensor', exists=True, mandatory=False, position=0, argstr="-in %s")
    in_xfm = traits.Str(desc='transform to apply', exists=True, mandatory=False, position=1, argstr="-trans %s")
    in_target = traits.Str(desc='', exists=True, mandatory=False, position=2, argstr="-target %s")
    out_path = traits.Str(desc='', exists=True, mandatory=False, position=3, argstr="-out %s", \
                         name_source="in_tensor", name_template="%s_affxfmd.nii.gz")


class affSymTensor3DVolOutputSpec(TraitedSpec):
    out_file = traits.File(desc='cheese', exists=True)


class affSymTensor3DVolTask(CommandLineDtitk):
    input_spec = affSymTensor3DVolInputSpec
    output_spec = affSymTensor3DVolOutputSpec
    _cmd = 'affineSymTensor3DVolume'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.out_path)
        return outputs


class affScalarVolInputSpec(CommandLineInputSpec):
    in_volume = traits.Str(desc='moving volume', exists=True, mandatory=False, position=0, argstr="-in %s")
    in_xfm = traits.Str(desc='transform to apply', exists=True, mandatory=False, position=1, argstr="-trans %s")
    in_target = traits.Str(desc='', position=2, argstr="-target %s")
    out_path = traits.Str(desc='', mandatory=False, position=3, argstr="-out %s",
                          name_source="in_volume", name_template="%s_affxfmd.nii.gz")


class affScalarVolOutputSpec(TraitedSpec):
    out_file = traits.File(desc='moved volume', exists=True)


class affScalarVolTask(CommandLineDtitk):
    input_spec = affScalarVolInputSpec
    output_spec = affScalarVolOutputSpec
    _cmd = 'affineScalarVolume'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.out_path)
        return outputs


class diffeoScalarVolInputSpec(CommandLineInputSpec):
    in_volume = traits.Str(desc='moving volume', exists=True, mandatory=False, position=0, argstr="-in %s")
    in_xfm = traits.Str(desc='transform to apply', exists=True, mandatory=False, position=2, argstr="-trans %s")
    in_target = traits.Str(desc='', exists=True, mandatory=False, position=3, argstr="-target %s")
    out_path = traits.Str(desc='', position=1, argstr="-out %s", name_source="in_volume", \
                          name_template="%s_diffeoxfmd.nii.gz")
    in_vsize = traits.Str(desc='', exists=True, mandatory=False, position=4, argstr="-vsize %s")
    in_flip = traits.Str(desc='', exists=True, mandatory=False, position=5, argstr="-flip %s")
    in_type = traits.Str(desc='', exists=True, mandatory=False, position=6, argstr="-type %s")
    in_interp = traits.Str(desc='0 trilin, 1 NN', exists=True, mandatory=False, position=7, argstr="-interp %s")


class diffeoScalarVolOutputSpec(TraitedSpec):
    out_file = traits.File(desc='moved volume', exists=True)


class diffeoScalarVolTask(CommandLineDtitk):
    input_spec = diffeoScalarVolInputSpec
    output_spec = diffeoScalarVolOutputSpec
    _cmd = 'deformationScalarVolume'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_path):
            self.inputs.out_path = fname_presuffix(self.inputs.in_volume, suffix="_diffeoxfmd",newpath=os.path.abspath("."))
        outputs['out_file'] = os.path.abspath(self.inputs.out_path)
        return outputs

'''
#TODO not using these yet... need to be tested

class SVAdjustVoxSpInputSpec(CommandLineInputSpec):
    in_volume = traits.Str(desc="image to resample", exists=True, mandatory=True, position=0, argstr="-in %s")
    in_target = traits.Str(desc='target volume', exists=True, mandatory=False, position=2, \
                            argstr="-target %s")
    in_voxsz = traits.Str(desc='resampled voxel size', exists=True, mandatory=False, position=3, \
                          argstr="-vsize %s")
    out_path = traits.Str(desc='output path', exists=True, mandatory=False, position=1, \
                         argstr="-out %s", name_source="in_volume", name_template='%s_origmvd.nii.gz')
    origin = traits.Str(desc='xyz voxel size', exists=True, mandatory=False, position=4, argstr='-origin %s')


class SVAdjustVoxSpOutputSpec(TraitedSpec):
    out_file = traits.File(exists=True)


class SVAdjustVoxSpTask(CommandLineDtitk):
    input_spec = SVAdjustVoxSpInputSpec
    output_spec = SVAdjustVoxSpOutputSpec
    _cmd = 'SVAdjustVoxelspace'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_path):
            self.inputs.out_path = fname_presuffix(self.inputs.in_volume, suffix="_origmvd", newpath=os.path.abspath("."))
        outputs['out_file'] = os.path.abspath(self.inputs.out_path)
        return outputs
'''

'''
class TVResampleInputSpec(CommandLineInputSpec):
    in_tensor = traits.Str(desc="image to resample", exists=True, mandatory=True, position=0, argstr="-in %s")
    in_arraysz = traits.Str(desc='resampled array size', exists=True, mandatory=False, position=1, \
                            argstr="-size %s")
    in_voxsz = traits.Str(desc='resampled voxel size', exists=True, mandatory=False, position=2, \
                          argstr="-vsize %s")
    out_path = traits.Str(desc='output path', exists=True, mandatory=False, position=3, \
                         argstr="-out %s", name_source="in_volume", name_template="%s_resampled.nii.gz" )


class TVResampleOutputSpec(TraitedSpec):
    out_file = traits.File(exists=True)


class TVResampleTask(CommandLineDtitk):
    input_spec = TVResampleInputSpec
    output_spec = TVResampleOutputSpec
    _cmd = 'TVResample'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.out_path)
        return outputs


class SVResampleInputSpec(CommandLineInputSpec):
    in_volume = traits.Str(desc="image to resample", exists=True, mandatory=True, position=0, argstr="-in %s")
    in_arraysz = traits.Str(desc='resampled array size', exists=True, mandatory=False, position=1, \
                            argstr="-size %s")
    in_voxsz = traits.Str(desc='resampled voxel size', exists=True, mandatory=False, position=2, \
                          argstr="-vsize %s")
    out_path = traits.Str(desc='output path', exists=True, mandatory=False, position=3, \
                         argstr="-out %s", name_source="in_volume", name_template="%s_resampled.nii.gz")


class SVResampleOutputSpec(TraitedSpec):
    out_file = traits.File(exists=True)


class SVResampleTask(CommandLineDtitk):
    input_spec = SVResampleInputSpec
    output_spec = SVResampleOutputSpec
    _cmd = 'SVResample'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_path):
            self.inputs.out_path = fname_presuffix(self.inputs.in_volume, suffix="_resampled",newpath=os.path.abspath("."))
        outputs['out_file'] = os.path.abspath(self.inputs.out_path)
        return outputs

class TVtoolInputSpec(CommandLineInputSpec):
    in_tensor = traits.Str(desc="image to resample", exists=True, mandatory=False, position=0, argstr="-in %s")
    in_flag = traits.Enum('fa', 'tr', 'ad', 'rd', 'pd', 'rgb', exists=True, mandatory=False, position=1, \
                          argstr="-%s", desc='')


class TVtoolOutputSpec(TraitedSpec):
    out_file = traits.File(exists=True)


class TVtoolTask(CommandLineDtitk):
    input_spec = TVtoolInputSpec
    output_spec = TVtoolOutputSpec
    _cmd = 'TVtool'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.in_tensor.replace('.nii.gz', '_'+self.inputs.in_flag+'.nii.gz')
        return outputs


class BinThreshInputSpec(CommandLineInputSpec):
    in_image = traits.Str(desc='', exists=True, mandatory=False, position=0, argstr="%s")
    out_path = traits.Str(desc='', exists=True, mandatory=False, position=1, argstr="%s")
    in_numbers = traits.Str(desc='LB UB inside_value outside_value', exists=True, mandatory=False, position=2, argstr="%s")


class BinThreshOutputSpec(TraitedSpec):
    out_file = traits.File(exists=True)


class BinThreshTask(CommandLineDtitk):
    input_spec = BinThreshInputSpec
    output_spec = BinThreshOutputSpec
    _cmd='BinaryThresholdImageFilter'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_path
        return outputs

'''
'''
    def _gen_filename(self, name):
        print "diffeo worked"
        out_file = self.inputs.out_file
        if not isdefined(out_file) and isdefined(self.inputs.in_volume):
            out_file = self._gen_filename(self.inputs.in_file, suffix='_diffeoxfmd')
        return os.path.abspath(out_file)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_path
        return outputs
'''
