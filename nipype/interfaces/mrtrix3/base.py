# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
# -*- coding: utf-8 -*-

from ... import logging, LooseVersion
from ...utils.filemanip import which
from ..base import (
    CommandLineInputSpec,
    CommandLine,
    traits,
    File,
    isdefined,
    PackageInfo,
)

iflogger = logging.getLogger("nipype.interface")


class Info(PackageInfo):
    version_cmd = "mrconvert --version"

    @staticmethod
    def parse_version(raw_info):
        # info is like: "== mrconvert 0.3.15-githash"
        for line in raw_info.splitlines():
            if line.startswith("== mrconvert "):
                v_string = line.split()[2]
                break
        else:
            return None

        # -githash may or may not be appended
        v_string = v_string.split("-")[0]

        return ".".join(v_string.split(".")[:3])

    @classmethod
    def looseversion(cls):
        """Return a comparable version object

        If no version found, use LooseVersion('0.0.0')
        """
        return LooseVersion(cls.version() or "0.0.0")


class MRTrix3BaseInputSpec(CommandLineInputSpec):
    nthreads = traits.Int(
        argstr="-nthreads %d",
        desc="number of threads. if zero, the number" " of available cpus will be used",
        nohash=True,
    )
    # DW gradient table import options
    grad_file = File(
        exists=True,
        argstr="-grad %s",
        desc="dw gradient scheme (MRTrix format)",
        xor=["grad_fsl"],
    )
    grad_fsl = traits.Tuple(
        File(exists=True),
        File(exists=True),
        argstr="-fslgrad %s %s",
        desc="(bvecs, bvals) dw gradient scheme (FSL format)",
        xor=["grad_file"],
    )
    bval_scale = traits.Enum(
        "yes",
        "no",
        argstr="-bvalue_scaling %s",
        desc="specifies whether the b - values should be scaled by the square"
        " of the corresponding DW gradient norm, as often required for "
        "multishell or DSI DW acquisition schemes. The default action "
        "can also be set in the MRtrix config file, under the "
        "BValueScaling entry. Valid choices are yes / no, true / "
        "false, 0 / 1 (default: true).",
    )

    in_bvec = File(
        exists=True, argstr="-fslgrad %s %s", desc="bvecs file in FSL format"
    )
    in_bval = File(exists=True, desc="bvals file in FSL format")
    out_bvec = File(
        exists=False,
        argstr="-export_grad_fsl %s %s",
        desc="export bvec file in FSL format",
    )
    out_bval = File(
        exists=False,
        desc="export bval file in FSL format",
    )


class MRTrix3Base(CommandLine):
    def _format_arg(self, name, trait_spec, value):
        if name == "nthreads" and value == 0:
            value = 1
            try:
                from multiprocessing import cpu_count

                value = cpu_count()
            except:
                iflogger.warning("Number of threads could not be computed")
                pass
            return trait_spec.argstr % value

        if name == "in_bvec":
            return trait_spec.argstr % (value, self.inputs.in_bval)
        if name == "out_bvec":
            return trait_spec.argstr % (value, self.inputs.out_bval)

        return super(MRTrix3Base, self)._format_arg(name, trait_spec, value)

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []

        try:
            if isdefined(self.inputs.grad_file) or isdefined(self.inputs.grad_fsl):
                skip += ["in_bvec", "in_bval"]

            is_bvec = isdefined(self.inputs.in_bvec)
            is_bval = isdefined(self.inputs.in_bval)
            if is_bvec or is_bval:
                if not is_bvec or not is_bval:
                    raise RuntimeError(
                        "If using bvecs and bvals inputs, both" "should be defined"
                    )
                skip += ["in_bval"]
        except AttributeError:
            pass

        return super(MRTrix3Base, self)._parse_inputs(skip=skip)

    @property
    def version(self):
        return Info.version()
