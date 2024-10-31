"""ANTS Apply Transforms interface
"""

import os

from .base import ANTSCommand, ANTSCommandInputSpec
from ..base import TraitedSpec, File, traits, Tuple, isdefined, InputMultiObject
from ...utils.filemanip import split_filename


class WarpTimeSeriesImageMultiTransformInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        4, 3, argstr="%d", usedefault=True, desc="image dimension (3 or 4)", position=1
    )
    input_image = File(
        argstr="%s",
        mandatory=True,
        copyfile=True,
        desc=("image to apply transformation to (generally a coregistered functional)"),
    )
    out_postfix = traits.Str(
        "_wtsimt",
        argstr="%s",
        usedefault=True,
        desc=("Postfix that is prepended to all output files (default = _wtsimt)"),
    )
    reference_image = File(
        argstr="-R %s",
        xor=["tightest_box"],
        desc="reference image space that you wish to warp INTO",
    )
    tightest_box = traits.Bool(
        argstr="--tightest-bounding-box",
        desc=(
            "computes tightest bounding box (overridden by reference_image if given)"
        ),
        xor=["reference_image"],
    )
    reslice_by_header = traits.Bool(
        argstr="--reslice-by-header",
        desc=(
            "Uses orientation matrix and origin encoded in "
            "reference image file header. Not typically used "
            "with additional transforms"
        ),
    )
    use_nearest = traits.Bool(
        argstr="--use-NN", desc="Use nearest neighbor interpolation"
    )
    use_bspline = traits.Bool(
        argstr="--use-Bspline", desc="Use 3rd order B-Spline interpolation"
    )
    transformation_series = InputMultiObject(
        File(exists=True),
        argstr="%s",
        desc="transformation file(s) to be applied",
        mandatory=True,
        copyfile=False,
    )
    invert_affine = traits.List(
        traits.Int,
        desc=(
            "List of Affine transformations to invert."
            "E.g.: [1,4,5] inverts the 1st, 4th, and 5th Affines "
            "found in transformation_series. Note that indexing "
            "starts with 1 and does not include warp fields. Affine "
            "transformations are distinguished "
            'from warp fields by the word "affine" included in their filenames.'
        ),
    )


class WarpTimeSeriesImageMultiTransformOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc="Warped image")


class WarpTimeSeriesImageMultiTransform(ANTSCommand):
    """Warps a time-series from one space to another

    Examples
    --------

    >>> from nipype.interfaces.ants import WarpTimeSeriesImageMultiTransform
    >>> wtsimt = WarpTimeSeriesImageMultiTransform()
    >>> wtsimt.inputs.input_image = 'resting.nii'
    >>> wtsimt.inputs.reference_image = 'ants_deformed.nii.gz'
    >>> wtsimt.inputs.transformation_series = ['ants_Warp.nii.gz','ants_Affine.txt']
    >>> wtsimt.cmdline
    'WarpTimeSeriesImageMultiTransform 4 resting.nii resting_wtsimt.nii -R ants_deformed.nii.gz ants_Warp.nii.gz \
ants_Affine.txt'

    >>> wtsimt = WarpTimeSeriesImageMultiTransform()
    >>> wtsimt.inputs.input_image = 'resting.nii'
    >>> wtsimt.inputs.reference_image = 'ants_deformed.nii.gz'
    >>> wtsimt.inputs.transformation_series = ['ants_Warp.nii.gz','ants_Affine.txt']
    >>> wtsimt.inputs.invert_affine = [1] # # this will invert the 1st Affine file: ants_Affine.txt
    >>> wtsimt.cmdline
    'WarpTimeSeriesImageMultiTransform 4 resting.nii resting_wtsimt.nii -R ants_deformed.nii.gz ants_Warp.nii.gz \
-i ants_Affine.txt'
    """

    _cmd = "WarpTimeSeriesImageMultiTransform"
    input_spec = WarpTimeSeriesImageMultiTransformInputSpec
    output_spec = WarpTimeSeriesImageMultiTransformOutputSpec

    def _format_arg(self, opt, spec, val):
        if opt == "out_postfix":
            _, name, ext = split_filename(os.path.abspath(self.inputs.input_image))
            return name + val + ext
        if opt == "transformation_series":
            series = []
            affine_counter = 0
            affine_invert = []
            for transformation in val:
                if "Affine" in transformation and isdefined(self.inputs.invert_affine):
                    affine_counter += 1
                    if affine_counter in self.inputs.invert_affine:
                        series += ["-i"]
                        affine_invert.append(affine_counter)
                series += [transformation]

            if isdefined(self.inputs.invert_affine):
                diff_inv = set(self.inputs.invert_affine) - set(affine_invert)
                if diff_inv:
                    raise Exception(
                        "Review invert_affine, not all indexes from invert_affine were used, "
                        "check the description for the full definition"
                    )

            return " ".join(series)
        return super()._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        _, name, ext = split_filename(os.path.abspath(self.inputs.input_image))
        outputs["output_image"] = os.path.join(
            os.getcwd(), f"{name}{self.inputs.out_postfix}{ext}"
        )
        return outputs

    def _run_interface(self, runtime, correct_return_codes=[0]):
        runtime = super()._run_interface(runtime, correct_return_codes=[0, 1])
        if "100 % complete" not in runtime.stdout:
            self.raise_exception(runtime)
        return runtime


class WarpImageMultiTransformInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3, 2, argstr="%d", usedefault=True, desc="image dimension (2 or 3)", position=1
    )
    input_image = File(
        argstr="%s",
        mandatory=True,
        desc=("image to apply transformation to (generally a coregistered functional)"),
        position=2,
    )
    output_image = File(
        genfile=True,
        hash_files=False,
        argstr="%s",
        desc="name of the output warped image",
        position=3,
        xor=["out_postfix"],
    )
    out_postfix = File(
        "_wimt",
        usedefault=True,
        hash_files=False,
        desc=("Postfix that is prepended to all output files (default = _wimt)"),
        xor=["output_image"],
    )
    reference_image = File(
        argstr="-R %s",
        xor=["tightest_box"],
        desc="reference image space that you wish to warp INTO",
    )
    tightest_box = traits.Bool(
        argstr="--tightest-bounding-box",
        desc=(
            "computes tightest bounding box (overridden by reference_image if given)"
        ),
        xor=["reference_image"],
    )
    reslice_by_header = traits.Bool(
        argstr="--reslice-by-header",
        desc=(
            "Uses orientation matrix and origin encoded in "
            "reference image file header. Not typically used "
            "with additional transforms"
        ),
    )
    use_nearest = traits.Bool(
        argstr="--use-NN", desc="Use nearest neighbor interpolation"
    )
    use_bspline = traits.Bool(
        argstr="--use-BSpline", desc="Use 3rd order B-Spline interpolation"
    )
    transformation_series = InputMultiObject(
        File(exists=True),
        argstr="%s",
        desc="transformation file(s) to be applied",
        mandatory=True,
        position=-1,
    )
    invert_affine = traits.List(
        traits.Int,
        desc=(
            "List of Affine transformations to invert."
            "E.g.: [1,4,5] inverts the 1st, 4th, and 5th Affines "
            "found in transformation_series. Note that indexing "
            "starts with 1 and does not include warp fields. Affine "
            "transformations are distinguished "
            'from warp fields by the word "affine" included in their filenames.'
        ),
    )


class WarpImageMultiTransformOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc="Warped image")


class WarpImageMultiTransform(ANTSCommand):
    """Warps an image from one space to another

    Examples
    --------

    >>> from nipype.interfaces.ants import WarpImageMultiTransform
    >>> wimt = WarpImageMultiTransform()
    >>> wimt.inputs.input_image = 'structural.nii'
    >>> wimt.inputs.reference_image = 'ants_deformed.nii.gz'
    >>> wimt.inputs.transformation_series = ['ants_Warp.nii.gz','ants_Affine.txt']
    >>> wimt.cmdline
    'WarpImageMultiTransform 3 structural.nii structural_wimt.nii -R ants_deformed.nii.gz ants_Warp.nii.gz \
ants_Affine.txt'

    >>> wimt = WarpImageMultiTransform()
    >>> wimt.inputs.input_image = 'diffusion_weighted.nii'
    >>> wimt.inputs.reference_image = 'functional.nii'
    >>> wimt.inputs.transformation_series = ['func2anat_coreg_Affine.txt','func2anat_InverseWarp.nii.gz', \
    'dwi2anat_Warp.nii.gz','dwi2anat_coreg_Affine.txt']
    >>> wimt.inputs.invert_affine = [1]  # this will invert the 1st Affine file: 'func2anat_coreg_Affine.txt'
    >>> wimt.cmdline
    'WarpImageMultiTransform 3 diffusion_weighted.nii diffusion_weighted_wimt.nii -R functional.nii \
-i func2anat_coreg_Affine.txt func2anat_InverseWarp.nii.gz dwi2anat_Warp.nii.gz dwi2anat_coreg_Affine.txt'

    """

    _cmd = "WarpImageMultiTransform"
    input_spec = WarpImageMultiTransformInputSpec
    output_spec = WarpImageMultiTransformOutputSpec

    def _gen_filename(self, name):
        if name == "output_image":
            _, name, ext = split_filename(os.path.abspath(self.inputs.input_image))
            return f"{name}{self.inputs.out_postfix}{ext}"
        return None

    def _format_arg(self, opt, spec, val):
        if opt == "transformation_series":
            series = []
            affine_counter = 0
            affine_invert = []
            for transformation in val:
                if "affine" in transformation.lower() and isdefined(
                    self.inputs.invert_affine
                ):
                    affine_counter += 1
                    if affine_counter in self.inputs.invert_affine:
                        series += ["-i"]
                        affine_invert.append(affine_counter)
                series += [transformation]

            if isdefined(self.inputs.invert_affine):
                diff_inv = set(self.inputs.invert_affine) - set(affine_invert)
                if diff_inv:
                    raise Exception(
                        "Review invert_affine, not all indexes from invert_affine were used, "
                        "check the description for the full definition"
                    )

            return " ".join(series)

        return super()._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.output_image):
            outputs["output_image"] = os.path.abspath(self.inputs.output_image)
        else:
            outputs["output_image"] = os.path.abspath(
                self._gen_filename("output_image")
            )
        return outputs


class ApplyTransformsInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        2,
        3,
        4,
        argstr="--dimensionality %d",
        desc=(
            "This option forces the image to be treated "
            "as a specified-dimensional image. If not "
            "specified, antsWarp tries to infer the "
            "dimensionality from the input image."
        ),
    )
    input_image_type = traits.Enum(
        0,
        1,
        2,
        3,
        argstr="--input-image-type %d",
        desc=(
            "Option specifying the input image "
            "type of scalar (default), vector, "
            "tensor, or time series."
        ),
    )
    input_image = File(
        argstr="--input %s",
        mandatory=True,
        desc=("image to apply transformation to (generally a coregistered functional)"),
        exists=True,
    )
    output_image = traits.Str(
        argstr="--output %s", desc="output file name", genfile=True, hash_files=False
    )
    out_postfix = traits.Str(
        "_trans",
        usedefault=True,
        desc=("Postfix that is appended to all output files (default = _trans)"),
    )
    reference_image = File(
        argstr="--reference-image %s",
        mandatory=True,
        desc="reference image space that you wish to warp INTO",
        exists=True,
    )
    interpolation = traits.Enum(
        "Linear",
        "NearestNeighbor",
        "CosineWindowedSinc",
        "WelchWindowedSinc",
        "HammingWindowedSinc",
        "LanczosWindowedSinc",
        "MultiLabel",
        "Gaussian",
        "BSpline",
        "GenericLabel",
        argstr="%s",
        usedefault=True,
    )
    interpolation_parameters = traits.Either(
        Tuple(traits.Int()),  # BSpline (order)
        Tuple(traits.Float(), traits.Float()),  # Gaussian/MultiLabel (sigma, alpha)
        Tuple(traits.Str()),  # GenericLabel
    )
    transforms = InputMultiObject(
        traits.Either(File(exists=True), "identity"),
        argstr="%s",
        mandatory=True,
        desc="transform files: will be applied in reverse order. For "
        "example, the last specified transform will be applied first.",
    )
    invert_transform_flags = InputMultiObject(traits.Bool())
    default_value = traits.Float(0.0, argstr="--default-value %g", usedefault=True)
    print_out_composite_warp_file = traits.Bool(
        False,
        requires=["output_image"],
        desc="output a composite warp file instead of a transformed image",
    )
    float = traits.Bool(
        argstr="--float %d",
        default_value=False,
        usedefault=True,
        desc="Use float instead of double for computations.",
    )


class ApplyTransformsOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc="Warped image")


class ApplyTransforms(ANTSCommand):
    """ApplyTransforms, applied to an input image, transforms it according to a
    reference image and a transform (or a set of transforms).

    Examples
    --------

    >>> from nipype.interfaces.ants import ApplyTransforms
    >>> at = ApplyTransforms()
    >>> at.inputs.input_image = 'moving1.nii'
    >>> at.inputs.reference_image = 'fixed1.nii'
    >>> at.inputs.transforms = 'identity'
    >>> at.cmdline
    'antsApplyTransforms --default-value 0 --float 0 --input moving1.nii \
--interpolation Linear --output moving1_trans.nii \
--reference-image fixed1.nii --transform identity'

    >>> at = ApplyTransforms()
    >>> at.inputs.dimension = 3
    >>> at.inputs.input_image = 'moving1.nii'
    >>> at.inputs.reference_image = 'fixed1.nii'
    >>> at.inputs.output_image = 'deformed_moving1.nii'
    >>> at.inputs.interpolation = 'Linear'
    >>> at.inputs.default_value = 0
    >>> at.inputs.transforms = ['ants_Warp.nii.gz', 'trans.mat']
    >>> at.inputs.invert_transform_flags = [False, True]
    >>> at.cmdline
    'antsApplyTransforms --default-value 0 --dimensionality 3 --float 0 --input moving1.nii \
--interpolation Linear --output deformed_moving1.nii --reference-image fixed1.nii \
--transform ants_Warp.nii.gz --transform [ trans.mat, 1 ]'

    >>> at1 = ApplyTransforms()
    >>> at1.inputs.dimension = 3
    >>> at1.inputs.input_image = 'moving1.nii'
    >>> at1.inputs.reference_image = 'fixed1.nii'
    >>> at1.inputs.output_image = 'deformed_moving1.nii'
    >>> at1.inputs.interpolation = 'BSpline'
    >>> at1.inputs.interpolation_parameters = (5,)
    >>> at1.inputs.default_value = 0
    >>> at1.inputs.transforms = ['ants_Warp.nii.gz', 'trans.mat']
    >>> at1.inputs.invert_transform_flags = [False, False]
    >>> at1.cmdline
    'antsApplyTransforms --default-value 0 --dimensionality 3 --float 0 --input moving1.nii \
--interpolation BSpline[ 5 ] --output deformed_moving1.nii --reference-image fixed1.nii \
--transform ants_Warp.nii.gz --transform trans.mat'

    Identity transforms may be used as part of a chain:

    >>> at2 = ApplyTransforms()
    >>> at2.inputs.dimension = 3
    >>> at2.inputs.input_image = 'moving1.nii'
    >>> at2.inputs.reference_image = 'fixed1.nii'
    >>> at2.inputs.output_image = 'deformed_moving1.nii'
    >>> at2.inputs.interpolation = 'BSpline'
    >>> at2.inputs.interpolation_parameters = (5,)
    >>> at2.inputs.default_value = 0
    >>> at2.inputs.transforms = ['identity', 'ants_Warp.nii.gz', 'trans.mat']
    >>> at2.cmdline
    'antsApplyTransforms --default-value 0 --dimensionality 3 --float 0 --input moving1.nii \
--interpolation BSpline[ 5 ] --output deformed_moving1.nii --reference-image fixed1.nii \
--transform identity --transform ants_Warp.nii.gz --transform trans.mat'
    """

    _cmd = "antsApplyTransforms"
    input_spec = ApplyTransformsInputSpec
    output_spec = ApplyTransformsOutputSpec

    def _gen_filename(self, name):
        if name == "output_image":
            output = self.inputs.output_image
            if not isdefined(output):
                _, name, ext = split_filename(self.inputs.input_image)
                output = name + self.inputs.out_postfix + ext
            return output
        return None

    def _get_transform_filenames(self):
        retval = []
        invert_flags = self.inputs.invert_transform_flags
        if not isdefined(invert_flags):
            invert_flags = [False] * len(self.inputs.transforms)
        elif len(self.inputs.transforms) != len(invert_flags):
            raise ValueError(
                "ERROR: The invert_transform_flags list must have the same number "
                "of entries as the transforms list."
            )

        for transform, invert in zip(self.inputs.transforms, invert_flags):
            if invert:
                retval.append(f"--transform [ {transform}, 1 ]")
            else:
                retval.append(f"--transform {transform}")
        return " ".join(retval)

    def _get_output_warped_filename(self):
        if isdefined(self.inputs.print_out_composite_warp_file):
            return "--output [ %s, %d ]" % (
                self._gen_filename("output_image"),
                int(self.inputs.print_out_composite_warp_file),
            )
        else:
            return "--output %s" % (self._gen_filename("output_image"))

    def _format_arg(self, opt, spec, val):
        if opt == "output_image":
            return self._get_output_warped_filename()
        elif opt == "transforms":
            return self._get_transform_filenames()
        elif opt == "interpolation":
            if self.inputs.interpolation in [
                "BSpline",
                "MultiLabel",
                "Gaussian",
                "GenericLabel",
            ] and isdefined(self.inputs.interpolation_parameters):
                return "--interpolation {}[ {} ]".format(
                    self.inputs.interpolation,
                    ", ".join(
                        [str(param) for param in self.inputs.interpolation_parameters]
                    ),
                )
            else:
                return "--interpolation %s" % self.inputs.interpolation
        return super()._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["output_image"] = os.path.abspath(self._gen_filename("output_image"))
        return outputs


class ApplyTransformsToPointsInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        2,
        3,
        4,
        argstr="--dimensionality %d",
        desc=(
            "This option forces the image to be treated "
            "as a specified-dimensional image. If not "
            "specified, antsWarp tries to infer the "
            "dimensionality from the input image."
        ),
    )
    input_file = File(
        argstr="--input %s",
        mandatory=True,
        desc=(
            "Currently, the only input supported is a csv file with"
            " columns including x,y (2D), x,y,z (3D) or x,y,z,t,label (4D) column headers."
            " The points should be defined in physical space."
            " If in doubt how to convert coordinates from your files to the space"
            " required by antsApplyTransformsToPoints try creating/drawing a simple"
            " label volume with only one voxel set to 1 and all others set to 0."
            " Write down the voxel coordinates. Then use ImageMaths LabelStats to find"
            " out what coordinates for this voxel antsApplyTransformsToPoints is"
            " expecting."
        ),
        exists=True,
    )
    output_file = traits.Str(
        argstr="--output %s",
        desc="Name of the output CSV file",
        name_source=["input_file"],
        hash_files=False,
        name_template="%s_transformed.csv",
    )
    transforms = traits.List(
        File(exists=True),
        argstr="%s",
        mandatory=True,
        desc="transforms that will be applied to the points",
    )
    invert_transform_flags = traits.List(
        traits.Bool(), desc="list indicating if a transform should be reversed"
    )


class ApplyTransformsToPointsOutputSpec(TraitedSpec):
    output_file = File(exists=True, desc="csv file with transformed coordinates")


class ApplyTransformsToPoints(ANTSCommand):
    """ApplyTransformsToPoints, applied to an CSV file, transforms coordinates
    using provided transform (or a set of transforms).

    Examples
    --------

    >>> from nipype.interfaces.ants import ApplyTransforms
    >>> at = ApplyTransformsToPoints()
    >>> at.inputs.dimension = 3
    >>> at.inputs.input_file = 'moving.csv'
    >>> at.inputs.transforms = ['trans.mat', 'ants_Warp.nii.gz']
    >>> at.inputs.invert_transform_flags = [False, False]
    >>> at.cmdline
    'antsApplyTransformsToPoints --dimensionality 3 --input moving.csv --output moving_transformed.csv \
--transform [ trans.mat, 0 ] --transform [ ants_Warp.nii.gz, 0 ]'


    """

    _cmd = "antsApplyTransformsToPoints"
    input_spec = ApplyTransformsToPointsInputSpec
    output_spec = ApplyTransformsToPointsOutputSpec

    def _get_transform_filenames(self):
        retval = []
        for ii in range(len(self.inputs.transforms)):
            if isdefined(self.inputs.invert_transform_flags):
                if len(self.inputs.transforms) == len(
                    self.inputs.invert_transform_flags
                ):
                    invert_code = 1 if self.inputs.invert_transform_flags[ii] else 0
                    retval.append(
                        "--transform [ %s, %d ]"
                        % (self.inputs.transforms[ii], invert_code)
                    )
                else:
                    raise Exception(
                        "ERROR: The useInverse list must have the same number "
                        "of entries as the transformsFileName list."
                    )
            else:
                retval.append("--transform %s" % self.inputs.transforms[ii])
        return " ".join(retval)

    def _format_arg(self, opt, spec, val):
        if opt == "transforms":
            return self._get_transform_filenames()
        return super()._format_arg(opt, spec, val)
