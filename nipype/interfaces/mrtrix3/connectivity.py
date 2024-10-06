# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
# -*- coding: utf-8 -*-

import os
import os.path as op

from ..base import CommandLineInputSpec, traits, TraitedSpec, File, isdefined
from .base import MRTrix3Base


class BuildConnectomeInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True, argstr="%s", mandatory=True, position=-3, desc="input tractography"
    )
    in_parc = File(exists=True, argstr="%s", position=-2, desc="parcellation file")
    out_file = File(
        "connectome.csv",
        argstr="%s",
        mandatory=True,
        position=-1,
        usedefault=True,
        desc="output file after processing",
    )

    nthreads = traits.Int(
        argstr="-nthreads %d",
        desc="number of threads. if zero, the number of available cpus will be used",
        nohash=True,
    )

    vox_lookup = traits.Bool(
        argstr="-assignment_voxel_lookup",
        desc="use a simple voxel lookup value at each streamline endpoint",
    )
    search_radius = traits.Float(
        argstr="-assignment_radial_search %f",
        desc="perform a radial search from each streamline endpoint to locate "
        "the nearest node. Argument is the maximum radius in mm; if no node is"
        " found within this radius, the streamline endpoint is not assigned to"
        " any node.",
    )
    search_reverse = traits.Float(
        argstr="-assignment_reverse_search %f",
        desc="traverse from each streamline endpoint inwards along the "
        "streamline, in search of the last node traversed by the streamline. "
        "Argument is the maximum traversal length in mm (set to 0 to allow "
        "search to continue to the streamline midpoint).",
    )
    search_forward = traits.Float(
        argstr="-assignment_forward_search %f",
        desc="project the streamline forwards from the endpoint in search of a"
        "parcellation node voxel. Argument is the maximum traversal length in "
        "mm.",
    )

    metric = traits.Enum(
        "count",
        "meanlength",
        "invlength",
        "invnodevolume",
        "mean_scalar",
        "invlength_invnodevolume",
        argstr="-metric %s",
        desc="specify the edge weight metric",
    )

    in_scalar = File(
        exists=True,
        argstr="-image %s",
        desc="provide the associated image for the mean_scalar metric",
    )

    in_weights = File(
        exists=True,
        argstr="-tck_weights_in %s",
        desc="specify a text scalar file containing the streamline weights",
    )

    keep_unassigned = traits.Bool(
        argstr="-keep_unassigned",
        desc="By default, the program discards the"
        " information regarding those streamlines that are not successfully "
        "assigned to a node pair. Set this option to keep these values (will "
        "be the first row/column in the output matrix)",
    )
    zero_diagonal = traits.Bool(
        argstr="-zero_diagonal",
        desc="set all diagonal entries in the matrix "
        "to zero (these represent streamlines that connect to the same node at"
        " both ends)",
    )


class BuildConnectomeOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="the output response file")


class BuildConnectome(MRTrix3Base):
    """
    Generate a connectome matrix from a streamlines file and a node
    parcellation image

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> mat = mrt.BuildConnectome()
    >>> mat.inputs.in_file = 'tracks.tck'
    >>> mat.inputs.in_parc = 'aparc+aseg.nii'
    >>> mat.cmdline                               # doctest: +ELLIPSIS
    'tck2connectome tracks.tck aparc+aseg.nii connectome.csv'
    >>> mat.run()                                 # doctest: +SKIP
    """

    _cmd = "tck2connectome"
    input_spec = BuildConnectomeInputSpec
    output_spec = BuildConnectomeOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs


class LabelConfigInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-3,
        desc="input anatomical image",
    )
    in_config = File(
        exists=True, argstr="%s", position=-2, desc="connectome configuration file"
    )
    out_file = File(
        "parcellation.mif",
        argstr="%s",
        mandatory=True,
        position=-1,
        usedefault=True,
        desc="output file after processing",
    )

    lut_basic = File(
        argstr="-lut_basic %s",
        desc="get information from "
        "a basic lookup table consisting of index / name pairs",
    )
    lut_fs = File(
        argstr="-lut_freesurfer %s",
        desc="get information from "
        'a FreeSurfer lookup table(typically "FreeSurferColorLUT'
        '.txt")',
    )
    lut_aal = File(
        argstr="-lut_aal %s",
        desc="get information from the AAL "
        'lookup table (typically "ROI_MNI_V4.txt")',
    )
    lut_itksnap = File(
        argstr="-lut_itksnap %s",
        desc="get information from an"
        " ITK - SNAP lookup table(this includes the IIT atlas "
        'file "LUT_GM.txt")',
    )
    spine = File(
        argstr="-spine %s",
        desc="provide a manually-defined "
        "segmentation of the base of the spine where the streamlines"
        " terminate, so that this can become a node in the connection"
        " matrix.",
    )
    nthreads = traits.Int(
        argstr="-nthreads %d",
        desc="number of threads. if zero, the number of available cpus will be used",
        nohash=True,
    )


class LabelConfigOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="the output response file")


class LabelConfig(MRTrix3Base):
    """
    Re-configure parcellation to be incrementally defined.

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> labels = mrt.LabelConfig()
    >>> labels.inputs.in_file = 'aparc+aseg.nii'
    >>> labels.inputs.in_config = 'mrtrix3_labelconfig.txt'
    >>> labels.cmdline                               # doctest: +ELLIPSIS
    'labelconfig aparc+aseg.nii mrtrix3_labelconfig.txt parcellation.mif'
    >>> labels.run()                                 # doctest: +SKIP
    """

    _cmd = "labelconfig"
    input_spec = LabelConfigInputSpec
    output_spec = LabelConfigOutputSpec

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []

        if not isdefined(self.inputs.in_config):
            from shutil import which

            path = which(self._cmd)
            if path is None:
                path = os.getenv("MRTRIX3_HOME", "/opt/mrtrix3")
            else:
                path = op.dirname(op.dirname(path))

            self.inputs.in_config = op.join(
                path,
                "src/dwi/tractography/connectomics/example_configs/fs_default.txt",
            )

        return super()._parse_inputs(skip=skip)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs


class LabelConvertInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-4,
        desc="input anatomical image",
    )
    in_lut = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-3,
        desc="get information from "
        "a basic lookup table consisting of index / name pairs",
    )
    in_config = File(
        exists=True, argstr="%s", position=-2, desc="connectome configuration file"
    )
    out_file = File(
        "parcellation.mif",
        argstr="%s",
        mandatory=True,
        position=-1,
        usedefault=True,
        desc="output file after processing",
    )
    spine = File(
        argstr="-spine %s",
        desc="provide a manually-defined "
        "segmentation of the base of the spine where the streamlines"
        " terminate, so that this can become a node in the connection"
        " matrix.",
    )
    num_threads = traits.Int(
        argstr="-nthreads %d",
        desc="number of threads. if zero, the number of available cpus will be used",
        nohash=True,
    )


class LabelConvertOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="the output response file")


class LabelConvert(MRTrix3Base):
    """
    Re-configure parcellation to be incrementally defined.

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> labels = mrt.LabelConvert()
    >>> labels.inputs.in_file = 'aparc+aseg.nii'
    >>> labels.inputs.in_config = 'mrtrix3_labelconfig.txt'
    >>> labels.inputs.in_lut = 'FreeSurferColorLUT.txt'
    >>> labels.cmdline
    'labelconvert aparc+aseg.nii FreeSurferColorLUT.txt mrtrix3_labelconfig.txt parcellation.mif'
    >>> labels.run()                                 # doctest: +SKIP
    """

    _cmd = "labelconvert"
    input_spec = LabelConvertInputSpec
    output_spec = LabelConvertOutputSpec

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []

        if not isdefined(self.inputs.in_config):
            from nipype.utils.filemanip import which

            path = which(self._cmd)
            if path is None:
                path = os.getenv("MRTRIX3_HOME", "/opt/mrtrix3")
            else:
                path = op.dirname(op.dirname(path))

            self.inputs.in_config = op.join(
                path,
                "src/dwi/tractography/connectomics/example_configs/fs_default.txt",
            )

        return super()._parse_inputs(skip=skip)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs
