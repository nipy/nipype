"""ANTs' utilities."""
import os
from warnings import warn
from ..base import traits, isdefined, TraitedSpec, File, Str, InputMultiObject
from ..mixins import CopyHeaderInterface
from .base import ANTSCommandInputSpec, ANTSCommand


class ImageMathInputSpec(ANTSCommandInputSpec):
    dimension = traits.Int(
        3, usedefault=True, position=1, argstr="%d", desc="dimension of output image"
    )
    output_image = File(
        position=2,
        argstr="%s",
        name_source=["op1"],
        name_template="%s_maths",
        desc="output image file",
        keep_extension=True,
    )
    operation = traits.Enum(
        # Mathematical Operations
        "m",
        "vm",
        "+",
        "v+",
        "-",
        "v-",
        "/",
        "^",
        "max",
        "exp",
        "addtozero",
        "overadd",
        "abs",
        "total",
        "mean",
        "vtotal",
        "Decision",
        "Neg",
        # Spatial Filtering Operations
        "Project",
        "G",
        "MD",
        "ME",
        "MO",
        "MC",
        "GD",
        "GE",
        "GO",
        "GC",
        "ExtractContours",
        # Transform Image Operations
        "Translate",
        # Tensor Operations
        "4DTensorTo3DTensor",
        "ExtractVectorComponent",
        "TensorColor",
        "TensorFA",
        "TensorFADenominator",
        "TensorFANumerator",
        "TensorMeanDiffusion",
        "TensorRadialDiffusion",
        "TensorAxialDiffusion",
        "TensorEigenvalue",
        "TensorToVector",
        "TensorToVectorComponent",
        "TensorMask",
        # Unclassified Operators
        "Byte",
        "CorruptImage",
        "D",
        "MaurerDistance",
        "ExtractSlice",
        "FillHoles",
        "Convolve",
        "Finite",
        "FlattenImage",
        "GetLargestComponent",
        "Grad",
        "RescaleImage",
        "WindowImage",
        "NeighborhoodStats",
        "ReplicateDisplacement",
        "ReplicateImage",
        "LabelStats",
        "Laplacian",
        "Canny",
        "Lipschitz",
        "MTR",
        "Normalize",
        "PadImage",
        "SigmoidImage",
        "Sharpen",
        "UnsharpMask",
        "PValueImage",
        "ReplaceVoxelValue",
        "SetTimeSpacing",
        "SetTimeSpacingWarp",
        "stack",
        "ThresholdAtMean",
        "TriPlanarView",
        "TruncateImageIntensity",
        mandatory=True,
        position=3,
        argstr="%s",
        desc="mathematical operations",
    )
    op1 = File(
        exists=True, mandatory=True, position=-3, argstr="%s", desc="first operator"
    )
    op2 = traits.Either(
        File(exists=True), Str, position=-2, argstr="%s", desc="second operator"
    )

    args = Str(position=-1, argstr="%s", desc="Additional parameters to the command")

    copy_header = traits.Bool(
        True,
        usedefault=True,
        desc="copy headers of the original image into the output (corrected) file",
    )


class ImageMathOuputSpec(TraitedSpec):
    output_image = File(exists=True, desc="output image file")


class ImageMath(ANTSCommand, CopyHeaderInterface):
    """
    Operations over images.

    Examples
    --------
    >>> ImageMath(
    ...     op1='structural.nii',
    ...     operation='+',
    ...     op2='2').cmdline
    'ImageMath 3 structural_maths.nii + structural.nii 2'

    >>> ImageMath(
    ...     op1='structural.nii',
    ...     operation='Project',
    ...     op2='1 2').cmdline
    'ImageMath 3 structural_maths.nii Project structural.nii 1 2'

    >>> ImageMath(
    ...     op1='structural.nii',
    ...     operation='G',
    ...     op2='4').cmdline
    'ImageMath 3 structural_maths.nii G structural.nii 4'

    >>> ImageMath(
    ...     op1='structural.nii',
    ...     operation='TruncateImageIntensity',
    ...     op2='0.005 0.999 256').cmdline
    'ImageMath 3 structural_maths.nii TruncateImageIntensity structural.nii 0.005 0.999 256'

    By default, Nipype copies headers from the first input image (``op1``)
    to the output image.
    For some operations, as the ``PadImage`` operation, the header cannot be copied from inputs to
    outputs, and so ``copy_header`` option is automatically set to ``False``.

    >>> pad = ImageMath(
    ...     op1='structural.nii',
    ...     operation='PadImage')
    >>> pad.inputs.copy_header
    False

    While the operation is set to ``PadImage``,
    setting ``copy_header = True`` will have no effect.

    >>> pad.inputs.copy_header = True
    >>> pad.inputs.copy_header
    False

    For any other operation, ``copy_header`` can be enabled/disabled normally:

    >>> pad.inputs.operation = "ME"
    >>> pad.inputs.copy_header = True
    >>> pad.inputs.copy_header
    True

    """

    _cmd = "ImageMath"
    input_spec = ImageMathInputSpec
    output_spec = ImageMathOuputSpec
    _copy_header_map = {"output_image": "op1"}
    _no_copy_header_operation = (
        "PadImage",
        "LabelStats",
        "SetTimeSpacing",
        "SetTimeSpacingWarp",
        "TriPlanarView",
    )

    def __init__(self, **inputs):
        super(ImageMath, self).__init__(**inputs)
        if self.inputs.operation in self._no_copy_header_operation:
            self.inputs.copy_header = False

        self.inputs.on_trait_change(self._operation_update, "operation")
        self.inputs.on_trait_change(self._copyheader_update, "copy_header")

    def _operation_update(self):
        if self.inputs.operation in self._no_copy_header_operation:
            self.inputs.copy_header = False

    def _copyheader_update(self):
        if (
            self.inputs.copy_header
            and self.inputs.operation in self._no_copy_header_operation
        ):
            warn(
                f"copy_header cannot be updated to True with {self.inputs.operation} as operation."
            )
            self.inputs.copy_header = False


class ResampleImageBySpacingInputSpec(ANTSCommandInputSpec):
    dimension = traits.Int(
        3, usedefault=True, position=1, argstr="%d", desc="dimension of output image"
    )
    input_image = File(
        exists=True, mandatory=True, position=2, argstr="%s", desc="input image file"
    )
    output_image = File(
        position=3,
        argstr="%s",
        name_source=["input_image"],
        name_template="%s_resampled",
        desc="output image file",
        keep_extension=True,
    )
    out_spacing = traits.Either(
        traits.List(traits.Float, minlen=2, maxlen=3),
        traits.Tuple(traits.Float, traits.Float, traits.Float),
        traits.Tuple(traits.Float, traits.Float),
        position=4,
        argstr="%s",
        mandatory=True,
        desc="output spacing",
    )
    apply_smoothing = traits.Bool(
        False, argstr="%d", position=5, desc="smooth before resampling"
    )
    addvox = traits.Int(
        argstr="%d",
        position=6,
        requires=["apply_smoothing"],
        desc="addvox pads each dimension by addvox",
    )
    nn_interp = traits.Bool(
        argstr="%d", desc="nn interpolation", position=-1, requires=["addvox"]
    )


class ResampleImageBySpacingOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc="resampled file")


class ResampleImageBySpacing(ANTSCommand):
    """
    Resample an image with a given spacing.

    Examples
    --------
    >>> res = ResampleImageBySpacing(dimension=3)
    >>> res.inputs.input_image = 'structural.nii'
    >>> res.inputs.output_image = 'output.nii.gz'
    >>> res.inputs.out_spacing = (4, 4, 4)
    >>> res.cmdline  #doctest: +ELLIPSIS
    'ResampleImageBySpacing 3 structural.nii output.nii.gz 4 4 4'

    >>> res = ResampleImageBySpacing(dimension=3)
    >>> res.inputs.input_image = 'structural.nii'
    >>> res.inputs.output_image = 'output.nii.gz'
    >>> res.inputs.out_spacing = (4, 4, 4)
    >>> res.inputs.apply_smoothing = True
    >>> res.cmdline  #doctest: +ELLIPSIS
    'ResampleImageBySpacing 3 structural.nii output.nii.gz 4 4 4 1'

    >>> res = ResampleImageBySpacing(dimension=3)
    >>> res.inputs.input_image = 'structural.nii'
    >>> res.inputs.output_image = 'output.nii.gz'
    >>> res.inputs.out_spacing = (0.4, 0.4, 0.4)
    >>> res.inputs.apply_smoothing = True
    >>> res.inputs.addvox = 2
    >>> res.inputs.nn_interp = False
    >>> res.cmdline  #doctest: +ELLIPSIS
    'ResampleImageBySpacing 3 structural.nii output.nii.gz 0.4 0.4 0.4 1 2 0'

    """

    _cmd = "ResampleImageBySpacing"
    input_spec = ResampleImageBySpacingInputSpec
    output_spec = ResampleImageBySpacingOutputSpec

    def _format_arg(self, name, trait_spec, value):
        if name == "out_spacing":
            if len(value) != self.inputs.dimension:
                raise ValueError("out_spacing dimensions should match dimension")

            value = " ".join(["%g" % d for d in value])

        return super(ResampleImageBySpacing, self)._format_arg(name, trait_spec, value)


class ThresholdImageInputSpec(ANTSCommandInputSpec):
    dimension = traits.Int(
        3, usedefault=True, position=1, argstr="%d", desc="dimension of output image"
    )
    input_image = File(
        exists=True, mandatory=True, position=2, argstr="%s", desc="input image file"
    )
    output_image = File(
        position=3,
        argstr="%s",
        name_source=["input_image"],
        name_template="%s_resampled",
        desc="output image file",
        keep_extension=True,
    )

    mode = traits.Enum(
        "Otsu",
        "Kmeans",
        argstr="%s",
        position=4,
        requires=["num_thresholds"],
        xor=["th_low", "th_high"],
        desc="whether to run Otsu / Kmeans thresholding",
    )
    num_thresholds = traits.Int(position=5, argstr="%d", desc="number of thresholds")
    input_mask = File(
        exists=True,
        requires=["num_thresholds"],
        argstr="%s",
        desc="input mask for Otsu, Kmeans",
    )

    th_low = traits.Float(position=4, argstr="%f", xor=["mode"], desc="lower threshold")
    th_high = traits.Float(
        position=5, argstr="%f", xor=["mode"], desc="upper threshold"
    )
    inside_value = traits.Float(
        1, position=6, argstr="%f", requires=["th_low"], desc="inside value"
    )
    outside_value = traits.Float(
        0, position=7, argstr="%f", requires=["th_low"], desc="outside value"
    )
    copy_header = traits.Bool(
        True,
        mandatory=True,
        usedefault=True,
        desc="copy headers of the original image into the output (corrected) file",
    )


class ThresholdImageOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc="resampled file")


class ThresholdImage(ANTSCommand, CopyHeaderInterface):
    """
    Apply thresholds on images.

    Examples
    --------
    >>> thres = ThresholdImage(dimension=3)
    >>> thres.inputs.input_image = 'structural.nii'
    >>> thres.inputs.output_image = 'output.nii.gz'
    >>> thres.inputs.th_low = 0.5
    >>> thres.inputs.th_high = 1.0
    >>> thres.inputs.inside_value = 1.0
    >>> thres.inputs.outside_value = 0.0
    >>> thres.cmdline  #doctest: +ELLIPSIS
    'ThresholdImage 3 structural.nii output.nii.gz 0.500000 1.000000 1.000000 0.000000'

    >>> thres = ThresholdImage(dimension=3)
    >>> thres.inputs.input_image = 'structural.nii'
    >>> thres.inputs.output_image = 'output.nii.gz'
    >>> thres.inputs.mode = 'Kmeans'
    >>> thres.inputs.num_thresholds = 4
    >>> thres.cmdline  #doctest: +ELLIPSIS
    'ThresholdImage 3 structural.nii output.nii.gz Kmeans 4'

    """

    _cmd = "ThresholdImage"
    input_spec = ThresholdImageInputSpec
    output_spec = ThresholdImageOutputSpec
    _copy_header_map = {"output_image": "input_image"}


class AIInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3, 2, usedefault=True, argstr="-d %d", desc="dimension of output image"
    )
    verbose = traits.Bool(
        False, usedefault=True, argstr="-v %d", desc="enable verbosity"
    )

    fixed_image = File(
        exists=True,
        mandatory=True,
        desc="Image to which the moving_image should be transformed",
    )
    moving_image = File(
        exists=True,
        mandatory=True,
        desc="Image that will be transformed to fixed_image",
    )

    fixed_image_mask = File(exists=True, argstr="-x %s", desc="fixed mage mask")
    moving_image_mask = File(
        exists=True, requires=["fixed_image_mask"], desc="moving mage mask"
    )

    metric_trait = (
        traits.Enum("Mattes", "GC", "MI"),
        traits.Int(32),
        traits.Enum("Regular", "Random", "None"),
        traits.Range(value=0.2, low=0.0, high=1.0),
    )
    metric = traits.Tuple(
        *metric_trait, argstr="-m %s", mandatory=True, desc="the metric(s) to use."
    )

    transform = traits.Tuple(
        traits.Enum("Affine", "Rigid", "Similarity"),
        traits.Range(value=0.1, low=0.0, exclude_low=True),
        argstr="-t %s[%g]",
        usedefault=True,
        desc="Several transform options are available",
    )

    principal_axes = traits.Bool(
        False,
        usedefault=True,
        argstr="-p %d",
        xor=["blobs"],
        desc="align using principal axes",
    )
    search_factor = traits.Tuple(
        traits.Float(20),
        traits.Range(value=0.12, low=0.0, high=1.0),
        usedefault=True,
        argstr="-s [%g,%g]",
        desc="search factor",
    )

    search_grid = traits.Either(
        traits.Tuple(
            traits.Float, traits.Tuple(traits.Float, traits.Float, traits.Float)
        ),
        traits.Tuple(traits.Float, traits.Tuple(traits.Float, traits.Float)),
        argstr="-g %s",
        desc="Translation search grid in mm",
        min_ver="2.3.0",
    )

    convergence = traits.Tuple(
        traits.Range(low=1, high=10000, value=10),
        traits.Float(1e-6),
        traits.Range(low=1, high=100, value=10),
        usedefault=True,
        argstr="-c [%d,%g,%d]",
        desc="convergence",
    )

    output_transform = File(
        "initialization.mat", usedefault=True, argstr="-o %s", desc="output file name"
    )


class AIOuputSpec(TraitedSpec):
    output_transform = File(exists=True, desc="output file name")


class AI(ANTSCommand):
    """
    Calculate the optimal linear transform parameters for aligning two images.

    Examples
    --------
    >>> AI(
    ...     fixed_image='structural.nii',
    ...     moving_image='epi.nii',
    ...     metric=('Mattes', 32, 'Regular', 1),
    ... ).cmdline
    'antsAI -c [10,1e-06,10] -d 3 -m Mattes[structural.nii,epi.nii,32,Regular,1]
    -o initialization.mat -p 0 -s [20,0.12] -t Affine[0.1] -v 0'

    >>> AI(fixed_image='structural.nii',
    ...    moving_image='epi.nii',
    ...    metric=('Mattes', 32, 'Regular', 1),
    ...    search_grid=(12, (1, 1, 1)),
    ... ).cmdline
    'antsAI -c [10,1e-06,10] -d 3 -m Mattes[structural.nii,epi.nii,32,Regular,1]
    -o initialization.mat -p 0 -s [20,0.12] -g [12.0,1x1x1] -t Affine[0.1] -v 0'

    """

    _cmd = "antsAI"
    input_spec = AIInputSpec
    output_spec = AIOuputSpec

    def _run_interface(self, runtime, correct_return_codes=(0,)):
        runtime = super(AI, self)._run_interface(runtime, correct_return_codes)

        self._output = {
            "output_transform": os.path.join(
                runtime.cwd, os.path.basename(self.inputs.output_transform)
            )
        }
        return runtime

    def _format_arg(self, opt, spec, val):
        if opt == "metric":
            val = "%s[{fixed_image},{moving_image},%d,%s,%g]" % val
            val = val.format(
                fixed_image=self.inputs.fixed_image,
                moving_image=self.inputs.moving_image,
            )
            return spec.argstr % val

        if opt == "search_grid":
            fmtval = "[%s,%s]" % (val[0], "x".join("%g" % v for v in val[1]))
            return spec.argstr % fmtval

        if opt == "fixed_image_mask":
            if isdefined(self.inputs.moving_image_mask):
                return spec.argstr % ("[%s,%s]" % (val, self.inputs.moving_image_mask))

        return super(AI, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        return getattr(self, "_output")


class AverageAffineTransformInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3, 2, argstr="%d", mandatory=True, position=0, desc="image dimension (2 or 3)"
    )
    output_affine_transform = File(
        argstr="%s",
        mandatory=True,
        position=1,
        desc="Outputfname.txt: the name of the resulting transform.",
    )
    transforms = InputMultiObject(
        File(exists=True),
        argstr="%s",
        mandatory=True,
        position=3,
        desc="transforms to average",
    )


class AverageAffineTransformOutputSpec(TraitedSpec):
    affine_transform = File(exists=True, desc="average transform file")


class AverageAffineTransform(ANTSCommand):
    """
    Examples
    --------
    >>> from nipype.interfaces.ants import AverageAffineTransform
    >>> avg = AverageAffineTransform()
    >>> avg.inputs.dimension = 3
    >>> avg.inputs.transforms = ['trans.mat', 'func_to_struct.mat']
    >>> avg.inputs.output_affine_transform = 'MYtemplatewarp.mat'
    >>> avg.cmdline
    'AverageAffineTransform 3 MYtemplatewarp.mat trans.mat func_to_struct.mat'

    """

    _cmd = "AverageAffineTransform"
    input_spec = AverageAffineTransformInputSpec
    output_spec = AverageAffineTransformOutputSpec

    def _format_arg(self, opt, spec, val):
        return super(AverageAffineTransform, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["affine_transform"] = os.path.abspath(
            self.inputs.output_affine_transform
        )
        return outputs


class AverageImagesInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3, 2, argstr="%d", mandatory=True, position=0, desc="image dimension (2 or 3)"
    )
    output_average_image = File(
        "average.nii",
        argstr="%s",
        position=1,
        usedefault=True,
        hash_files=False,
        desc="the name of the resulting image.",
    )
    normalize = traits.Bool(
        argstr="%d",
        mandatory=True,
        position=2,
        desc="Normalize: if true, the 2nd image is divided by its mean. "
        "This will select the largest image to average into.",
    )
    images = InputMultiObject(
        File(exists=True),
        argstr="%s",
        mandatory=True,
        position=3,
        desc="image to apply transformation to (generally a coregistered functional)",
    )


class AverageImagesOutputSpec(TraitedSpec):
    output_average_image = File(exists=True, desc="average image file")


class AverageImages(ANTSCommand):
    """
    Examples
    --------
    >>> from nipype.interfaces.ants import AverageImages
    >>> avg = AverageImages()
    >>> avg.inputs.dimension = 3
    >>> avg.inputs.output_average_image = "average.nii.gz"
    >>> avg.inputs.normalize = True
    >>> avg.inputs.images = ['rc1s1.nii', 'rc1s1.nii']
    >>> avg.cmdline
    'AverageImages 3 average.nii.gz 1 rc1s1.nii rc1s1.nii'
    """

    _cmd = "AverageImages"
    input_spec = AverageImagesInputSpec
    output_spec = AverageImagesOutputSpec

    def _format_arg(self, opt, spec, val):
        return super(AverageImages, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["output_average_image"] = os.path.realpath(
            self.inputs.output_average_image
        )
        return outputs


class MultiplyImagesInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3, 2, argstr="%d", mandatory=True, position=0, desc="image dimension (2 or 3)"
    )
    first_input = File(
        argstr="%s", exists=True, mandatory=True, position=1, desc="image 1"
    )
    second_input = traits.Either(
        File(exists=True),
        traits.Float,
        argstr="%s",
        mandatory=True,
        position=2,
        desc="image 2 or multiplication weight",
    )
    output_product_image = File(
        argstr="%s",
        mandatory=True,
        position=3,
        desc="Outputfname.nii.gz: the name of the resulting image.",
    )


class MultiplyImagesOutputSpec(TraitedSpec):
    output_product_image = File(exists=True, desc="average image file")


class MultiplyImages(ANTSCommand):
    """
    Examples
    --------
    >>> from nipype.interfaces.ants import MultiplyImages
    >>> test = MultiplyImages()
    >>> test.inputs.dimension = 3
    >>> test.inputs.first_input = 'moving2.nii'
    >>> test.inputs.second_input = 0.25
    >>> test.inputs.output_product_image = "out.nii"
    >>> test.cmdline
    'MultiplyImages 3 moving2.nii 0.25 out.nii'
    """

    _cmd = "MultiplyImages"
    input_spec = MultiplyImagesInputSpec
    output_spec = MultiplyImagesOutputSpec

    def _format_arg(self, opt, spec, val):
        return super(MultiplyImages, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["output_product_image"] = os.path.abspath(
            self.inputs.output_product_image
        )
        return outputs


class CreateJacobianDeterminantImageInputSpec(ANTSCommandInputSpec):
    imageDimension = traits.Enum(
        3, 2, argstr="%d", mandatory=True, position=0, desc="image dimension (2 or 3)"
    )
    deformationField = File(
        argstr="%s",
        exists=True,
        mandatory=True,
        position=1,
        desc="deformation transformation file",
    )
    outputImage = File(argstr="%s", mandatory=True, position=2, desc="output filename")
    doLogJacobian = traits.Enum(
        0, 1, argstr="%d", position=3, desc="return the log jacobian"
    )
    useGeometric = traits.Enum(
        0, 1, argstr="%d", position=4, desc="return the geometric jacobian"
    )


class CreateJacobianDeterminantImageOutputSpec(TraitedSpec):
    jacobian_image = File(exists=True, desc="jacobian image")


class CreateJacobianDeterminantImage(ANTSCommand):
    """
    Examples
    --------
    >>> from nipype.interfaces.ants import CreateJacobianDeterminantImage
    >>> jacobian = CreateJacobianDeterminantImage()
    >>> jacobian.inputs.imageDimension = 3
    >>> jacobian.inputs.deformationField = 'ants_Warp.nii.gz'
    >>> jacobian.inputs.outputImage = 'out_name.nii.gz'
    >>> jacobian.cmdline
    'CreateJacobianDeterminantImage 3 ants_Warp.nii.gz out_name.nii.gz'
    """

    _cmd = "CreateJacobianDeterminantImage"
    input_spec = CreateJacobianDeterminantImageInputSpec
    output_spec = CreateJacobianDeterminantImageOutputSpec

    def _format_arg(self, opt, spec, val):
        return super(CreateJacobianDeterminantImage, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["jacobian_image"] = os.path.abspath(self.inputs.outputImage)
        return outputs


class AffineInitializerInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3, 2, usedefault=True, position=0, argstr="%s", desc="dimension"
    )
    fixed_image = File(
        exists=True, mandatory=True, position=1, argstr="%s", desc="reference image"
    )
    moving_image = File(
        exists=True, mandatory=True, position=2, argstr="%s", desc="moving image"
    )
    out_file = File(
        "transform.mat",
        usedefault=True,
        position=3,
        argstr="%s",
        desc="output transform file",
    )
    # Defaults in antsBrainExtraction.sh -> 15 0.1 0 10
    search_factor = traits.Float(
        15.0,
        usedefault=True,
        position=4,
        argstr="%f",
        desc="increments (degrees) for affine search",
    )
    radian_fraction = traits.Range(
        0.0,
        1.0,
        value=0.1,
        usedefault=True,
        position=5,
        argstr="%f",
        desc="search this arc +/- principal axes",
    )
    principal_axes = traits.Bool(
        False,
        usedefault=True,
        position=6,
        argstr="%d",
        desc="whether the rotation is searched around an initial principal axis alignment.",
    )
    local_search = traits.Int(
        10,
        usedefault=True,
        position=7,
        argstr="%d",
        desc=" determines if a local optimization is run at each search point for the set "
        "number of iterations",
    )


class AffineInitializerOutputSpec(TraitedSpec):
    out_file = File(desc="output transform file")


class AffineInitializer(ANTSCommand):
    """
    Initialize an affine transform (as in antsBrainExtraction.sh)

    >>> from nipype.interfaces.ants import AffineInitializer
    >>> init = AffineInitializer()
    >>> init.inputs.fixed_image = 'fixed1.nii'
    >>> init.inputs.moving_image = 'moving1.nii'
    >>> init.cmdline
    'antsAffineInitializer 3 fixed1.nii moving1.nii transform.mat 15.000000 0.100000 0 10'

    """

    _cmd = "antsAffineInitializer"
    input_spec = AffineInitializerInputSpec
    output_spec = AffineInitializerOutputSpec

    def _list_outputs(self):
        return {"out_file": os.path.abspath(self.inputs.out_file)}


class ComposeMultiTransformInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3, 2, argstr="%d", usedefault=True, position=0, desc="image dimension (2 or 3)"
    )
    output_transform = File(
        argstr="%s",
        position=1,
        name_source=["transforms"],
        name_template="%s_composed",
        keep_extension=True,
        desc="the name of the resulting transform.",
    )
    reference_image = File(
        argstr="%s",
        position=2,
        desc="Reference image (only necessary when output is warpfield)",
    )
    transforms = InputMultiObject(
        File(exists=True),
        argstr="%s",
        mandatory=True,
        position=3,
        desc="transforms to average",
    )


class ComposeMultiTransformOutputSpec(TraitedSpec):
    output_transform = File(exists=True, desc="Composed transform file")


class ComposeMultiTransform(ANTSCommand):
    """
    Take a set of transformations and convert them to a single transformation matrix/warpfield.

    Examples
    --------
    >>> from nipype.interfaces.ants import ComposeMultiTransform
    >>> compose_transform = ComposeMultiTransform()
    >>> compose_transform.inputs.dimension = 3
    >>> compose_transform.inputs.transforms = ['struct_to_template.mat', 'func_to_struct.mat']
    >>> compose_transform.cmdline
    'ComposeMultiTransform 3 struct_to_template_composed.mat
    struct_to_template.mat func_to_struct.mat'

    """

    _cmd = "ComposeMultiTransform"
    input_spec = ComposeMultiTransformInputSpec
    output_spec = ComposeMultiTransformOutputSpec


class LabelGeometryInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3, 2, argstr="%d", usedefault=True, position=0, desc="image dimension (2 or 3)"
    )
    label_image = File(
        argstr="%s",
        position=1,
        mandatory=True,
        desc="label image to use for extracting geometry measures",
    )
    intensity_image = File(
        value="[]",
        exists=True,
        argstr="%s",
        mandatory=True,
        usedefault=True,
        position=2,
        desc="Intensity image to extract values from. " "This is an optional input",
    )
    output_file = traits.Str(
        name_source=["label_image"],
        name_template="%s.csv",
        argstr="%s",
        position=3,
        desc="name of output file",
    )


class LabelGeometryOutputSpec(TraitedSpec):
    output_file = File(exists=True, desc="CSV file of geometry measures")


class LabelGeometry(ANTSCommand):
    """
    Extracts geometry measures using a label file and an optional image file

    Examples
    --------
    >>> from nipype.interfaces.ants import LabelGeometry
    >>> label_extract = LabelGeometry()
    >>> label_extract.inputs.dimension = 3
    >>> label_extract.inputs.label_image = 'atlas.nii.gz'
    >>> label_extract.cmdline
    'LabelGeometryMeasures 3 atlas.nii.gz [] atlas.csv'

    >>> label_extract.inputs.intensity_image = 'ants_Warp.nii.gz'
    >>> label_extract.cmdline
    'LabelGeometryMeasures 3 atlas.nii.gz ants_Warp.nii.gz atlas.csv'

    """

    _cmd = "LabelGeometryMeasures"
    input_spec = LabelGeometryInputSpec
    output_spec = LabelGeometryOutputSpec
