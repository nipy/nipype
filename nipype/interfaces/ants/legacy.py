# -*- coding: utf-8 -*-
"""ANTS Legacy Interfaces

These interfaces are for programs that have been deprecated by ANTs, but
are preserved for backwards compatibility.
"""

from builtins import range

import os
from glob import glob

from .base import ANTSCommand, ANTSCommandInputSpec
from ..base import TraitedSpec, File, traits, isdefined, OutputMultiPath
from ...utils.filemanip import split_filename


class antsIntroductionInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3,
        2,
        argstr="-d %d",
        usedefault=True,
        desc="image dimension (2 or 3)",
        position=1,
    )
    reference_image = File(
        exists=True,
        argstr="-r %s",
        desc="template file to warp to",
        mandatory=True,
        copyfile=True,
    )
    input_image = File(
        exists=True,
        argstr="-i %s",
        desc="input image to warp to template",
        mandatory=True,
        copyfile=False,
    )
    force_proceed = traits.Bool(
        argstr="-f 1",
        desc=("force script to proceed even if headers " "may be incompatible"),
    )
    inverse_warp_template_labels = traits.Bool(
        argstr="-l",
        desc=(
            "Applies inverse warp to the template labels "
            "to estimate label positions in target space (use "
            "for template-based segmentation)"
        ),
    )
    max_iterations = traits.List(
        traits.Int,
        argstr="-m %s",
        sep="x",
        desc=(
            "maximum number of iterations (must be "
            "list of integers in the form [J,K,L...]: "
            "J = coarsest resolution iterations, K = "
            "middle resolution interations, L = fine "
            "resolution iterations"
        ),
    )
    bias_field_correction = traits.Bool(
        argstr="-n 1", desc=("Applies bias field correction to moving " "image")
    )
    similarity_metric = traits.Enum(
        "PR",
        "CC",
        "MI",
        "MSQ",
        argstr="-s %s",
        desc=(
            "Type of similartiy metric used for registration "
            "(CC = cross correlation, MI = mutual information, "
            "PR = probability mapping, MSQ = mean square difference)"
        ),
    )
    transformation_model = traits.Enum(
        "GR",
        "EL",
        "SY",
        "S2",
        "EX",
        "DD",
        "RI",
        "RA",
        argstr="-t %s",
        usedefault=True,
        desc=(
            "Type of transofmration model used for registration "
            "(EL = elastic transformation model, SY = SyN with time, "
            "arbitrary number of time points, S2 =  SyN with time "
            "optimized for 2 time points, GR = greedy SyN, EX = "
            "exponential, DD = diffeomorphic demons style exponential "
            "mapping, RI = purely rigid, RA = affine rigid"
        ),
    )
    out_prefix = traits.Str(
        "ants_",
        argstr="-o %s",
        usedefault=True,
        desc=("Prefix that is prepended to all output " "files (default = ants_)"),
    )
    quality_check = traits.Bool(
        argstr="-q 1", desc="Perform a quality check of the result"
    )


class antsIntroductionOutputSpec(TraitedSpec):
    affine_transformation = File(exists=True, desc="affine (prefix_Affine.txt)")
    warp_field = File(exists=True, desc="warp field (prefix_Warp.nii)")
    inverse_warp_field = File(
        exists=True, desc="inverse warp field (prefix_InverseWarp.nii)"
    )
    input_file = File(exists=True, desc="input image (prefix_repaired.nii)")
    output_file = File(exists=True, desc="output image (prefix_deformed.nii)")


class antsIntroduction(ANTSCommand):
    """Uses ANTS to generate matrices to warp data from one space to another.

    Examples
    --------

    >>> from nipype.interfaces.ants.legacy import antsIntroduction
    >>> warp = antsIntroduction()
    >>> warp.inputs.reference_image = 'Template_6.nii'
    >>> warp.inputs.input_image = 'structural.nii'
    >>> warp.inputs.max_iterations = [30,90,20]
    >>> warp.cmdline
    'antsIntroduction.sh -d 3 -i structural.nii -m 30x90x20 -o ants_ -r Template_6.nii -t GR'

    """

    _cmd = "antsIntroduction.sh"
    input_spec = antsIntroductionInputSpec
    output_spec = antsIntroductionOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        transmodel = self.inputs.transformation_model

        # When transform is set as 'RI'/'RA', wrap fields should not be expected
        # The default transformation is GR, which outputs the wrap fields
        if not isdefined(transmodel) or (
            isdefined(transmodel) and transmodel not in ["RI", "RA"]
        ):
            outputs["warp_field"] = os.path.join(
                os.getcwd(), self.inputs.out_prefix + "Warp.nii.gz"
            )
            outputs["inverse_warp_field"] = os.path.join(
                os.getcwd(), self.inputs.out_prefix + "InverseWarp.nii.gz"
            )

        outputs["affine_transformation"] = os.path.join(
            os.getcwd(), self.inputs.out_prefix + "Affine.txt"
        )
        outputs["input_file"] = os.path.join(
            os.getcwd(), self.inputs.out_prefix + "repaired.nii.gz"
        )
        outputs["output_file"] = os.path.join(
            os.getcwd(), self.inputs.out_prefix + "deformed.nii.gz"
        )

        return outputs


# How do we make a pass through so that GenWarpFields is just an alias for  antsIntroduction ?


class GenWarpFields(antsIntroduction):
    pass


class buildtemplateparallelInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3,
        2,
        4,
        argstr="-d %d",
        usedefault=True,
        desc="image dimension (2, 3 or 4)",
        position=1,
    )
    out_prefix = traits.Str(
        "antsTMPL_",
        argstr="-o %s",
        usedefault=True,
        desc=("Prefix that is prepended to all output " "files (default = antsTMPL_)"),
    )
    in_files = traits.List(
        File(exists=True),
        mandatory=True,
        desc="list of images to generate template from",
        argstr="%s",
        position=-1,
    )
    parallelization = traits.Enum(
        0,
        1,
        2,
        argstr="-c %d",
        usedefault=True,
        desc=(
            "control for parallel processing (0 = "
            "serial, 1 = use PBS, 2 = use PEXEC, 3 = "
            "use Apple XGrid"
        ),
    )
    gradient_step_size = traits.Float(
        argstr="-g %f",
        desc=("smaller magnitude results in " "more cautious steps (default = " ".25)"),
    )
    iteration_limit = traits.Int(
        4, argstr="-i %d", usedefault=True, desc="iterations of template construction"
    )
    num_cores = traits.Int(
        argstr="-j %d",
        requires=["parallelization"],
        desc=(
            "Requires parallelization = 2 (PEXEC). " "Sets number of cpu cores to use"
        ),
    )
    max_iterations = traits.List(
        traits.Int,
        argstr="-m %s",
        sep="x",
        desc=(
            "maximum number of iterations (must be "
            "list of integers in the form [J,K,L...]: "
            "J = coarsest resolution iterations, K = "
            "middle resolution interations, L = fine "
            "resolution iterations"
        ),
    )
    bias_field_correction = traits.Bool(
        argstr="-n 1", desc=("Applies bias field correction to moving " "image")
    )
    rigid_body_registration = traits.Bool(
        argstr="-r 1",
        desc=(
            "registers inputs before creating template "
            "(useful if no initial template available)"
        ),
    )
    similarity_metric = traits.Enum(
        "PR",
        "CC",
        "MI",
        "MSQ",
        argstr="-s %s",
        desc=(
            "Type of similartiy metric used for registration "
            "(CC = cross correlation, MI = mutual information, "
            "PR = probability mapping, MSQ = mean square difference)"
        ),
    )
    transformation_model = traits.Enum(
        "GR",
        "EL",
        "SY",
        "S2",
        "EX",
        "DD",
        argstr="-t %s",
        usedefault=True,
        desc=(
            "Type of transofmration model used for registration "
            "(EL = elastic transformation model, SY = SyN with time, "
            "arbitrary number of time points, S2 =  SyN with time "
            "optimized for 2 time points, GR = greedy SyN, EX = "
            "exponential, DD = diffeomorphic demons style exponential "
            "mapping"
        ),
    )
    use_first_as_target = traits.Bool(
        desc=(
            "uses first volume as target of "
            "all inputs. When not used, an "
            "unbiased average image is used "
            "to start."
        )
    )


class buildtemplateparallelOutputSpec(TraitedSpec):
    final_template_file = File(exists=True, desc="final ANTS template")
    template_files = OutputMultiPath(
        File(exists=True), desc="Templates from different stages of iteration"
    )
    subject_outfiles = OutputMultiPath(
        File(exists=True),
        desc=(
            "Outputs for each input image. Includes warp "
            "field, inverse warp, Affine, original image "
            "(repaired) and warped image (deformed)"
        ),
    )


class buildtemplateparallel(ANTSCommand):
    """Generate a optimal average template

    .. warning::

      This can take a VERY long time to complete

    Examples
    --------

    >>> from nipype.interfaces.ants.legacy import buildtemplateparallel
    >>> tmpl = buildtemplateparallel()
    >>> tmpl.inputs.in_files = ['T1.nii', 'structural.nii']
    >>> tmpl.inputs.max_iterations = [30, 90, 20]
    >>> tmpl.cmdline
    'buildtemplateparallel.sh -d 3 -i 4 -m 30x90x20 -o antsTMPL_ -c 0 -t GR T1.nii structural.nii'

    """

    _cmd = "buildtemplateparallel.sh"
    input_spec = buildtemplateparallelInputSpec
    output_spec = buildtemplateparallelOutputSpec

    def _format_arg(self, opt, spec, val):
        if opt == "num_cores":
            if self.inputs.parallelization == 2:
                return "-j " + str(val)
            else:
                return ""
        if opt == "in_files":
            if self.inputs.use_first_as_target:
                start = "-z "
            else:
                start = ""
            return start + " ".join(name for name in val)
        return super(buildtemplateparallel, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["template_files"] = []
        for i in range(len(glob(os.path.realpath("*iteration*")))):
            temp = os.path.realpath(
                "%s_iteration_%d/%stemplate.nii.gz"
                % (self.inputs.transformation_model, i, self.inputs.out_prefix)
            )
            os.rename(
                temp,
                os.path.realpath(
                    "%s_iteration_%d/%stemplate_i%d.nii.gz"
                    % (self.inputs.transformation_model, i, self.inputs.out_prefix, i)
                ),
            )
            file_ = "%s_iteration_%d/%stemplate_i%d.nii.gz" % (
                self.inputs.transformation_model,
                i,
                self.inputs.out_prefix,
                i,
            )

            outputs["template_files"].append(os.path.realpath(file_))
            outputs["final_template_file"] = os.path.realpath(
                "%stemplate.nii.gz" % self.inputs.out_prefix
            )
        outputs["subject_outfiles"] = []
        for filename in self.inputs.in_files:
            _, base, _ = split_filename(filename)
            temp = glob(os.path.realpath("%s%s*" % (self.inputs.out_prefix, base)))
            for file_ in temp:
                outputs["subject_outfiles"].append(file_)
        return outputs
