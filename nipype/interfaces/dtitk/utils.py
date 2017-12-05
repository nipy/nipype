__author__ = 'kjordan'

from ..base import TraitedSpec, CommandLineInputSpec, File, \
    traits, isdefined
import os
from .base import CommandLineDtitk


class TVAdjustOriginInputSpec(CommandLineInputSpec):
    in_file = File(desc="image to resample", exists=True, mandatory=True,
                   position=0, argstr="-in %s")
    out_file = traits.Str(genfile=True, desc='output path', position=1,
                          argstr="-out %s")
    origin = traits.Str(desc='xyz voxel size', exists=True, mandatory=False,
                        position=4, argstr='-origin %s')


class TVAdjustOriginOutputSpec(TraitedSpec):
    out_file = traits.Str(exists=True)


class TVAdjustOriginTask(CommandLineDtitk):
    """
    Moves the origin of a tensor volume to zero

    Example
    -------

    >>> import nipype.interfaces.dtitk as dtitk
    >>> node = dtitk.TVAdjustOriginTask()
    >>> node.inputs.in_file = 'diffusion.nii'
    >>> node.run() # doctest: +SKIP
    """

    input_spec = TVAdjustOriginInputSpec
    output_spec = TVAdjustOriginOutputSpec
    _cmd = 'TVAdjustVoxelspace'
    _suffix = "_originzero"

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs["out_file"] = self._gen_fname(self.inputs.in_file,
                                                  suffix=self._suffix,
                                                  ext='.'+'.'.join(
                                                      self.inputs.in_file.
                                                      split(".")[1:]))
        outputs["out_file"] = os.path.abspath(outputs["out_file"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None


class TVAdjustVoxSpInputSpec(CommandLineInputSpec):
    in_file = File(desc="image to resample", exists=True, mandatory=True,
                   position=0, argstr="-in %s")
    out_file = traits.Str(genfile=True, desc='output path', position=1,
                          argstr="-out %s")
    origin = traits.Str(desc='xyz voxel size', exists=True, mandatory=False,
                        position=4, argstr='-origin %s')
    target = traits.Str(desc='target volume', exists=True, mandatory=False,
                        position=2, argstr="-target %s")
    vsize = traits.Str(desc='resampled voxel size', exists=True,
                       mandatory=False, position=3, argstr="-vsize %s")


class TVAdjustVoxSpOutputSpec(TraitedSpec):
    out_file = traits.Str(exists=True)


class TVAdjustVoxSpTask(CommandLineDtitk):
    """
     Adjusts the voxel space of a tensor volume

    Example
    -------

    >>> import nipype.interfaces.dtitk as dtitk
    >>> node = dtitk.TVAdjustVoxSpTask()
    >>> node.inputs.in_file = 'diffusion.nii'
    >>> node.run() # doctest: +SKIP
    """
    input_spec = TVAdjustVoxSpInputSpec
    output_spec = TVAdjustVoxSpOutputSpec
    _cmd = 'TVAdjustVoxelspace'
    _suffix = '_reslice'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs["out_file"] = self._gen_fname(self.inputs.in_file,
                                                  suffix=self._suffix,
                                                  ext='.'+'.'.join(
                                                      self.inputs.in_file.
                                                      split(".")[1:]))
        outputs["out_file"] = os.path.abspath(outputs["out_file"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None


# TODO not using these yet... need to be tested


class SVAdjustVoxSpInputSpec(CommandLineInputSpec):
    in_file = traits.Str(desc="image to resample", exists=True,
                         mandatory=True, position=0, argstr="-in %s")
    in_target = traits.Str(desc='target volume', exists=True, mandatory=False,
                           position=2, argstr="-target %s")
    in_voxsz = traits.Str(desc='resampled voxel size', exists=True,
                          mandatory=False, position=3, argstr="-vsize %s")
    out_file = traits.Str(desc='output path', exists=True, mandatory=False,
                          position=1, argstr="-out %s",
                          name_source="in_file",
                          name_template='%s_origmvd.nii.gz')
    origin = traits.Str(desc='xyz voxel size', exists=True, mandatory=False,
                        position=4, argstr='-origin %s')


class SVAdjustVoxSpOutputSpec(TraitedSpec):
    out_file = traits.File(exists=True)


class SVAdjustVoxSpTask(CommandLineDtitk):
    """
     Adjusts the voxel space of a scalar volume

        Example
        -------

        >>> import nipype.interfaces.dtitk as dtitk
        >>> node = dtitk.SVAdjustVoxSpTask()
        >>> node.inputs.in_file = 'diffusion.nii.gz'
        >>> node.run() # doctest: +SKIP
        """
    input_spec = SVAdjustVoxSpInputSpec
    output_spec = SVAdjustVoxSpOutputSpec
    _cmd = 'SVAdjustVoxelspace'
    _suffix = '_reslice'

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs["out_file"] = self._gen_filename(self.inputs.in_file,
                                                     suffix=self._suffix,
                                                     ext='.' + '.'.join(
                                                      self.inputs.in_file.
                                                      split(".")[1:]))
        outputs["out_file"] = os.path.abspath(outputs["out_file"])
        return outputs


class TVResampleInputSpec(CommandLineInputSpec):
    in_file = traits.Str(desc="image to resample", exists=True,
                         mandatory=True, position=0, argstr="-in %s")
    in_arraysz = traits.Str(desc='resampled array size', exists=True,
                            mandatory=False, position=1, argstr="-size %s")
    in_voxsz = traits.Str(desc='resampled voxel size', exists=True,
                          mandatory=False, position=2, argstr="-vsize %s")
    out_file = traits.Str(desc='output path', exists=True, mandatory=False,
                          position=3, argstr="-out %s",
                          name_source="in_file",
                          name_template="%s_resampled.nii.gz")


class TVResampleOutputSpec(TraitedSpec):
    out_file = traits.File(exists=True)


class TVResampleTask(CommandLineDtitk):
    """
    Resamples a tensor volume

        Example
        -------

        >>> import nipype.interfaces.dtitk as dtitk
        >>> node = dtitk.TVResampleTask()
        >>> node.inputs.in_file = 'diffusion.nii.gz'
        >>> node.run() # doctest: +SKIP
        """
    input_spec = TVResampleInputSpec
    output_spec = TVResampleOutputSpec
    _cmd = 'TVResample'
    _suffix = '_resampled'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs["out_file"] = self._gen_fname(self.inputs.in_file,
                                                  suffix=self._suffix,
                                                  ext='.' + '.'.join(
                                                      self.inputs.in_file.
                                                      split(".")[1:]))
        outputs["out_file"] = os.path.abspath(outputs["out_file"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None


class SVResampleInputSpec(CommandLineInputSpec):
    in_file = traits.Str(desc="image to resample", exists=True,
                         mandatory=True, position=0, argstr="-in %s")
    in_arraysz = traits.Str(desc='resampled array size', exists=True,
                            mandatory=False, position=1,
                            argstr="-size %s")
    in_voxsz = traits.Str(desc='resampled voxel size', exists=True,
                          mandatory=False, position=2, argstr="-vsize %s")
    out_file = traits.Str(desc='output path', exists=True, mandatory=False,
                          position=3, argstr="-out %s",
                          name_source="in_file",
                          name_template="%s_resampled.nii.gz")


class SVResampleOutputSpec(TraitedSpec):
    out_file = traits.File(exists=True)


class SVResampleTask(CommandLineDtitk):
    """
    Resamples a scalar volume

        Example
        -------

        >>> import nipype.interfaces.dtitk as dtitk
        >>> node = dtitk.SVResampleTask()
        >>> node.inputs.in_file = 'diffusion.nii'
        >>> node.run() # doctest: +SKIP
        """
    input_spec = SVResampleInputSpec
    output_spec = SVResampleOutputSpec
    _cmd = 'SVResample'
    _suffix = '_resampled'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs["out_file"] = self._gen_fname(self.inputs.in_file,
                                                  suffix=self._suffix,
                                                  ext='.' + '.'.join(
                                                      self.inputs.in_file.
                                                      split(".")[1:]))
        outputs["out_file"] = os.path.abspath(outputs["out_file"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None


class TVtoolInputSpec(CommandLineInputSpec):
    in_file = traits.Str(desc="image to resample", exists=True,
                         mandatory=False, position=0, argstr="-in %s")
    in_flag = traits.Enum('fa', 'tr', 'ad', 'rd', 'pd', 'rgb', exists=True,
                          mandatory=False, position=1, argstr="-%s", desc='')


class TVtoolOutputSpec(TraitedSpec):
    out_file = traits.File(exists=True)


class TVtoolTask(CommandLineDtitk):
    """
    Calculates a tensor metric volume from a tensor volume

        Example
        -------

        >>> import nipype.interfaces.dtitk as dtitk
        >>> node = dtitk.TVtoolTask()
        >>> node.inputs.in_file = 'diffusion.nii'
        >>> node.inputs.in_flag = 'fa'
        >>> node.run() # doctest: +SKIP
        """
    input_spec = TVtoolInputSpec
    output_spec = TVtoolOutputSpec
    _cmd = 'TVtool'

    def _list_outputs(self):
        _suffix = self.inputs.in_flag
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs["out_file"] = self._gen_fname(self.inputs.in_file,
                                                  suffix=_suffix,
                                                  ext='.' + '.'.join(
                                                      self.inputs.in_file.
                                                      split(".")[1:]))
        outputs["out_file"] = os.path.abspath(outputs["out_file"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None


class BinThreshInputSpec(CommandLineInputSpec):
    in_file = traits.Str(desc='', exists=True, mandatory=False, position=0,
                         argstr="%s")
    out_file = traits.Str(desc='', exists=True, mandatory=False, position=1,
                          argstr="%s")
    in_numbers = traits.Str(desc='LB UB inside_value outside_value',
                            exists=True, mandatory=False, position=2,
                            argstr="%s")


class BinThreshOutputSpec(TraitedSpec):
    out_file = traits.File(exists=True)


class BinThreshTask(CommandLineDtitk):
    """
    Binarizes an image based on parameters

        Example
        -------

        >>> import nipype.interfaces.dtitk as dtitk
        >>> node = dtitk.BinThreshTask()
        >>> node.inputs.in_file = 'diffusion.nii'
        >>> node.inputs.in_numbers = '0 100 1 0'
        >>> node.run() # doctest: +SKIP
        """

    input_spec = BinThreshInputSpec
    output_spec = BinThreshOutputSpec
    _cmd = 'BinaryThresholdImageFilter'
    _suffix = '_bin'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs["out_file"] = self._gen_fname(self.inputs.in_file,
                                                  suffix=self._suffix,
                                                  ext='.'+'.'.join(
                                                    self.inputs.in_file.
                                                    split(".")[1:]))
        outputs["out_file"] = os.path.abspath(outputs["out_file"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None
