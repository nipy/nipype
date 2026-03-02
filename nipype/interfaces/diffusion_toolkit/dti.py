# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provides interfaces to various commands provided by diffusion toolkit"""
import os
import re

from ...utils.filemanip import fname_presuffix, split_filename, copyfile
from ..base import (
    TraitedSpec,
    File,
    traits,
    CommandLine,
    CommandLineInputSpec,
    isdefined,
)

__docformat__ = "restructuredtext"


class DTIReconInputSpec(CommandLineInputSpec):
    DWI = File(
        desc="Input diffusion volume",
        argstr="%s",
        exists=True,
        mandatory=True,
        position=1,
    )
    out_prefix = traits.Str(
        "dti", desc="Output file prefix", argstr="%s", usedefault=True, position=2
    )
    output_type = traits.Enum(
        "nii",
        "analyze",
        "ni1",
        "nii.gz",
        argstr="-ot %s",
        desc="output file type",
        usedefault=True,
    )
    bvecs = File(exists=True, desc="b vectors file", argstr="-gm %s", mandatory=True)
    bvals = File(exists=True, desc="b values file", mandatory=True)
    n_averages = traits.Int(desc="Number of averages", argstr="-nex %s")
    image_orientation_vectors = traits.List(
        traits.Float(),
        minlen=6,
        maxlen=6,
        desc="""\
Specify image orientation vectors. if just one argument given,
will treat it as filename and read the orientation vectors from
the file. If 6 arguments are given, will treat them as 6 float
numbers and construct the 1st and 2nd vector and calculate the 3rd
one automatically.
This information will be used to determine image orientation,
as well as to adjust gradient vectors with oblique angle when.""",
        argstr="-iop %f",
    )
    oblique_correction = traits.Bool(
        desc="""\
When oblique angle(s) applied, some SIEMENS DTI protocols do not
adjust gradient accordingly, thus it requires adjustment for correct
diffusion tensor calculation""",
        argstr="-oc",
    )
    b0_threshold = traits.Float(
        desc="""\
Program will use b0 image with the given threshold to mask out high
background of fa/adc maps. by default it will calculate threshold
automatically. but if it failed, you need to set it manually.""",
        argstr="-b0_th",
    )


class DTIReconOutputSpec(TraitedSpec):
    ADC = File(exists=True)
    B0 = File(exists=True)
    L1 = File(exists=True)
    L2 = File(exists=True)
    L3 = File(exists=True)
    exp = File(exists=True)
    FA = File(exists=True)
    FA_color = File(exists=True)
    tensor = File(exists=True)
    V1 = File(exists=True)
    V2 = File(exists=True)
    V3 = File(exists=True)


class DTIRecon(CommandLine):
    """Use dti_recon to generate tensors and other maps"""

    input_spec = DTIReconInputSpec
    output_spec = DTIReconOutputSpec

    _cmd = "dti_recon"

    def _create_gradient_matrix(self, bvecs_file, bvals_file):
        _gradient_matrix_file = "gradient_matrix.txt"
        with open(bvals_file) as fbvals:
            bvals = fbvals.readline().strip().split()
        with open(bvecs_file) as fbvecs:
            bvecs_x = fbvecs.readline().split()
            bvecs_y = fbvecs.readline().split()
            bvecs_z = fbvecs.readline().split()

        with open(_gradient_matrix_file, "w") as gradient_matrix_f:
            for i in range(len(bvals)):
                gradient_matrix_f.write(
                    f"{bvecs_x[i]}, {bvecs_y[i]}, {bvecs_z[i]}, {bvals[i]}\n"
                )
        return _gradient_matrix_file

    def _format_arg(self, name, spec, value):
        if name == "bvecs":
            new_val = self._create_gradient_matrix(self.inputs.bvecs, self.inputs.bvals)
            return super()._format_arg("bvecs", spec, new_val)
        return super()._format_arg(name, spec, value)

    def _list_outputs(self):
        out_prefix = self.inputs.out_prefix
        output_type = self.inputs.output_type

        outputs = self.output_spec().get()
        outputs["ADC"] = os.path.abspath(
            fname_presuffix("", prefix=out_prefix, suffix="_adc." + output_type)
        )
        outputs["B0"] = os.path.abspath(
            fname_presuffix("", prefix=out_prefix, suffix="_b0." + output_type)
        )
        outputs["L1"] = os.path.abspath(
            fname_presuffix("", prefix=out_prefix, suffix="_e1." + output_type)
        )
        outputs["L2"] = os.path.abspath(
            fname_presuffix("", prefix=out_prefix, suffix="_e2." + output_type)
        )
        outputs["L3"] = os.path.abspath(
            fname_presuffix("", prefix=out_prefix, suffix="_e3." + output_type)
        )
        outputs["exp"] = os.path.abspath(
            fname_presuffix("", prefix=out_prefix, suffix="_exp." + output_type)
        )
        outputs["FA"] = os.path.abspath(
            fname_presuffix("", prefix=out_prefix, suffix="_fa." + output_type)
        )
        outputs["FA_color"] = os.path.abspath(
            fname_presuffix("", prefix=out_prefix, suffix="_fa_color." + output_type)
        )
        outputs["tensor"] = os.path.abspath(
            fname_presuffix("", prefix=out_prefix, suffix="_tensor." + output_type)
        )
        outputs["V1"] = os.path.abspath(
            fname_presuffix("", prefix=out_prefix, suffix="_v1." + output_type)
        )
        outputs["V2"] = os.path.abspath(
            fname_presuffix("", prefix=out_prefix, suffix="_v2." + output_type)
        )
        outputs["V3"] = os.path.abspath(
            fname_presuffix("", prefix=out_prefix, suffix="_v3." + output_type)
        )

        return outputs


class DTITrackerInputSpec(CommandLineInputSpec):
    tensor_file = File(exists=True, desc="reconstructed tensor file")
    input_type = traits.Enum(
        "nii",
        "analyze",
        "ni1",
        "nii.gz",
        desc="""\
Input and output file type. Accepted values are:

* analyze -> analyze format 7.5
* ni1     -> nifti format saved in separate .hdr and .img file
* nii     -> nifti format with one .nii file
* nii.gz  -> nifti format with compression

Default type is 'nii'
""",
        argstr="-it %s",
    )
    tracking_method = traits.Enum(
        "fact",
        "rk2",
        "tl",
        "sl",
        desc="""\
Tracking algorithm.

* fact -> use FACT method for tracking. This is the default method.
* rk2  -> use 2nd order Runge-Kutta method for tracking.
* tl   -> use tensorline method for tracking.
* sl   -> use interpolated streamline method with fixed step-length

""",
        argstr="-%s",
    )
    step_length = traits.Float(
        desc="""\
Step length, in the unit of minimum voxel size.
default value is 0.5 for interpolated streamline method
and 0.1 for other methods""",
        argstr="-l %f",
    )
    angle_threshold = traits.Float(
        desc="set angle threshold. default value is 35 degree", argstr="-at %f"
    )
    angle_threshold_weight = traits.Float(
        desc="set angle threshold weighting factor. weighting will be applied "
        "on top of the angle_threshold",
        argstr="-atw %f",
    )
    random_seed = traits.Int(
        desc="use random location in a voxel instead of the center of the voxel "
        "to seed. can also define number of seed per voxel. default is 1",
        argstr="-rseed %d",
    )
    invert_x = traits.Bool(desc="invert x component of the vector", argstr="-ix")
    invert_y = traits.Bool(desc="invert y component of the vector", argstr="-iy")
    invert_z = traits.Bool(desc="invert z component of the vector", argstr="-iz")
    swap_xy = traits.Bool(desc="swap x & y vectors while tracking", argstr="-sxy")
    swap_yz = traits.Bool(desc="swap y & z vectors while tracking", argstr="-syz")
    swap_zx = traits.Bool(desc="swap x & z vectors while tracking", argstr="-szx")
    mask1_file = File(
        desc="first mask image", mandatory=True, argstr="-m %s", position=2
    )
    mask1_threshold = traits.Float(
        desc="threshold value for the first mask image, if not given, the program will "
        "try automatically find the threshold",
        position=3,
    )
    mask2_file = File(desc="second mask image", argstr="-m2 %s", position=4)
    mask2_threshold = traits.Float(
        desc="threshold value for the second mask image, if not given, the program will "
        "try automatically find the threshold",
        position=5,
    )
    input_data_prefix = traits.Str(
        "dti",
        desc="for internal naming use only",
        position=0,
        argstr="%s",
        usedefault=True,
    )
    output_file = File(
        "tracks.trk", "file containing tracks", argstr="%s", position=1, usedefault=True
    )
    output_mask = File(
        desc="output a binary mask file in analyze format", argstr="-om %s"
    )
    primary_vector = traits.Enum(
        "v2",
        "v3",
        desc="which vector to use for fibre tracking: v2 or v3. If not set use v1",
        argstr="-%s",
    )


class DTITrackerOutputSpec(TraitedSpec):
    track_file = File(exists=True)
    mask_file = File(exists=True)


class DTITracker(CommandLine):
    input_spec = DTITrackerInputSpec
    output_spec = DTITrackerOutputSpec

    _cmd = "dti_tracker"

    def _run_interface(self, runtime):
        _, _, ext = split_filename(self.inputs.tensor_file)
        copyfile(
            self.inputs.tensor_file,
            os.path.abspath(self.inputs.input_data_prefix + "_tensor" + ext),
            copy=False,
        )

        return super()._run_interface(runtime)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["track_file"] = os.path.abspath(self.inputs.output_file)
        if isdefined(self.inputs.output_mask) and self.inputs.output_mask:
            outputs["mask_file"] = os.path.abspath(self.inputs.output_mask)

        return outputs
