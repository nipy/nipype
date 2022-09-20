# -*- coding: utf-8 -*-
"""The ants module provides basic functions for interfacing with ants
   functions.
"""
import os

from ...utils.filemanip import ensure_list
from ..base import TraitedSpec, File, Str, traits, InputMultiPath, isdefined
from .base import ANTSCommand, ANTSCommandInputSpec, LOCAL_DEFAULT_NUMBER_OF_THREADS


class ANTSInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3, 2, argstr="%d", position=1, desc="image dimension (2 or 3)"
    )
    fixed_image = InputMultiPath(
        File(exists=True),
        mandatory=True,
        desc=("image to which the moving image is " "warped"),
    )
    moving_image = InputMultiPath(
        File(exists=True),
        argstr="%s",
        mandatory=True,
        desc=(
            "image to apply transformation to "
            "(generally a coregistered"
            "functional)"
        ),
    )

    #    Not all metrics are appropriate for all modalities. Also, not all metrics
    #    are efficeint or appropriate at all resolution levels, Some metrics
    #    perform well for gross global registraiton, but do poorly for small
    #    changes (i.e. Mattes), and some metrics do well for small changes but
    #    don't work well for gross level changes (i.e. 'CC').
    #
    #    This is a two stage registration. in the first stage
    #      [ 'Mattes', .................]
    #         ^^^^^^ <- First stage
    #    Do a unimodal registration of the first elements of the fixed/moving input
    #    list use the"CC" as the metric.
    #
    #    In the second stage
    #      [ ....., ['Mattes','CC'] ]
    #               ^^^^^^^^^^^^^^^ <- Second stage
    #    Do a multi-modal registration where the first elements of fixed/moving
    #    input list use 'CC' metric and that is added to 'Mattes' metric result of
    #    the second elements of the fixed/moving input.
    #
    #    Cost = Sum_i ( metricweight[i] Metric_i ( fixedimage[i], movingimage[i]) )
    metric = traits.List(
        traits.Enum("CC", "MI", "SMI", "PR", "SSD", "MSQ", "PSE"),
        mandatory=True,
        desc="",
    )

    metric_weight = traits.List(
        traits.Float(),
        value=[1.0],
        usedefault=True,
        requires=["metric"],
        mandatory=True,
        desc="the metric weight(s) for each stage. "
        "The weights must sum to 1 per stage.",
    )

    radius = traits.List(
        traits.Int(),
        requires=["metric"],
        mandatory=True,
        desc="radius of the region (i.e. number of layers around a voxel/pixel)"
        " that is used for computing cross correlation",
    )

    output_transform_prefix = Str(
        "out", usedefault=True, argstr="--output-naming %s", mandatory=True, desc=""
    )
    transformation_model = traits.Enum(
        "Diff",
        "Elast",
        "Exp",
        "Greedy Exp",
        "SyN",
        argstr="%s",
        mandatory=True,
        desc="",
    )
    gradient_step_length = traits.Float(requires=["transformation_model"], desc="")
    number_of_time_steps = traits.Int(requires=["gradient_step_length"], desc="")
    delta_time = traits.Float(requires=["number_of_time_steps"], desc="")
    symmetry_type = traits.Float(requires=["delta_time"], desc="")

    use_histogram_matching = traits.Bool(
        argstr="%s", default_value=True, usedefault=True
    )
    number_of_iterations = traits.List(
        traits.Int(), argstr="--number-of-iterations %s", sep="x"
    )
    smoothing_sigmas = traits.List(
        traits.Int(), argstr="--gaussian-smoothing-sigmas %s", sep="x"
    )
    subsampling_factors = traits.List(
        traits.Int(), argstr="--subsampling-factors %s", sep="x"
    )
    affine_gradient_descent_option = traits.List(traits.Float(), argstr="%s")

    mi_option = traits.List(traits.Int(), argstr="--MI-option %s", sep="x")
    regularization = traits.Enum("Gauss", "DMFFD", argstr="%s", desc="")
    regularization_gradient_field_sigma = traits.Float(
        requires=["regularization"], desc=""
    )
    regularization_deformation_field_sigma = traits.Float(
        requires=["regularization"], desc=""
    )
    number_of_affine_iterations = traits.List(
        traits.Int(), argstr="--number-of-affine-iterations %s", sep="x"
    )


class ANTSOutputSpec(TraitedSpec):
    affine_transform = File(exists=True, desc="Affine transform file")
    warp_transform = File(exists=True, desc="Warping deformation field")
    inverse_warp_transform = File(exists=True, desc="Inverse warping deformation field")
    metaheader = File(exists=True, desc="VTK metaheader .mhd file")
    metaheader_raw = File(exists=True, desc="VTK metaheader .raw file")


class ANTS(ANTSCommand):
    """ANTS wrapper for registration of images
    (old, use Registration instead)

    Examples
    --------

    >>> from nipype.interfaces.ants import ANTS
    >>> ants = ANTS()
    >>> ants.inputs.dimension = 3
    >>> ants.inputs.output_transform_prefix = 'MY'
    >>> ants.inputs.metric = ['CC']
    >>> ants.inputs.fixed_image = ['T1.nii']
    >>> ants.inputs.moving_image = ['resting.nii']
    >>> ants.inputs.metric_weight = [1.0]
    >>> ants.inputs.radius = [5]
    >>> ants.inputs.transformation_model = 'SyN'
    >>> ants.inputs.gradient_step_length = 0.25
    >>> ants.inputs.number_of_iterations = [50, 35, 15]
    >>> ants.inputs.use_histogram_matching = True
    >>> ants.inputs.mi_option = [32, 16000]
    >>> ants.inputs.regularization = 'Gauss'
    >>> ants.inputs.regularization_gradient_field_sigma = 3
    >>> ants.inputs.regularization_deformation_field_sigma = 0
    >>> ants.inputs.number_of_affine_iterations = [10000,10000,10000,10000,10000]
    >>> ants.cmdline
    'ANTS 3 --MI-option 32x16000 --image-metric CC[ T1.nii, resting.nii, 1, 5 ] --number-of-affine-iterations \
10000x10000x10000x10000x10000 --number-of-iterations 50x35x15 --output-naming MY --regularization Gauss[3.0,0.0] \
--transformation-model SyN[0.25] --use-Histogram-Matching 1'
    """

    _cmd = "ANTS"
    input_spec = ANTSInputSpec
    output_spec = ANTSOutputSpec

    def _image_metric_constructor(self):
        retval = []
        intensity_based = ["CC", "MI", "SMI", "PR", "SSD", "MSQ"]
        point_set_based = ["PSE", "JTB"]
        for ii in range(len(self.inputs.moving_image)):
            if self.inputs.metric[ii] in intensity_based:
                retval.append(
                    "--image-metric %s[ %s, %s, %g, %d ]"
                    % (
                        self.inputs.metric[ii],
                        self.inputs.fixed_image[ii],
                        self.inputs.moving_image[ii],
                        self.inputs.metric_weight[ii],
                        self.inputs.radius[ii],
                    )
                )
            elif self.inputs.metric[ii] == point_set_based:
                pass
                # retval.append('--image-metric %s[%s, %s, ...'.format(self.inputs.metric[ii],
                #               self.inputs.fixed_image[ii], self.inputs.moving_image[ii], ...))
        return " ".join(retval)

    def _transformation_constructor(self):
        model = self.inputs.transformation_model
        step_length = self.inputs.gradient_step_length
        time_step = self.inputs.number_of_time_steps
        delta_time = self.inputs.delta_time
        symmetry_type = self.inputs.symmetry_type
        retval = ["--transformation-model %s" % model]
        parameters = []
        for elem in (step_length, time_step, delta_time, symmetry_type):
            if elem is not traits.Undefined:
                parameters.append("%#.2g" % elem)
        if len(parameters) > 0:
            if len(parameters) > 1:
                parameters = ",".join(parameters)
            else:
                parameters = "".join(parameters)
            retval.append("[%s]" % parameters)
        return "".join(retval)

    def _regularization_constructor(self):
        return "--regularization {0}[{1},{2}]".format(
            self.inputs.regularization,
            self.inputs.regularization_gradient_field_sigma,
            self.inputs.regularization_deformation_field_sigma,
        )

    def _affine_gradient_descent_option_constructor(self):
        values = self.inputs.affine_gradient_descent_option
        defaults = [0.1, 0.5, 1.0e-4, 1.0e-4]
        for ii in range(len(defaults)):
            try:
                defaults[ii] = values[ii]
            except IndexError:
                break
        parameters = self._format_xarray(
            [("%g" % defaults[index]) for index in range(4)]
        )
        retval = ["--affine-gradient-descent-option", parameters]
        return " ".join(retval)

    def _format_arg(self, opt, spec, val):
        if opt == "moving_image":
            return self._image_metric_constructor()
        elif opt == "transformation_model":
            return self._transformation_constructor()
        elif opt == "regularization":
            return self._regularization_constructor()
        elif opt == "affine_gradient_descent_option":
            return self._affine_gradient_descent_option_constructor()
        elif opt == "use_histogram_matching":
            if self.inputs.use_histogram_matching:
                return "--use-Histogram-Matching 1"
            else:
                return "--use-Histogram-Matching 0"
        return super(ANTS, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["affine_transform"] = os.path.abspath(
            self.inputs.output_transform_prefix + "Affine.txt"
        )
        outputs["warp_transform"] = os.path.abspath(
            self.inputs.output_transform_prefix + "Warp.nii.gz"
        )
        outputs["inverse_warp_transform"] = os.path.abspath(
            self.inputs.output_transform_prefix + "InverseWarp.nii.gz"
        )
        # outputs['metaheader'] = os.path.abspath(self.inputs.output_transform_prefix + 'velocity.mhd')
        # outputs['metaheader_raw'] = os.path.abspath(self.inputs.output_transform_prefix + 'velocity.raw')
        return outputs


class RegistrationInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3,
        2,
        argstr="--dimensionality %d",
        usedefault=True,
        desc="image dimension (2 or 3)",
    )
    fixed_image = InputMultiPath(
        File(exists=True),
        mandatory=True,
        desc="Image to which the moving_image should be transformed"
        "(usually a structural image)",
    )
    fixed_image_mask = File(
        exists=True,
        argstr="%s",
        max_ver="2.1.0",
        xor=["fixed_image_masks"],
        desc="Mask used to limit metric sampling region of the fixed image"
        "in all stages",
    )
    fixed_image_masks = InputMultiPath(
        traits.Either("NULL", File(exists=True)),
        min_ver="2.2.0",
        xor=["fixed_image_mask"],
        desc="Masks used to limit metric sampling region of the fixed image, defined per registration stage"
        '(Use "NULL" to omit a mask at a given stage)',
    )
    moving_image = InputMultiPath(
        File(exists=True),
        mandatory=True,
        desc="Image that will be registered to the space of fixed_image. This is the"
        "image on which the transformations will be applied to",
    )
    moving_image_mask = File(
        exists=True,
        requires=["fixed_image_mask"],
        max_ver="2.1.0",
        xor=["moving_image_masks"],
        desc="mask used to limit metric sampling region of the moving image"
        "in all stages",
    )
    moving_image_masks = InputMultiPath(
        traits.Either("NULL", File(exists=True)),
        min_ver="2.2.0",
        xor=["moving_image_mask"],
        desc="Masks used to limit metric sampling region of the moving image, defined per registration stage"
        '(Use "NULL" to omit a mask at a given stage)',
    )

    save_state = File(
        argstr="--save-state %s",
        exists=False,
        desc="Filename for saving the internal restorable state of the registration",
    )
    restore_state = File(
        argstr="--restore-state %s",
        exists=True,
        desc="Filename for restoring the internal restorable state of the registration",
    )

    initial_moving_transform = InputMultiPath(
        File(exists=True),
        argstr="%s",
        desc="A transform or a list of transforms that should be applied "
        "before the registration begins. Note that, when a list is given, "
        "the transformations are applied in reverse order.",
        xor=["initial_moving_transform_com"],
    )
    invert_initial_moving_transform = InputMultiPath(
        traits.Bool(),
        requires=["initial_moving_transform"],
        desc="One boolean or a list of booleans that indicate"
        "whether the inverse(s) of the transform(s) defined"
        "in initial_moving_transform should be used.",
        xor=["initial_moving_transform_com"],
    )

    initial_moving_transform_com = traits.Enum(
        0,
        1,
        2,
        argstr="%s",
        xor=["initial_moving_transform"],
        desc="Align the moving_image and fixed_image before registration using "
        "the geometric center of the images (=0), the image intensities (=1), "
        "or the origin of the images (=2).",
    )
    metric_item_trait = traits.Enum("CC", "MeanSquares", "Demons", "GC", "MI", "Mattes")
    metric_stage_trait = traits.Either(
        metric_item_trait, traits.List(metric_item_trait)
    )
    metric = traits.List(
        metric_stage_trait,
        mandatory=True,
        desc="the metric(s) to use for each stage. "
        "Note that multiple metrics per stage are not supported "
        "in ANTS 1.9.1 and earlier.",
    )
    metric_weight_item_trait = traits.Float(1.0, usedefault=True)
    metric_weight_stage_trait = traits.Either(
        metric_weight_item_trait, traits.List(metric_weight_item_trait)
    )
    metric_weight = traits.List(
        metric_weight_stage_trait,
        value=[1.0],
        usedefault=True,
        requires=["metric"],
        mandatory=True,
        desc="the metric weight(s) for each stage. "
        "The weights must sum to 1 per stage.",
    )
    radius_bins_item_trait = traits.Int(5, usedefault=True)
    radius_bins_stage_trait = traits.Either(
        radius_bins_item_trait, traits.List(radius_bins_item_trait)
    )
    radius_or_number_of_bins = traits.List(
        radius_bins_stage_trait,
        value=[5],
        usedefault=True,
        requires=["metric_weight"],
        desc="the number of bins in each stage for the MI and Mattes metric, "
        "the radius for other metrics",
    )
    sampling_strategy_item_trait = traits.Enum("None", "Regular", "Random", None)
    sampling_strategy_stage_trait = traits.Either(
        sampling_strategy_item_trait, traits.List(sampling_strategy_item_trait)
    )
    sampling_strategy = traits.List(
        trait=sampling_strategy_stage_trait,
        requires=["metric_weight"],
        desc="the metric sampling strategy (strategies) for each stage",
    )
    sampling_percentage_item_trait = traits.Either(
        traits.Range(low=0.0, high=1.0), None
    )
    sampling_percentage_stage_trait = traits.Either(
        sampling_percentage_item_trait, traits.List(sampling_percentage_item_trait)
    )
    sampling_percentage = traits.List(
        trait=sampling_percentage_stage_trait,
        requires=["sampling_strategy"],
        desc="the metric sampling percentage(s) to use for each stage",
    )
    use_estimate_learning_rate_once = traits.List(traits.Bool(), desc="")
    use_histogram_matching = traits.Either(
        traits.Bool,
        traits.List(traits.Bool(argstr="%s")),
        default=True,
        usedefault=True,
        desc="Histogram match the images before registration.",
    )
    interpolation = traits.Enum(
        "Linear",
        "NearestNeighbor",
        "CosineWindowedSinc",
        "WelchWindowedSinc",
        "HammingWindowedSinc",
        "LanczosWindowedSinc",
        "BSpline",
        "MultiLabel",
        "Gaussian",
        "GenericLabel",
        argstr="%s",
        usedefault=True,
    )
    interpolation_parameters = traits.Either(
        traits.Tuple(traits.Int()),  # BSpline (order)
        traits.Tuple(
            traits.Float(), traits.Float()  # Gaussian/MultiLabel (sigma, alpha)
        ),
        traits.Tuple(traits.Str()),  # GenericLabel (interpolator)
    )

    write_composite_transform = traits.Bool(
        argstr="--write-composite-transform %d",
        default_value=False,
        usedefault=True,
        desc="",
    )
    collapse_output_transforms = traits.Bool(
        argstr="--collapse-output-transforms %d",
        default_value=True,
        usedefault=True,  # This should be true for explicit completeness
        desc=(
            "Collapse output transforms. Specifically, enabling this option "
            "combines all adjacent linear transforms and composes all "
            "adjacent displacement field transforms before writing the "
            "results to disk."
        ),
    )
    initialize_transforms_per_stage = traits.Bool(
        argstr="--initialize-transforms-per-stage %d",
        default_value=False,
        usedefault=True,  # This should be true for explicit completeness
        desc=(
            "Initialize linear transforms from the previous stage. By enabling this option, "
            "the current linear stage transform is directly initialized from the previous "
            "stages linear transform; this allows multiple linear stages to be run where "
            "each stage directly updates the estimated linear transform from the previous "
            "stage. (e.g. Translation -> Rigid -> Affine). "
        ),
    )
    # NOTE: Even though only 0=False and 1=True are allowed, ants uses integer
    # values instead of booleans
    float = traits.Bool(
        argstr="--float %d",
        default_value=False,
        desc="Use float instead of double for computations.",
    )

    transforms = traits.List(
        traits.Enum(
            "Rigid",
            "Affine",
            "CompositeAffine",
            "Similarity",
            "Translation",
            "BSpline",
            "GaussianDisplacementField",
            "TimeVaryingVelocityField",
            "TimeVaryingBSplineVelocityField",
            "SyN",
            "BSplineSyN",
            "Exponential",
            "BSplineExponential",
        ),
        argstr="%s",
        mandatory=True,
    )
    # TODO: input checking and allow defaults
    # All parameters must be specified for BSplineDisplacementField, TimeVaryingBSplineVelocityField, BSplineSyN,
    # Exponential, and BSplineExponential. EVEN DEFAULTS!
    transform_parameters = traits.List(
        traits.Either(
            traits.Tuple(traits.Float()),  # Translation, Rigid, Affine,
            # CompositeAffine, Similarity
            traits.Tuple(
                traits.Float(),  # GaussianDisplacementField, SyN
                traits.Float(),
                traits.Float(),
            ),
            traits.Tuple(
                traits.Float(),  # BSplineSyn,
                traits.Int(),  # BSplineDisplacementField,
                traits.Int(),  # TimeVaryingBSplineVelocityField
                traits.Int(),
            ),
            traits.Tuple(
                traits.Float(),  # TimeVaryingVelocityField
                traits.Int(),
                traits.Float(),
                traits.Float(),
                traits.Float(),
                traits.Float(),
            ),
            traits.Tuple(
                traits.Float(),  # Exponential
                traits.Float(),
                traits.Float(),
                traits.Int(),
            ),
            traits.Tuple(
                traits.Float(),  # BSplineExponential
                traits.Int(),
                traits.Int(),
                traits.Int(),
                traits.Int(),
            ),
        )
    )
    restrict_deformation = traits.List(
        traits.List(traits.Range(low=0.0, high=1.0)),
        desc=(
            "This option allows the user to restrict the optimization of "
            "the displacement field, translation, rigid or affine transform "
            "on a per-component basis. For example, if one wants to limit "
            "the deformation or rotation of 3-D volume to the  first two "
            "dimensions, this is possible by specifying a weight vector of "
            "'1x1x0' for a deformation field or '1x1x0x1x1x0' for a rigid "
            "transformation.  Low-dimensional restriction only works if "
            "there are no preceding transformations."
        ),
    )
    # Convergence flags
    number_of_iterations = traits.List(traits.List(traits.Int()))
    smoothing_sigmas = traits.List(traits.List(traits.Float()), mandatory=True)
    sigma_units = traits.List(
        traits.Enum("mm", "vox"),
        requires=["smoothing_sigmas"],
        desc="units for smoothing sigmas",
    )
    shrink_factors = traits.List(traits.List(traits.Int()), mandatory=True)
    convergence_threshold = traits.List(
        trait=traits.Float(),
        value=[1e-6],
        minlen=1,
        requires=["number_of_iterations"],
        usedefault=True,
    )
    convergence_window_size = traits.List(
        trait=traits.Int(),
        value=[10],
        minlen=1,
        requires=["convergence_threshold"],
        usedefault=True,
    )
    # Output flags
    output_transform_prefix = Str("transform", usedefault=True, argstr="%s", desc="")
    output_warped_image = traits.Either(traits.Bool, File(), hash_files=False, desc="")
    output_inverse_warped_image = traits.Either(
        traits.Bool, File(), hash_files=False, requires=["output_warped_image"], desc=""
    )
    winsorize_upper_quantile = traits.Range(
        low=0.0,
        high=1.0,
        value=1.0,
        argstr="%s",
        usedefault=True,
        desc="The Upper quantile to clip image ranges",
    )
    winsorize_lower_quantile = traits.Range(
        low=0.0,
        high=1.0,
        value=0.0,
        argstr="%s",
        usedefault=True,
        desc="The Lower quantile to clip image ranges",
    )
    random_seed = traits.Int(
        argstr="--random-seed %d",
        desc="Fixed seed for random number generation",
        min_ver="2.3.0",
    )
    verbose = traits.Bool(
        argstr="-v", default_value=False, usedefault=True, nohash=True
    )


class RegistrationOutputSpec(TraitedSpec):
    forward_transforms = traits.List(
        File(exists=True), desc="List of output transforms for forward registration"
    )
    reverse_forward_transforms = traits.List(
        File(exists=True),
        desc="List of output transforms for forward registration reversed for antsApplyTransform",
    )
    reverse_transforms = traits.List(
        File(exists=True), desc="List of output transforms for reverse registration"
    )
    forward_invert_flags = traits.List(
        traits.Bool(), desc="List of flags corresponding to the forward transforms"
    )
    reverse_forward_invert_flags = traits.List(
        traits.Bool(),
        desc="List of flags corresponding to the forward transforms reversed for antsApplyTransform",
    )
    reverse_invert_flags = traits.List(
        traits.Bool(), desc="List of flags corresponding to the reverse transforms"
    )
    composite_transform = File(exists=True, desc="Composite transform file")
    inverse_composite_transform = File(desc="Inverse composite transform file")
    warped_image = File(desc="Outputs warped image")
    inverse_warped_image = File(desc="Outputs the inverse of the warped image")
    save_state = File(desc="The saved registration state to be restored")
    metric_value = traits.Float(desc="the final value of metric")
    elapsed_time = traits.Float(desc="the total elapsed time as reported by ANTs")


class Registration(ANTSCommand):
    """ANTs Registration command for registration of images

    `antsRegistration <http://stnava.github.io/ANTs/>`_ registers a ``moving_image`` to a ``fixed_image``,
    using a predefined (sequence of) cost function(s) and transformation operations.
    The cost function is defined using one or more 'metrics', specifically
    local cross-correlation (``CC``), Mean Squares (``MeanSquares``), Demons (``Demons``),
    global correlation (``GC``), or Mutual Information (``Mattes`` or ``MI``).

    ANTS can use both linear (``Translation``, ``Rigid``, ``Affine``, ``CompositeAffine``,
    or ``Translation``) and non-linear transformations (``BSpline``, ``GaussianDisplacementField``,
    ``TimeVaryingVelocityField``, ``TimeVaryingBSplineVelocityField``, ``SyN``, ``BSplineSyN``,
    ``Exponential``, or ``BSplineExponential``). Usually, registration is done in multiple
    *stages*. For example first an Affine, then a Rigid, and ultimately a non-linear
    (Syn)-transformation.

    antsRegistration can be initialized using one or more transforms from moving_image
    to fixed_image with the ``initial_moving_transform``-input. For example, when you
    already have a warpfield that corrects for geometrical distortions in an EPI (functional) image,
    that you want to apply before an Affine registration to a structural image.
    You could put this transform into 'intial_moving_transform'.

    The Registration-interface can output the resulting transform(s) that map moving_image to
    fixed_image in a single file as a ``composite_transform`` (if ``write_composite_transform``
    is set to ``True``), or a list of transforms as ``forwards_transforms``. It can also output
    inverse transforms (from ``fixed_image`` to ``moving_image``) in a similar fashion using
    ``inverse_composite_transform``. Note that the order of ``forward_transforms`` is in 'natural'
    order: the first element should be applied first, the last element should be applied last.

    Note, however, that ANTS tools always apply lists of transformations in reverse order (the last
    transformation in the list is applied first). Therefore, if the output forward_transforms
    is a list, one can not directly feed it into, for example, ``ants.ApplyTransforms``. To
    make ``ants.ApplyTransforms`` apply the transformations in the same order as ``ants.Registration``,
    you have to provide the list of transformations in reverse order from ``forward_transforms``.
    ``reverse_forward_transforms`` outputs ``forward_transforms`` in reverse order and can be used for
    this purpose. Note also that, because ``composite_transform`` is always a single file, this
    output is preferred for  most use-cases.

    More information can be found in the `ANTS
    manual <https://sourceforge.net/projects/advants/files/Documentation/ants.pdf/download>`_.

    See below for some useful examples.

    Examples
    --------

    Set up a Registration node with some default settings. This Node registers
    'fixed1.nii' to 'moving1.nii' by first fitting a linear 'Affine' transformation, and
    then a non-linear 'SyN' transformation, both using the Mutual Information-cost
    metric.

    The registration is initialized by first applying the (linear) transform
    trans.mat.

    >>> import copy, pprint
    >>> from nipype.interfaces.ants import Registration
    >>> reg = Registration()
    >>> reg.inputs.fixed_image = 'fixed1.nii'
    >>> reg.inputs.moving_image = 'moving1.nii'
    >>> reg.inputs.output_transform_prefix = "output_"
    >>> reg.inputs.initial_moving_transform = 'trans.mat'
    >>> reg.inputs.transforms = ['Affine', 'SyN']
    >>> reg.inputs.transform_parameters = [(2.0,), (0.25, 3.0, 0.0)]
    >>> reg.inputs.number_of_iterations = [[1500, 200], [100, 50, 30]]
    >>> reg.inputs.dimension = 3
    >>> reg.inputs.write_composite_transform = True
    >>> reg.inputs.collapse_output_transforms = False
    >>> reg.inputs.initialize_transforms_per_stage = False
    >>> reg.inputs.metric = ['Mattes']*2
    >>> reg.inputs.metric_weight = [1]*2 # Default (value ignored currently by ANTs)
    >>> reg.inputs.radius_or_number_of_bins = [32]*2
    >>> reg.inputs.sampling_strategy = ['Random', None]
    >>> reg.inputs.sampling_percentage = [0.05, None]
    >>> reg.inputs.convergence_threshold = [1.e-8, 1.e-9]
    >>> reg.inputs.convergence_window_size = [20]*2
    >>> reg.inputs.smoothing_sigmas = [[1,0], [2,1,0]]
    >>> reg.inputs.sigma_units = ['vox'] * 2
    >>> reg.inputs.shrink_factors = [[2,1], [3,2,1]]
    >>> reg.inputs.use_estimate_learning_rate_once = [True, True]
    >>> reg.inputs.use_histogram_matching = [True, True] # This is the default
    >>> reg.inputs.output_warped_image = 'output_warped_image.nii.gz'
    >>> reg.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 0 ] \
--initialize-transforms-per-stage 0 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] \
--transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] \
--convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[ 0.25, 3.0, 0.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] --convergence [ 100x50x30, 1e-09, 20 ] \
--smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 \
--use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ]  --write-composite-transform 1'
    >>> reg.run()  # doctest: +SKIP

    Same as reg1, but first invert the initial transform ('trans.mat') before applying it.

    >>> reg.inputs.invert_initial_moving_transform = True
    >>> reg1 = copy.deepcopy(reg)
    >>> reg1.inputs.winsorize_lower_quantile = 0.025
    >>> reg1.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 0 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] \
--transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] \
--convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[ 0.25, 3.0, 0.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] --convergence [ 100x50x30, 1e-09, 20 ] \
--smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 \
--use-histogram-matching 1 --winsorize-image-intensities [ 0.025, 1.0 ]  --write-composite-transform 1'
    >>> reg1.run()  # doctest: +SKIP

    Clip extremely high intensity data points using winsorize_upper_quantile. All data points
    higher than the 0.975 quantile are set to the value of the 0.975 quantile.

    >>> reg2 = copy.deepcopy(reg)
    >>> reg2.inputs.winsorize_upper_quantile = 0.975
    >>> reg2.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 0 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] \
--transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] \
--convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[ 0.25, 3.0, 0.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] --convergence [ 100x50x30, 1e-09, 20 ] \
--smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 \
--use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 0.975 ]  --write-composite-transform 1'

    Clip extremely low intensity data points using winsorize_lower_quantile. All data points
    lower than the 0.025 quantile are set to the original value at the 0.025 quantile.


    >>> reg3 = copy.deepcopy(reg)
    >>> reg3.inputs.winsorize_lower_quantile = 0.025
    >>> reg3.inputs.winsorize_upper_quantile = 0.975
    >>> reg3.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 0 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] \
--transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] \
--convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[ 0.25, 3.0, 0.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] --convergence [ 100x50x30, 1e-09, 20 ] \
--smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 \
--use-histogram-matching 1 --winsorize-image-intensities [ 0.025, 0.975 ]  --write-composite-transform 1'

    Use float instead of double for computations (saves memory usage)

    >>> reg3a = copy.deepcopy(reg)
    >>> reg3a.inputs.float = True
    >>> reg3a.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --float 1 \
--initial-moving-transform [ trans.mat, 1 ] --initialize-transforms-per-stage 0 --interpolation Linear \
--output [ output_, output_warped_image.nii.gz ] --transform Affine[ 2.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] --convergence [ 1500x200, 1e-08, 20 ] \
--smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 \
--transform SyN[ 0.25, 3.0, 0.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] \
--convergence [ 100x50x30, 1e-09, 20 ] --smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ]  \
--write-composite-transform 1'

    Force to use double instead of float for computations (more precision and memory usage).

    >>> reg3b = copy.deepcopy(reg)
    >>> reg3b.inputs.float = False
    >>> reg3b.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --float 0 \
--initial-moving-transform [ trans.mat, 1 ] --initialize-transforms-per-stage 0 --interpolation Linear \
--output [ output_, output_warped_image.nii.gz ] --transform Affine[ 2.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] --convergence [ 1500x200, 1e-08, 20 ] \
--smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 \
--transform SyN[ 0.25, 3.0, 0.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] \
--convergence [ 100x50x30, 1e-09, 20 ] --smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ]  \
--write-composite-transform 1'

    'collapse_output_transforms' can be used to put all transformation in a single 'composite_transform'-
    file. Note that forward_transforms will now be an empty list.

    >>> # Test collapse transforms flag
    >>> reg4 = copy.deepcopy(reg)
    >>> reg4.inputs.save_state = 'trans.mat'
    >>> reg4.inputs.restore_state = 'trans.mat'
    >>> reg4.inputs.initialize_transforms_per_stage = True
    >>> reg4.inputs.collapse_output_transforms = True
    >>> outputs = reg4._list_outputs()
    >>> pprint.pprint(outputs)  # doctest: +ELLIPSIS,
    {'composite_transform': '...data/output_Composite.h5',
     'elapsed_time': <undefined>,
     'forward_invert_flags': [],
     'forward_transforms': [],
     'inverse_composite_transform': '...data/output_InverseComposite.h5',
     'inverse_warped_image': <undefined>,
     'metric_value': <undefined>,
     'reverse_forward_invert_flags': [],
     'reverse_forward_transforms': [],
     'reverse_invert_flags': [],
     'reverse_transforms': [],
     'save_state': '...data/trans.mat',
     'warped_image': '...data/output_warped_image.nii.gz'}
    >>> reg4.cmdline
    'antsRegistration --collapse-output-transforms 1 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 1 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] \
--restore-state trans.mat --save-state trans.mat --transform Affine[ 2.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] --convergence [ 1500x200, 1e-08, 20 ] \
--smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 \
--transform SyN[ 0.25, 3.0, 0.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] \
--convergence [ 100x50x30, 1e-09, 20 ] --smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ]  \
--write-composite-transform 1'


    >>> # Test collapse transforms flag
    >>> reg4b = copy.deepcopy(reg4)
    >>> reg4b.inputs.write_composite_transform = False
    >>> outputs = reg4b._list_outputs()
    >>> pprint.pprint(outputs)  # doctest: +ELLIPSIS,
    {'composite_transform': <undefined>,
     'elapsed_time': <undefined>,
     'forward_invert_flags': [False, False],
     'forward_transforms': ['...data/output_0GenericAffine.mat',
     '...data/output_1Warp.nii.gz'],
     'inverse_composite_transform': <undefined>,
     'inverse_warped_image': <undefined>,
     'metric_value': <undefined>,
     'reverse_forward_invert_flags': [False, False],
     'reverse_forward_transforms': ['...data/output_1Warp.nii.gz',
     '...data/output_0GenericAffine.mat'],
     'reverse_invert_flags': [True, False],
     'reverse_transforms': ['...data/output_0GenericAffine.mat', \
    '...data/output_1InverseWarp.nii.gz'],
     'save_state': '...data/trans.mat',
     'warped_image': '...data/output_warped_image.nii.gz'}
    >>> reg4b.aggregate_outputs()  # doctest: +SKIP
    >>> reg4b.cmdline
    'antsRegistration --collapse-output-transforms 1 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 1 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] \
--restore-state trans.mat --save-state trans.mat --transform Affine[ 2.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] --convergence [ 1500x200, 1e-08, 20 ] \
--smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 \
--transform SyN[ 0.25, 3.0, 0.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] \
--convergence [ 100x50x30, 1e-09, 20 ] --smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ]  \
--write-composite-transform 0'

    One can use multiple similarity metrics in a single registration stage.The Node below first
    performs a linear registation using only the Mutual Information ('Mattes')-metric.
    In a second stage, it performs a non-linear registration ('Syn') using both a
    Mutual Information and a local cross-correlation ('CC')-metric. Both metrics are weighted
    equally ('metric_weight' is .5 for both). The Mutual Information- metric uses 32 bins.
    The local cross-correlations (correlations between every voxel's neighborhoods) is computed
    with a radius of 4.

    >>> # Test multiple metrics per stage
    >>> reg5 = copy.deepcopy(reg)
    >>> reg5.inputs.fixed_image = 'fixed1.nii'
    >>> reg5.inputs.moving_image = 'moving1.nii'
    >>> reg5.inputs.metric = ['Mattes', ['Mattes', 'CC']]
    >>> reg5.inputs.metric_weight = [1, [.5,.5]]
    >>> reg5.inputs.radius_or_number_of_bins = [32, [32, 4] ]
    >>> reg5.inputs.sampling_strategy = ['Random', None] # use default strategy in second stage
    >>> reg5.inputs.sampling_percentage = [0.05, [0.05, 0.10]]
    >>> reg5.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 0 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] \
--transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] \
--convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[ 0.25, 3.0, 0.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 0.5, 32, None, 0.05 ] \
--metric CC[ fixed1.nii, moving1.nii, 0.5, 4, None, 0.1 ] --convergence [ 100x50x30, 1e-09, 20 ] \
--smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 \
--use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ]  --write-composite-transform 1'

    ANTS Registration can also use multiple modalities to perform the registration. Here it is assumed
    that fixed1.nii and fixed2.nii are in the same space, and so are moving1.nii and
    moving2.nii. First, a linear registration is performed matching fixed1.nii to moving1.nii,
    then a non-linear registration is performed to match fixed2.nii to moving2.nii, starting from
    the transformation of the first step.

    >>> # Test multiple inputS
    >>> reg6 = copy.deepcopy(reg5)
    >>> reg6.inputs.fixed_image = ['fixed1.nii', 'fixed2.nii']
    >>> reg6.inputs.moving_image = ['moving1.nii', 'moving2.nii']
    >>> reg6.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 0 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] \
--transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] \
--convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[ 0.25, 3.0, 0.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 0.5, 32, None, 0.05 ] \
--metric CC[ fixed2.nii, moving2.nii, 0.5, 4, None, 0.1 ] --convergence [ 100x50x30, 1e-09, 20 ] \
--smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 \
--use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ]  --write-composite-transform 1'

    Different methods can be used for the interpolation when applying transformations.

    >>> # Test Interpolation Parameters (BSpline)
    >>> reg7a = copy.deepcopy(reg)
    >>> reg7a.inputs.interpolation = 'BSpline'
    >>> reg7a.inputs.interpolation_parameters = (3,)
    >>> reg7a.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 0 --interpolation BSpline[ 3 ] --output [ output_, output_warped_image.nii.gz ] \
--transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] \
--convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[ 0.25, 3.0, 0.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] --convergence [ 100x50x30, 1e-09, 20 ] \
--smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 \
--use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ]  --write-composite-transform 1'

    >>> # Test Interpolation Parameters (MultiLabel/Gaussian)
    >>> reg7b = copy.deepcopy(reg)
    >>> reg7b.inputs.interpolation = 'Gaussian'
    >>> reg7b.inputs.interpolation_parameters = (1.0, 1.0)
    >>> reg7b.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 0 --interpolation Gaussian[ 1.0, 1.0 ] \
--output [ output_, output_warped_image.nii.gz ] --transform Affine[ 2.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] --convergence [ 1500x200, 1e-08, 20 ] \
--smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 \
--transform SyN[ 0.25, 3.0, 0.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] \
--convergence [ 100x50x30, 1e-09, 20 ] --smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ]  \
--write-composite-transform 1'

    BSplineSyN non-linear registration with custom parameters.

    >>> # Test Extended Transform Parameters
    >>> reg8 = copy.deepcopy(reg)
    >>> reg8.inputs.transforms = ['Affine', 'BSplineSyN']
    >>> reg8.inputs.transform_parameters = [(2.0,), (0.25, 26, 0, 3)]
    >>> reg8.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 0 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] \
--transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] \
--convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform BSplineSyN[ 0.25, 26, 0, 3 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] --convergence [ 100x50x30, 1e-09, 20 ] \
--smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 \
--use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ]  --write-composite-transform 1'

    Mask the fixed image in the second stage of the registration (but not the first).

    >>> # Test masking
    >>> reg9 = copy.deepcopy(reg)
    >>> reg9.inputs.fixed_image_masks = ['NULL', 'fixed1.nii']
    >>> reg9.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 1 ] \
--initialize-transforms-per-stage 0 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] \
--transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] \
--convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --masks [ NULL, NULL ] \
--transform SyN[ 0.25, 3.0, 0.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] \
--convergence [ 100x50x30, 1e-09, 20 ] --smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --masks [ fixed1.nii, NULL ] \
--winsorize-image-intensities [ 0.0, 1.0 ]  --write-composite-transform 1'

    Here we use both a warpfield and a linear transformation, before registration commences.  Note that
    the first transformation that needs to be applied ('ants_Warp.nii.gz') is last in the list of
    'initial_moving_transform'.

    >>> # Test initialization with multiple transforms matrices (e.g., unwarp and affine transform)
    >>> reg10 = copy.deepcopy(reg)
    >>> reg10.inputs.initial_moving_transform = ['func_to_struct.mat', 'ants_Warp.nii.gz']
    >>> reg10.inputs.invert_initial_moving_transform = [False, False]
    >>> reg10.cmdline
    'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform \
[ func_to_struct.mat, 0 ] [ ants_Warp.nii.gz, 0 ] --initialize-transforms-per-stage 0 --interpolation Linear \
--output [ output_, output_warped_image.nii.gz ] --transform Affine[ 2.0 ] \
--metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] --convergence [ 1500x200, 1e-08, 20 ] \
--smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 \
--transform SyN[ 0.25, 3.0, 0.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] \
--convergence [ 100x50x30, 1e-09, 20 ] --smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 \
--use-estimate-learning-rate-once 1 --use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ]  \
--write-composite-transform 1'
    """

    DEF_SAMPLING_STRATEGY = "None"
    """The default sampling strategy argument."""

    _cmd = "antsRegistration"
    input_spec = RegistrationInputSpec
    output_spec = RegistrationOutputSpec
    _quantilesDone = False
    _linear_transform_names = [
        "Rigid",
        "Affine",
        "Translation",
        "CompositeAffine",
        "Similarity",
    ]

    def __init__(self, **inputs):
        super(Registration, self).__init__(**inputs)
        self._elapsed_time = None
        self._metric_value = None

    def _run_interface(self, runtime, correct_return_codes=(0,)):
        runtime = super(Registration, self)._run_interface(runtime)

        # Parse some profiling info
        output = runtime.stdout or runtime.merged
        if output:
            lines = output.split("\n")
            for l in lines[::-1]:
                # This should be the last line
                if l.strip().startswith("Total elapsed time:"):
                    self._elapsed_time = float(
                        l.strip().replace("Total elapsed time: ", "")
                    )
                elif "DIAGNOSTIC" in l:
                    self._metric_value = float(l.split(",")[2])
                    break

        return runtime

    def _format_metric(self, index):
        """
        Format the antsRegistration -m metric argument(s).

        Parameters
        ----------
        index: the stage index
        """
        # The metric name input for the current stage.
        name_input = self.inputs.metric[index]
        # The stage-specific input dictionary.
        stage_inputs = dict(
            fixed_image=self.inputs.fixed_image[0],
            moving_image=self.inputs.moving_image[0],
            metric=name_input,
            weight=self.inputs.metric_weight[index],
            radius_or_bins=self.inputs.radius_or_number_of_bins[index],
            optional=self.inputs.radius_or_number_of_bins[index],
        )
        # The optional sampling strategy and percentage.
        if isdefined(self.inputs.sampling_strategy) and self.inputs.sampling_strategy:
            sampling_strategy = self.inputs.sampling_strategy[index]
            if sampling_strategy:
                stage_inputs["sampling_strategy"] = sampling_strategy
        if (
            isdefined(self.inputs.sampling_percentage)
            and self.inputs.sampling_percentage
        ):
            sampling_percentage = self.inputs.sampling_percentage[index]
            if sampling_percentage:
                stage_inputs["sampling_percentage"] = sampling_percentage

        # Make a list of metric specifications, one per -m command line
        # argument for the current stage.
        # If there are multiple inputs for this stage, then convert the
        # dictionary of list inputs into a list of metric specifications.
        # Otherwise, make a singleton list of the metric specification
        # from the non-list inputs.
        if isinstance(name_input, list):
            items = list(stage_inputs.items())
            indexes = list(range(0, len(name_input)))
            specs = list()
            for i in indexes:
                temp = dict([(k, v[i]) for k, v in items])
                if len(self.inputs.fixed_image) == 1:
                    temp["fixed_image"] = self.inputs.fixed_image[0]
                else:
                    temp["fixed_image"] = self.inputs.fixed_image[i]

                if len(self.inputs.moving_image) == 1:
                    temp["moving_image"] = self.inputs.moving_image[0]
                else:
                    temp["moving_image"] = self.inputs.moving_image[i]

                specs.append(temp)
        else:
            specs = [stage_inputs]

        # Format the --metric command line metric arguments, one per
        # specification.
        return [self._format_metric_argument(**spec) for spec in specs]

    @staticmethod
    def _format_metric_argument(**kwargs):
        retval = "%s[ %s, %s, %g, %d" % (
            kwargs["metric"],
            kwargs["fixed_image"],
            kwargs["moving_image"],
            kwargs["weight"],
            kwargs["radius_or_bins"],
        )

        # The optional sampling strategy.
        if "sampling_strategy" in kwargs:
            sampling_strategy = kwargs["sampling_strategy"]
        elif "sampling_percentage" in kwargs:
            # The sampling percentage is specified but not the
            # sampling strategy. Use the default strategy.
            sampling_strategy = Registration.DEF_SAMPLING_STRATEGY
        else:
            sampling_strategy = None
        # Format the optional sampling arguments.
        if sampling_strategy:
            retval += ", %s" % sampling_strategy
            if "sampling_percentage" in kwargs:
                retval += ", %g" % kwargs["sampling_percentage"]

        retval += " ]"

        return retval

    def _format_transform(self, index):
        retval = []
        retval.append("%s[ " % self.inputs.transforms[index])
        parameters = ", ".join(
            [str(element) for element in self.inputs.transform_parameters[index]]
        )
        retval.append("%s" % parameters)
        retval.append(" ]")
        return "".join(retval)

    def _format_registration(self):
        retval = []
        for ii in range(len(self.inputs.transforms)):
            retval.append("--transform %s" % (self._format_transform(ii)))
            for metric in self._format_metric(ii):
                retval.append("--metric %s" % metric)
            retval.append("--convergence %s" % self._format_convergence(ii))
            if isdefined(self.inputs.sigma_units):
                retval.append(
                    "--smoothing-sigmas %s%s"
                    % (
                        self._format_xarray(self.inputs.smoothing_sigmas[ii]),
                        self.inputs.sigma_units[ii],
                    )
                )
            else:
                retval.append(
                    "--smoothing-sigmas %s"
                    % self._format_xarray(self.inputs.smoothing_sigmas[ii])
                )
            retval.append(
                "--shrink-factors %s"
                % self._format_xarray(self.inputs.shrink_factors[ii])
            )
            if isdefined(self.inputs.use_estimate_learning_rate_once):
                retval.append(
                    "--use-estimate-learning-rate-once %d"
                    % self.inputs.use_estimate_learning_rate_once[ii]
                )
            if isdefined(self.inputs.use_histogram_matching):
                # use_histogram_matching is either a common flag for all transforms
                # or a list of transform-specific flags
                if isinstance(self.inputs.use_histogram_matching, bool):
                    histval = self.inputs.use_histogram_matching
                else:
                    histval = self.inputs.use_histogram_matching[ii]
                retval.append("--use-histogram-matching %d" % histval)
            if isdefined(self.inputs.restrict_deformation):
                retval.append(
                    "--restrict-deformation %s"
                    % self._format_xarray(self.inputs.restrict_deformation[ii])
                )
            if any(
                (
                    isdefined(self.inputs.fixed_image_masks),
                    isdefined(self.inputs.moving_image_masks),
                )
            ):
                if isdefined(self.inputs.fixed_image_masks):
                    fixed_masks = ensure_list(self.inputs.fixed_image_masks)
                    fixed_mask = fixed_masks[ii if len(fixed_masks) > 1 else 0]
                else:
                    fixed_mask = "NULL"

                if isdefined(self.inputs.moving_image_masks):
                    moving_masks = ensure_list(self.inputs.moving_image_masks)
                    moving_mask = moving_masks[ii if len(moving_masks) > 1 else 0]
                else:
                    moving_mask = "NULL"
                retval.append("--masks [ %s, %s ]" % (fixed_mask, moving_mask))
        return " ".join(retval)

    def _get_outputfilenames(self, inverse=False):
        output_filename = None
        if not inverse:
            if (
                isdefined(self.inputs.output_warped_image)
                and self.inputs.output_warped_image
            ):
                output_filename = self.inputs.output_warped_image
                if isinstance(output_filename, bool):
                    output_filename = (
                        "%s_Warped.nii.gz" % self.inputs.output_transform_prefix
                    )
            return output_filename
        inv_output_filename = None
        if (
            isdefined(self.inputs.output_inverse_warped_image)
            and self.inputs.output_inverse_warped_image
        ):
            inv_output_filename = self.inputs.output_inverse_warped_image
            if isinstance(inv_output_filename, bool):
                inv_output_filename = (
                    "%s_InverseWarped.nii.gz" % self.inputs.output_transform_prefix
                )
        return inv_output_filename

    def _format_convergence(self, ii):
        convergence_iter = self._format_xarray(self.inputs.number_of_iterations[ii])
        if len(self.inputs.convergence_threshold) > ii:
            convergence_value = self.inputs.convergence_threshold[ii]
        else:
            convergence_value = self.inputs.convergence_threshold[0]
        if len(self.inputs.convergence_window_size) > ii:
            convergence_ws = self.inputs.convergence_window_size[ii]
        else:
            convergence_ws = self.inputs.convergence_window_size[0]
        return "[ %s, %g, %d ]" % (convergence_iter, convergence_value, convergence_ws)

    def _format_winsorize_image_intensities(self):
        if (
            not self.inputs.winsorize_upper_quantile
            > self.inputs.winsorize_lower_quantile
        ):
            raise RuntimeError(
                "Upper bound MUST be more than lower bound: %g > %g"
                % (
                    self.inputs.winsorize_upper_quantile,
                    self.inputs.winsorize_lower_quantile,
                )
            )
        self._quantilesDone = True
        return "--winsorize-image-intensities [ %s, %s ]" % (
            self.inputs.winsorize_lower_quantile,
            self.inputs.winsorize_upper_quantile,
        )

    def _get_initial_transform_filenames(self):
        n_transforms = len(self.inputs.initial_moving_transform)

        # Assume transforms should not be inverted by default
        invert_flags = [0] * n_transforms
        if isdefined(self.inputs.invert_initial_moving_transform):
            if len(self.inputs.invert_initial_moving_transform) != n_transforms:
                raise Exception(
                    'Inputs "initial_moving_transform" and "invert_initial_moving_transform"'
                    "should have the same length."
                )
            invert_flags = self.inputs.invert_initial_moving_transform

        retval = [
            "[ %s, %d ]" % (xfm, int(flag))
            for xfm, flag in zip(self.inputs.initial_moving_transform, invert_flags)
        ]
        return " ".join(["--initial-moving-transform"] + retval)

    def _format_arg(self, opt, spec, val):
        if opt == "fixed_image_mask":
            if isdefined(self.inputs.moving_image_mask):
                return "--masks [ %s, %s ]" % (
                    self.inputs.fixed_image_mask,
                    self.inputs.moving_image_mask,
                )
            else:
                return "--masks %s" % self.inputs.fixed_image_mask
        elif opt == "transforms":
            return self._format_registration()
        elif opt == "initial_moving_transform":
            return self._get_initial_transform_filenames()
        elif opt == "initial_moving_transform_com":
            do_center_of_mass_init = (
                self.inputs.initial_moving_transform_com
                if isdefined(self.inputs.initial_moving_transform_com)
                else 0
            )  # Just do the default behavior
            return "--initial-moving-transform [ %s, %s, %d ]" % (
                self.inputs.fixed_image[0],
                self.inputs.moving_image[0],
                do_center_of_mass_init,
            )
        elif opt == "interpolation":
            if self.inputs.interpolation in [
                "BSpline",
                "MultiLabel",
                "Gaussian",
                "GenericLabel",
            ] and isdefined(self.inputs.interpolation_parameters):
                return "--interpolation %s[ %s ]" % (
                    self.inputs.interpolation,
                    ", ".join(
                        [str(param) for param in self.inputs.interpolation_parameters]
                    ),
                )
            else:
                return "--interpolation %s" % self.inputs.interpolation
        elif opt == "output_transform_prefix":
            out_filename = self._get_outputfilenames(inverse=False)
            inv_out_filename = self._get_outputfilenames(inverse=True)
            if out_filename and inv_out_filename:
                return "--output [ %s, %s, %s ]" % (
                    self.inputs.output_transform_prefix,
                    out_filename,
                    inv_out_filename,
                )
            elif out_filename:
                return "--output [ %s, %s ]" % (
                    self.inputs.output_transform_prefix,
                    out_filename,
                )
            else:
                return "--output %s" % self.inputs.output_transform_prefix
        elif opt == "winsorize_upper_quantile" or opt == "winsorize_lower_quantile":
            if not self._quantilesDone:
                return self._format_winsorize_image_intensities()
            else:
                self._quantilesDone = False
                return ""  # Must return something for argstr!
        # This feature was removed from recent versions of antsRegistration due to corrupt outputs.
        # elif opt == 'collapse_linear_transforms_to_fixed_image_header':
        #    return self._formatCollapseLinearTransformsToFixedImageHeader()
        return super(Registration, self)._format_arg(opt, spec, val)

    def _output_filenames(self, prefix, count, transform, inverse=False):
        self.low_dimensional_transform_map = {
            "Rigid": "Rigid.mat",
            "Affine": "Affine.mat",
            "GenericAffine": "GenericAffine.mat",
            "CompositeAffine": "Affine.mat",
            "Similarity": "Similarity.mat",
            "Translation": "Translation.mat",
            "BSpline": "BSpline.txt",
            "Initial": "DerivedInitialMovingTranslation.mat",
        }
        if transform in list(self.low_dimensional_transform_map.keys()):
            suffix = self.low_dimensional_transform_map[transform]
            inverse_mode = inverse
        else:
            inverse_mode = False  # These are not analytically invertable
            if inverse:
                suffix = "InverseWarp.nii.gz"
            else:
                suffix = "Warp.nii.gz"
        return "%s%d%s" % (prefix, count, suffix), inverse_mode

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["forward_transforms"] = []
        outputs["forward_invert_flags"] = []
        outputs["reverse_transforms"] = []
        outputs["reverse_invert_flags"] = []

        # invert_initial_moving_transform should be always defined, even if
        # there's no initial transform
        invert_initial_moving_transform = [False] * len(
            self.inputs.initial_moving_transform
        )
        if isdefined(self.inputs.invert_initial_moving_transform):
            invert_initial_moving_transform = (
                self.inputs.invert_initial_moving_transform
            )

        if self.inputs.write_composite_transform:
            filename = self.inputs.output_transform_prefix + "Composite.h5"
            outputs["composite_transform"] = os.path.abspath(filename)
            filename = self.inputs.output_transform_prefix + "InverseComposite.h5"
            outputs["inverse_composite_transform"] = os.path.abspath(filename)
        # If composite transforms are written, then individuals are not written (as of 2014-10-26
        else:
            if not self.inputs.collapse_output_transforms:
                transform_count = 0
                if isdefined(self.inputs.initial_moving_transform):
                    outputs[
                        "forward_transforms"
                    ] += self.inputs.initial_moving_transform
                    outputs["forward_invert_flags"] += invert_initial_moving_transform
                    outputs["reverse_transforms"] = (
                        self.inputs.initial_moving_transform
                        + outputs["reverse_transforms"]
                    )
                    outputs["reverse_invert_flags"] = [
                        not e for e in invert_initial_moving_transform
                    ] + outputs[
                        "reverse_invert_flags"
                    ]  # Prepend
                    transform_count += len(self.inputs.initial_moving_transform)
                elif isdefined(self.inputs.initial_moving_transform_com):
                    forward_filename, forward_inversemode = self._output_filenames(
                        self.inputs.output_transform_prefix, transform_count, "Initial"
                    )
                    reverse_filename, reverse_inversemode = self._output_filenames(
                        self.inputs.output_transform_prefix,
                        transform_count,
                        "Initial",
                        True,
                    )
                    outputs["forward_transforms"].append(
                        os.path.abspath(forward_filename)
                    )
                    outputs["forward_invert_flags"].append(False)
                    outputs["reverse_transforms"].insert(
                        0, os.path.abspath(reverse_filename)
                    )
                    outputs["reverse_invert_flags"].insert(0, True)
                    transform_count += 1

                for count in range(len(self.inputs.transforms)):
                    forward_filename, forward_inversemode = self._output_filenames(
                        self.inputs.output_transform_prefix,
                        transform_count,
                        self.inputs.transforms[count],
                    )
                    reverse_filename, reverse_inversemode = self._output_filenames(
                        self.inputs.output_transform_prefix,
                        transform_count,
                        self.inputs.transforms[count],
                        True,
                    )
                    outputs["forward_transforms"].append(
                        os.path.abspath(forward_filename)
                    )
                    outputs["forward_invert_flags"].append(forward_inversemode)
                    outputs["reverse_transforms"].insert(
                        0, os.path.abspath(reverse_filename)
                    )
                    outputs["reverse_invert_flags"].insert(0, reverse_inversemode)
                    transform_count += 1
            else:
                transform_count = 0
                is_linear = [
                    t in self._linear_transform_names for t in self.inputs.transforms
                ]
                collapse_list = []

                if isdefined(self.inputs.initial_moving_transform) or isdefined(
                    self.inputs.initial_moving_transform_com
                ):
                    is_linear.insert(0, True)

                # Only files returned by collapse_output_transforms
                if any(is_linear):
                    collapse_list.append("GenericAffine")
                if not all(is_linear):
                    collapse_list.append("SyN")

                for transform in collapse_list:
                    forward_filename, forward_inversemode = self._output_filenames(
                        self.inputs.output_transform_prefix,
                        transform_count,
                        transform,
                        inverse=False,
                    )
                    reverse_filename, reverse_inversemode = self._output_filenames(
                        self.inputs.output_transform_prefix,
                        transform_count,
                        transform,
                        inverse=True,
                    )
                    outputs["forward_transforms"].append(
                        os.path.abspath(forward_filename)
                    )
                    outputs["forward_invert_flags"].append(forward_inversemode)
                    outputs["reverse_transforms"].append(
                        os.path.abspath(reverse_filename)
                    )
                    outputs["reverse_invert_flags"].append(reverse_inversemode)
                    transform_count += 1

        out_filename = self._get_outputfilenames(inverse=False)
        inv_out_filename = self._get_outputfilenames(inverse=True)
        if out_filename:
            outputs["warped_image"] = os.path.abspath(out_filename)
        if inv_out_filename:
            outputs["inverse_warped_image"] = os.path.abspath(inv_out_filename)
        if len(self.inputs.save_state):
            outputs["save_state"] = os.path.abspath(self.inputs.save_state)
        if self._metric_value:
            outputs["metric_value"] = self._metric_value
        if self._elapsed_time:
            outputs["elapsed_time"] = self._elapsed_time

        outputs["reverse_forward_transforms"] = outputs["forward_transforms"][::-1]
        outputs["reverse_forward_invert_flags"] = outputs["forward_invert_flags"][::-1]

        return outputs


class MeasureImageSimilarityInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        2,
        3,
        4,
        argstr="--dimensionality %d",
        position=1,
        desc="Dimensionality of the fixed/moving image pair",
    )
    fixed_image = File(
        exists=True, mandatory=True, desc="Image to which the moving image is warped"
    )
    moving_image = File(
        exists=True,
        mandatory=True,
        desc="Image to apply transformation to (generally a coregistered functional)",
    )
    metric = traits.Enum(
        "CC", "MI", "Mattes", "MeanSquares", "Demons", "GC", argstr="%s", mandatory=True
    )
    metric_weight = traits.Float(
        requires=["metric"],
        default_value=1.0,
        usedefault=True,
        desc='The "metricWeight" variable is not used.',
    )
    radius_or_number_of_bins = traits.Int(
        requires=["metric"],
        mandatory=True,
        desc="The number of bins in each stage for the MI and Mattes metric, "
        "or the radius for other metrics",
    )
    sampling_strategy = traits.Enum(
        "None",
        "Regular",
        "Random",
        requires=["metric"],
        usedefault=True,
        desc="Manner of choosing point set over which to optimize the metric. "
        'Defaults to "None" (i.e. a dense sampling of one sample per voxel).',
    )
    sampling_percentage = traits.Either(
        traits.Range(low=0.0, high=1.0),
        requires=["metric"],
        mandatory=True,
        desc="Percentage of points accessible to the sampling strategy over which "
        "to optimize the metric.",
    )
    fixed_image_mask = File(
        exists=True,
        argstr="%s",
        desc="mask used to limit metric sampling region of the fixed image",
    )
    moving_image_mask = File(
        exists=True,
        requires=["fixed_image_mask"],
        desc="mask used to limit metric sampling region of the moving image",
    )


class MeasureImageSimilarityOutputSpec(TraitedSpec):
    similarity = traits.Float()


class MeasureImageSimilarity(ANTSCommand):
    """


    Examples
    --------

    >>> from nipype.interfaces.ants import MeasureImageSimilarity
    >>> sim = MeasureImageSimilarity()
    >>> sim.inputs.dimension = 3
    >>> sim.inputs.metric = 'MI'
    >>> sim.inputs.fixed_image = 'T1.nii'
    >>> sim.inputs.moving_image = 'resting.nii'
    >>> sim.inputs.metric_weight = 1.0
    >>> sim.inputs.radius_or_number_of_bins = 5
    >>> sim.inputs.sampling_strategy = 'Regular'
    >>> sim.inputs.sampling_percentage = 1.0
    >>> sim.inputs.fixed_image_mask = 'mask.nii'
    >>> sim.inputs.moving_image_mask = 'mask.nii.gz'
    >>> sim.cmdline
    'MeasureImageSimilarity --dimensionality 3 --masks ["mask.nii","mask.nii.gz"] \
--metric MI["T1.nii","resting.nii",1.0,5,Regular,1.0]'
    """

    _cmd = "MeasureImageSimilarity"
    input_spec = MeasureImageSimilarityInputSpec
    output_spec = MeasureImageSimilarityOutputSpec

    def _metric_constructor(self):
        retval = (
            '--metric {metric}["{fixed_image}","{moving_image}",{metric_weight},'
            "{radius_or_number_of_bins},{sampling_strategy},{sampling_percentage}]".format(
                metric=self.inputs.metric,
                fixed_image=self.inputs.fixed_image,
                moving_image=self.inputs.moving_image,
                metric_weight=self.inputs.metric_weight,
                radius_or_number_of_bins=self.inputs.radius_or_number_of_bins,
                sampling_strategy=self.inputs.sampling_strategy,
                sampling_percentage=self.inputs.sampling_percentage,
            )
        )
        return retval

    def _mask_constructor(self):
        if self.inputs.moving_image_mask:
            retval = '--masks ["{fixed_image_mask}","{moving_image_mask}"]'.format(
                fixed_image_mask=self.inputs.fixed_image_mask,
                moving_image_mask=self.inputs.moving_image_mask,
            )
        else:
            retval = '--masks "{fixed_image_mask}"'.format(
                fixed_image_mask=self.inputs.fixed_image_mask
            )
        return retval

    def _format_arg(self, opt, spec, val):
        if opt == "metric":
            return self._metric_constructor()
        elif opt == "fixed_image_mask":
            return self._mask_constructor()
        return super(MeasureImageSimilarity, self)._format_arg(opt, spec, val)

    def aggregate_outputs(self, runtime=None, needed_outputs=None):
        outputs = self._outputs()
        stdout = runtime.stdout.split("\n")
        outputs.similarity = float(stdout[0])
        return outputs


class RegistrationSynQuickInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3, 2, argstr="-d %d", usedefault=True, desc="image dimension (2 or 3)"
    )
    fixed_image = InputMultiPath(
        File(exists=True),
        mandatory=True,
        argstr="-f %s...",
        desc="Fixed image or source image or reference image",
    )
    moving_image = InputMultiPath(
        File(exists=True),
        mandatory=True,
        argstr="-m %s...",
        desc="Moving image or target image",
    )
    output_prefix = Str(
        "transform",
        usedefault=True,
        argstr="-o %s",
        desc="A prefix that is prepended to all output files",
    )
    num_threads = traits.Int(
        default_value=LOCAL_DEFAULT_NUMBER_OF_THREADS,
        usedefault=True,
        desc="Number of threads (default = 1)",
        argstr="-n %d",
    )

    transform_type = traits.Enum(
        "s",
        "t",
        "r",
        "a",
        "sr",
        "b",
        "br",
        argstr="-t %s",
        desc="""\
Transform type

  * t:  translation
  * r:  rigid
  * a:  rigid + affine
  * s:  rigid + affine + deformable syn (default)
  * sr: rigid + deformable syn
  * b:  rigid + affine + deformable b-spline syn
  * br: rigid + deformable b-spline syn

""",
        usedefault=True,
    )

    use_histogram_matching = traits.Bool(
        False, argstr="-j %d", desc="use histogram matching"
    )
    histogram_bins = traits.Int(
        default_value=32,
        usedefault=True,
        argstr="-r %d",
        desc="histogram bins for mutual information in SyN stage \
                                 (default = 32)",
    )
    spline_distance = traits.Int(
        default_value=26,
        usedefault=True,
        argstr="-s %d",
        desc="spline distance for deformable B-spline SyN transform \
                                 (default = 26)",
    )
    precision_type = traits.Enum(
        "double",
        "float",
        argstr="-p %s",
        desc="precision type (default = double)",
        usedefault=True,
    )
    random_seed = traits.Int(
        argstr="-e %d",
        desc="fixed random seed",
        min_ver="2.3.0",
    )


class RegistrationSynQuickOutputSpec(TraitedSpec):
    warped_image = File(exists=True, desc="Warped image")
    inverse_warped_image = File(exists=True, desc="Inverse warped image")
    out_matrix = File(exists=True, desc="Affine matrix")
    forward_warp_field = File(exists=True, desc="Forward warp field")
    inverse_warp_field = File(exists=True, desc="Inverse warp field")


class RegistrationSynQuick(ANTSCommand):
    """
    Registration using a symmetric image normalization method (SyN).
    You can read more in Avants et al.; Med Image Anal., 2008
    (https://www.ncbi.nlm.nih.gov/pubmed/17659998).

    Examples
    --------

    >>> from nipype.interfaces.ants import RegistrationSynQuick
    >>> reg = RegistrationSynQuick()
    >>> reg.inputs.fixed_image = 'fixed1.nii'
    >>> reg.inputs.moving_image = 'moving1.nii'
    >>> reg.inputs.num_threads = 2
    >>> reg.cmdline
    'antsRegistrationSyNQuick.sh -d 3 -f fixed1.nii -r 32 -m moving1.nii -n 2 -o transform -p d -s 26 -t s'
    >>> reg.run()  # doctest: +SKIP

    example for multiple images

    >>> from nipype.interfaces.ants import RegistrationSynQuick
    >>> reg = RegistrationSynQuick()
    >>> reg.inputs.fixed_image = ['fixed1.nii', 'fixed2.nii']
    >>> reg.inputs.moving_image = ['moving1.nii', 'moving2.nii']
    >>> reg.inputs.num_threads = 2
    >>> reg.cmdline
    'antsRegistrationSyNQuick.sh -d 3 -f fixed1.nii -f fixed2.nii -r 32 -m moving1.nii -m moving2.nii \
-n 2 -o transform -p d -s 26 -t s'
    >>> reg.run()  # doctest: +SKIP
    """

    _cmd = "antsRegistrationSyNQuick.sh"
    input_spec = RegistrationSynQuickInputSpec
    output_spec = RegistrationSynQuickOutputSpec

    def _num_threads_update(self):
        """
        antsRegistrationSyNQuick.sh ignores environment variables,
        so override environment update from ANTSCommand class
        """
        pass

    def _format_arg(self, name, spec, value):
        if name == "precision_type":
            return spec.argstr % value[0]
        return super(RegistrationSynQuick, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        out_base = os.path.abspath(self.inputs.output_prefix)
        outputs["warped_image"] = out_base + "Warped.nii.gz"
        outputs["inverse_warped_image"] = out_base + "InverseWarped.nii.gz"
        outputs["out_matrix"] = out_base + "0GenericAffine.mat"

        if self.inputs.transform_type not in ("t", "r", "a"):
            outputs["forward_warp_field"] = out_base + "1Warp.nii.gz"
            outputs["inverse_warp_field"] = out_base + "1InverseWarp.nii.gz"
        return outputs


class CompositeTransformUtilInputSpec(ANTSCommandInputSpec):
    process = traits.Enum(
        "assemble",
        "disassemble",
        argstr="--%s",
        position=1,
        usedefault=True,
        desc="What to do with the transform inputs (assemble or disassemble)",
    )
    out_file = File(
        exists=False,
        argstr="%s",
        position=2,
        desc="Output file path (only used for disassembly).",
    )
    in_file = InputMultiPath(
        File(exists=True),
        mandatory=True,
        argstr="%s...",
        position=3,
        desc="Input transform file(s)",
    )
    output_prefix = Str(
        "transform",
        usedefault=True,
        argstr="%s",
        position=4,
        desc="A prefix that is prepended to all output files (only used for assembly).",
    )


class CompositeTransformUtilOutputSpec(TraitedSpec):
    affine_transform = File(desc="Affine transform component")
    displacement_field = File(desc="Displacement field component")
    out_file = File(desc="Compound transformation file")


class CompositeTransformUtil(ANTSCommand):
    """
    ANTs utility which can combine or break apart transform files into their individual
    constituent components.

    Examples
    --------

    >>> from nipype.interfaces.ants import CompositeTransformUtil
    >>> tran = CompositeTransformUtil()
    >>> tran.inputs.process = 'disassemble'
    >>> tran.inputs.in_file = 'output_Composite.h5'
    >>> tran.cmdline
    'CompositeTransformUtil --disassemble output_Composite.h5 transform'
    >>> tran.run()  # doctest: +SKIP

    example for assembling transformation files

    >>> from nipype.interfaces.ants import CompositeTransformUtil
    >>> tran = CompositeTransformUtil()
    >>> tran.inputs.process = 'assemble'
    >>> tran.inputs.out_file = 'my.h5'
    >>> tran.inputs.in_file = ['AffineTransform.mat', 'DisplacementFieldTransform.nii.gz']
    >>> tran.cmdline
    'CompositeTransformUtil --assemble my.h5 AffineTransform.mat DisplacementFieldTransform.nii.gz '
    >>> tran.run()  # doctest: +SKIP
    """

    _cmd = "CompositeTransformUtil"
    input_spec = CompositeTransformUtilInputSpec
    output_spec = CompositeTransformUtilOutputSpec

    def _num_threads_update(self):
        """
        CompositeTransformUtil ignores environment variables,
        so override environment update from ANTSCommand class
        """
        pass

    def _format_arg(self, name, spec, value):
        if name == "output_prefix" and self.inputs.process == "assemble":
            return ""
        if name == "out_file" and self.inputs.process == "disassemble":
            return ""
        return super(CompositeTransformUtil, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if self.inputs.process == "disassemble":
            outputs["affine_transform"] = os.path.abspath(
                "00_{}_AffineTransform.mat".format(self.inputs.output_prefix)
            )
            outputs["displacement_field"] = os.path.abspath(
                "01_{}_DisplacementFieldTransform.nii.gz".format(
                    self.inputs.output_prefix
                )
            )
        if self.inputs.process == "assemble":
            outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs
