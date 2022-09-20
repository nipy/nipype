# -*- coding: utf-8 -*-

import os

from ...utils.filemanip import split_filename
from ..base import (
    CommandLineInputSpec,
    CommandLine,
    traits,
    TraitedSpec,
    File,
    Directory,
    StdOutCommandLine,
    StdOutCommandLineInputSpec,
    isdefined,
    InputMultiPath,
)


class DTIFitInputSpec(StdOutCommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=1,
        desc="voxel-order data filename",
    )

    bgmask = File(
        argstr="-bgmask %s",
        exists=True,
        desc=(
            "Provides the name of a file containing a background mask computed using, "
            "for example, FSL bet2 program. The mask file contains zero in background "
            "voxels and non-zero in foreground."
        ),
    )

    scheme_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=2,
        desc="Camino scheme file (b values / vectors, see camino.fsl2scheme)",
    )

    non_linear = traits.Bool(
        argstr="-nonlinear",
        position=3,
        desc="Use non-linear fitting instead of the default linear regression "
        "to the log measurements. ",
    )


class DTIFitOutputSpec(TraitedSpec):
    tensor_fitted = File(exists=True, desc="path/name of 4D volume in voxel order")


class DTIFit(StdOutCommandLine):
    """
    Reads diffusion MRI data, acquired using the acquisition scheme detailed in the scheme file,
    from the data file.

    Use non-linear fitting instead of the default linear regression to the log measurements.
    The data file stores the diffusion MRI data in voxel order with the measurements stored
    in big-endian format and ordered as in the scheme file.
    The default input data type is four-byte float.
    The default output data type is eight-byte double.
    See modelfit and camino for the format of the data file and scheme file.
    The program fits the diffusion tensor to each voxel and outputs the results,
    in voxel order and as big-endian eight-byte doubles, to the standard output.
    The program outputs eight values in each voxel:
    [exit code, ln(S(0)), D_xx, D_xy, D_xz, D_yy, D_yz, D_zz].
    An exit code of zero indicates no problems.
    For a list of other exit codes, see modelfit(1).
    The entry S(0) is an estimate of the signal at q=0.

    Example
    -------
    >>> import nipype.interfaces.camino as cmon
    >>> fit = cmon.DTIFit()
    >>> fit.inputs.scheme_file = 'A.scheme'
    >>> fit.inputs.in_file = 'tensor_fitted_data.Bdouble'
    >>> fit.run()                  # doctest: +SKIP

    """

    _cmd = "dtfit"
    input_spec = DTIFitInputSpec
    output_spec = DTIFitOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["tensor_fitted"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + "_DT.Bdouble"


class DTMetricInputSpec(CommandLineInputSpec):
    eigen_data = File(
        exists=True,
        argstr="-inputfile %s",
        mandatory=True,
        desc="voxel-order data filename",
    )

    metric = traits.Enum(
        "fa",
        "md",
        "rd",
        "l1",
        "l2",
        "l3",
        "tr",
        "ra",
        "2dfa",
        "cl",
        "cp",
        "cs",
        argstr="-stat %s",
        mandatory=True,
        desc="Specifies the metric to compute.",
    )

    inputdatatype = traits.Enum(
        "double",
        "float",
        "long",
        "int",
        "short",
        "char",
        argstr="-inputdatatype %s",
        usedefault=True,
        desc="Specifies the data type of the input data.",
    )

    outputdatatype = traits.Enum(
        "double",
        "float",
        "long",
        "int",
        "short",
        "char",
        argstr="-outputdatatype %s",
        usedefault=True,
        desc="Specifies the data type of the output data.",
    )

    data_header = File(
        argstr="-header %s",
        exists=True,
        desc=(
            "A Nifti .nii or .nii.gz file containing the header information. "
            "Usually this will be the header of the raw data file from which "
            "the diffusion tensors were reconstructed."
        ),
    )

    outputfile = File(
        argstr="-outputfile %s",
        genfile=True,
        desc=(
            "Output name. Output will be a .nii.gz file if data_header is provided and"
            "in voxel order with outputdatatype datatype (default: double) otherwise."
        ),
    )


class DTMetricOutputSpec(TraitedSpec):
    metric_stats = File(
        exists=True, desc="Diffusion Tensor statistics of the chosen metric"
    )


class DTMetric(CommandLine):
    """
    Computes tensor metric statistics based on the eigenvalues l1 >= l2 >= l3
    typically obtained from ComputeEigensystem.

    The full list of statistics is:

     - <cl> = (l1 - l2) / l1 , a measure of linearity
     - <cp> = (l2 - l3) / l1 , a measure of planarity
     - <cs> = l3 / l1 , a measure of isotropy
       with: cl + cp + cs = 1
     - <l1> = first eigenvalue
     - <l2> = second eigenvalue
     - <l3> = third eigenvalue
     - <tr> = l1 + l2 + l3
     - <md> = tr / 3
     - <rd> = (l2 + l3) / 2
     - <fa> = fractional anisotropy. (Basser et al, J Magn Reson B 1996)
     - <ra> = relative anisotropy (Basser et al, J Magn Reson B 1996)
     - <2dfa> = 2D FA of the two minor eigenvalues l2 and l3
       i.e. sqrt( 2 * [(l2 - <l>)^2 + (l3 - <l>)^2] / (l2^2 + l3^2) )
       with: <l> = (l2 + l3) / 2


    Example
    -------
    Compute the CP planar metric as float data type.

    >>> import nipype.interfaces.camino as cam
    >>> dtmetric = cam.DTMetric()
    >>> dtmetric.inputs.eigen_data = 'dteig.Bdouble'
    >>> dtmetric.inputs.metric = 'cp'
    >>> dtmetric.inputs.outputdatatype = 'float'
    >>> dtmetric.run()                  # doctest: +SKIP

    """

    _cmd = "dtshape"
    input_spec = DTMetricInputSpec
    output_spec = DTMetricOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["metric_stats"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        return self._gen_outputfile()

    def _gen_outputfile(self):
        outputfile = self.inputs.outputfile
        if not isdefined(outputfile):
            outputfile = self._gen_filename("outputfile")
        return outputfile

    def _gen_filename(self, name):
        if name == "outputfile":
            _, name, _ = split_filename(self.inputs.eigen_data)
            metric = self.inputs.metric
            datatype = self.inputs.outputdatatype
            if isdefined(self.inputs.data_header):
                filename = name + "_" + metric + ".nii.gz"
            else:
                filename = name + "_" + metric + ".B" + datatype
        return filename


class ModelFitInputSpec(StdOutCommandLineInputSpec):
    def _gen_model_options():  # @NoSelf
        """
        Generate all possible permutations of < multi - tensor > < single - tensor > options
        """

        single_tensor = ["dt", "restore", "algdt", "nldt_pos", "nldt", "ldt_wtd"]
        multi_tensor = [
            "cylcyl",
            "cylcyl_eq",
            "pospos",
            "pospos_eq",
            "poscyl",
            "poscyl_eq",
            "cylcylcyl",
            "cylcylcyl_eq",
            "pospospos",
            "pospospos_eq",
            "posposcyl",
            "posposcyl_eq",
            "poscylcyl",
            "poscylcyl_eq",
        ]
        other = ["adc", "ball_stick"]

        model_list = single_tensor
        model_list.extend(other)
        model_list.extend(
            [multi + " " + single for multi in multi_tensor for single in single_tensor]
        )
        return model_list

    model = traits.Enum(
        _gen_model_options(),
        argstr="-model %s",
        mandatory=True,
        desc="Specifies the model to be fit to the data.",
    )

    in_file = File(
        exists=True,
        argstr="-inputfile %s",
        mandatory=True,
        desc="voxel-order data filename",
    )

    inputdatatype = traits.Enum(
        "float",
        "char",
        "short",
        "int",
        "long",
        "double",
        argstr="-inputdatatype %s",
        desc="Specifies the data type of the input file. "
        "The input file must have BIG-ENDIAN ordering. "
        "By default, the input type is ``float``.",
    )

    scheme_file = File(
        exists=True,
        argstr="-schemefile %s",
        mandatory=True,
        desc="Camino scheme file (b values / vectors, see camino.fsl2scheme)",
    )

    outputfile = File(argstr="-outputfile %s", desc="Filename of the output file.")

    outlier = File(
        argstr="-outliermap %s",
        exists=True,
        desc="Specifies the name of the file to contain the outlier map generated by "
        "the RESTORE algorithm.",
    )

    noisemap = File(
        argstr="-noisemap %s",
        exists=True,
        desc="Specifies the name of the file to contain the estimated noise variance on the "
        "diffusion-weighted signal, generated by a weighted tensor fit. "
        "The data type of this file is big-endian double.",
    )

    residualmap = File(
        argstr="-residualmap %s",
        exists=True,
        desc="Specifies the name of the file to contain the weighted residual errors after "
        "computing a weighted linear tensor fit. "
        "One value is produced per measurement, in voxel order. "
        "The data type of this file is big-endian double. "
        "Images of the residuals for each measurement can be extracted with shredder.",
    )

    sigma = traits.Float(
        argstr="-sigma %G",
        desc="Specifies the standard deviation of the noise in the data. "
        "Required by the RESTORE algorithm.",
    )

    bgthresh = traits.Float(
        argstr="-bgthresh %G",
        desc="Sets a threshold on the average q=0 measurement to separate "
        "foreground and background. The program does not process background voxels, "
        "but outputs the same number of values in background voxels and foreground voxels. "
        "Each value is zero in background voxels apart from the exit code which is -1.",
    )

    bgmask = File(
        argstr="-bgmask %s",
        exists=True,
        desc="Provides the name of a file containing a background mask computed using, "
        "for example, FSL's bet2 program. The mask file contains zero in background voxels "
        "and non-zero in foreground.",
    )

    cfthresh = traits.Float(
        argstr="-csfthresh %G",
        desc="Sets a threshold on the average q=0 measurement to determine which voxels "
        "are CSF. This program does not treat CSF voxels any different to other voxels.",
    )

    fixedmodq = traits.List(
        traits.Float,
        argstr="-fixedmod %s",
        minlen=4,
        maxlen=4,
        desc="Specifies <M> <N> <Q> <tau> a spherical acquisition scheme with M measurements "
        "with q=0 and N measurements with :math:`|q|=Q` and diffusion time tau. "
        "The N measurements with :math:`|q|=Q` have unique directions. The program reads in "
        "the directions from the files in directory PointSets.",
    )

    fixedbvalue = traits.List(
        traits.Float,
        argstr="-fixedbvalue %s",
        minlen=3,
        maxlen=3,
        desc="As above, but specifies <M> <N> <b>. The resulting scheme is the same whether "
        "you specify b directly or indirectly using -fixedmodq.",
    )

    tau = traits.Float(
        argstr="-tau %G",
        desc="Sets the diffusion time separately. This overrides the diffusion time "
        "specified in a scheme file or by a scheme index for both the acquisition scheme "
        "and in the data synthesis.",
    )


class ModelFitOutputSpec(TraitedSpec):
    fitted_data = File(exists=True, desc="output file of 4D volume in voxel order")


class ModelFit(StdOutCommandLine):
    """
    Fits models of the spin-displacement density to diffusion MRI measurements.

    This is an interface to various model fitting routines for diffusion MRI data that
    fit models of the spin-displacement density function. In particular, it will fit the
    diffusion tensor to a set of measurements as well as various other models including
    two or three-tensor models. The program can read input data from a file or can
    generate synthetic data using various test functions for testing and simulations.

    Example
    -------
    >>> import nipype.interfaces.camino as cmon
    >>> fit = cmon.ModelFit()
    >>> fit.model = 'dt'
    >>> fit.inputs.scheme_file = 'A.scheme'
    >>> fit.inputs.in_file = 'tensor_fitted_data.Bdouble'
    >>> fit.run()                  # doctest: +SKIP

    """

    _cmd = "modelfit"
    input_spec = ModelFitInputSpec
    output_spec = ModelFitOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["fitted_data"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + "_fit.Bdouble"


class DTLUTGenInputSpec(StdOutCommandLineInputSpec):
    lrange = traits.List(
        traits.Float,
        desc="Index to one-tensor LUTs. This is the ratio L1/L3 and L2 / L3."
        "The LUT is square, with half the values calculated (because L2 / L3 cannot be "
        "less than L1 / L3 by definition)."
        "The minimum must be >= 1. For comparison, a ratio L1 / L3 = 10 with L2 / L3 = 1 "
        "corresponds to an FA of 0.891, and L1 / L3 = 15 with L2 / L3 = 1 corresponds "
        "to an FA of 0.929. The default range is 1 to 10.",
        argstr="-lrange %s",
        minlen=2,
        maxlen=2,
        position=1,
        units="NA",
    )

    frange = traits.List(
        traits.Float,
        desc="Index to two-tensor LUTs. This is the fractional anisotropy"
        " of the two tensors. The default is 0.3 to 0.94",
        argstr="-frange %s",
        minlen=2,
        maxlen=2,
        position=1,
        units="NA",
    )

    step = traits.Float(
        argstr="-step %f",
        units="NA",
        desc="Distance between points in the LUT."
        "For example, if lrange is 1 to 10 and the step is 0.1, LUT entries will be computed "
        "at L1 / L3 = 1, 1.1, 1.2 ... 10.0 and at L2 / L3 = 1.0, 1.1 ... L1 / L3."
        "For single tensor LUTs, the default step is 0.2, for two-tensor LUTs it is 0.02.",
    )

    samples = traits.Int(
        argstr="-samples %d",
        units="NA",
        desc="The number of synthetic measurements to generate at each point in the LUT. "
        "The default is 2000.",
    )

    snr = traits.Float(
        argstr="-snr %f",
        units="NA",
        desc="The signal to noise ratio of the unweighted (q = 0) measurements."
        "This should match the SNR (in white matter) of the images that the LUTs are used with.",
    )

    bingham = traits.Bool(
        argstr="-bingham",
        desc="Compute a LUT for the Bingham PDF. This is the default.",
    )

    acg = traits.Bool(argstr="-acg", desc="Compute a LUT for the ACG PDF.")

    watson = traits.Bool(argstr="-watson", desc="Compute a LUT for the Watson PDF.")

    inversion = traits.Int(
        argstr="-inversion %d",
        units="NA",
        desc="Index of the inversion to use. The default is 1 (linear single tensor inversion).",
    )

    trace = traits.Float(
        argstr="-trace %G",
        units="NA",
        desc="Trace of the diffusion tensor(s) used in the test function in the LUT generation. "
        "The default is 2100E-12 m^2 s^-1.",
    )

    scheme_file = File(
        argstr="-schemefile %s",
        mandatory=True,
        position=2,
        desc="The scheme file of the images to be processed using this LUT.",
    )


class DTLUTGenOutputSpec(TraitedSpec):
    dtLUT = File(exists=True, desc="Lookup Table")


class DTLUTGen(StdOutCommandLine):
    """
    Calibrates the PDFs for PICo probabilistic tractography.

    This program needs to be run once for every acquisition scheme.
    It outputs a lookup table that is used by the dtpicoparams program to find PICo PDF
    parameters for an image.
    The default single tensor LUT contains parameters of the Bingham distribution and is
    generated by supplying a scheme file and an estimated signal to noise in white matter
    regions of the (q=0) image.
    The default inversion is linear (inversion index 1).

    Advanced users can control several options, including the extent and resolution of the LUT,
    the inversion index, and the type of PDF. See dtlutgen(1) for details.

    Example
    -------
    >>> import nipype.interfaces.camino as cmon
    >>> dtl = cmon.DTLUTGen()
    >>> dtl.inputs.snr = 16
    >>> dtl.inputs.scheme_file = 'A.scheme'
    >>> dtl.run()                  # doctest: +SKIP

    """

    _cmd = "dtlutgen"
    input_spec = DTLUTGenInputSpec
    output_spec = DTLUTGenOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["dtLUT"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.scheme_file)
        return name + ".dat"


class PicoPDFsInputSpec(StdOutCommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="< %s",
        mandatory=True,
        position=1,
        desc="voxel-order data filename",
    )

    inputmodel = traits.Enum(
        "dt",
        "multitensor",
        "pds",
        argstr="-inputmodel %s",
        position=2,
        desc="input model type",
        usedefault=True,
    )

    luts = InputMultiPath(
        File(exists=True),
        argstr="-luts %s",
        mandatory=True,
        desc="Files containing the lookup tables."
        "For tensor data, one lut must be specified for each type of inversion used in the "
        "image (one-tensor, two-tensor, three-tensor)."
        "For pds, the number of LUTs must match -numpds (it is acceptable to use the same "
        "LUT several times - see example, above)."
        "These LUTs may be generated with dtlutgen.",
    )

    pdf = traits.Enum(
        "bingham",
        "watson",
        "acg",
        argstr="-pdf %s",
        position=4,
        desc="""\
Specifies the PDF to use. There are three choices:

  * watson - The Watson distribution. This distribution is rotationally symmetric.
  * bingham - The Bingham distributionn, which allows elliptical probability density contours.
  * acg - The Angular Central Gaussian distribution, which also allows elliptical probability
    density contours.

""",
        usedefault=True,
    )

    directmap = traits.Bool(
        argstr="-directmap",
        desc="Only applicable when using pds as the inputmodel. Use direct mapping between "
        "the eigenvalues and the distribution parameters instead of the log of the eigenvalues.",
    )

    maxcomponents = traits.Int(
        argstr="-maxcomponents %d",
        units="NA",
        desc="The maximum number of tensor components in a voxel (default 2) for multitensor data."
        "Currently, only the default is supported, but future releases may allow the input "
        "of three-tensor data using this option.",
    )

    numpds = traits.Int(
        argstr="-numpds %d",
        units="NA",
        desc="The maximum number of PDs in a voxel (default 3) for PD data."
        "This option determines the size of the input and output voxels."
        "This means that the data file may be large enough to accommodate three or more PDs,"
        "but does not mean that any of the voxels are classified as containing three or more PDs.",
    )


class PicoPDFsOutputSpec(TraitedSpec):
    pdfs = File(exists=True, desc="path/name of 4D volume in voxel order")


class PicoPDFs(StdOutCommandLine):
    """
    Constructs a spherical PDF in each voxel for probabilistic tractography.

    Example
    -------
    >>> import nipype.interfaces.camino as cmon
    >>> pdf = cmon.PicoPDFs()
    >>> pdf.inputs.inputmodel = 'dt'
    >>> pdf.inputs.luts = ['lut_file']
    >>> pdf.inputs.in_file = 'voxel-order_data.Bfloat'
    >>> pdf.run()                  # doctest: +SKIP

    """

    _cmd = "picopdfs"
    input_spec = PicoPDFsInputSpec
    output_spec = PicoPDFsOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["pdfs"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + "_pdfs.Bdouble"


class TrackInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True, argstr="-inputfile %s", position=1, desc="input data file"
    )

    seed_file = File(exists=True, argstr="-seedfile %s", position=2, desc="seed file")

    inputmodel = traits.Enum(
        "dt",
        "multitensor",
        "sfpeak",
        "pico",
        "repbs_dt",
        "repbs_multitensor",
        "ballstick",
        "wildbs_dt",
        "bayesdirac",
        "bayesdirac_dt",
        "bedpostx_dyad",
        "bedpostx",
        argstr="-inputmodel %s",
        desc="input model type",
        usedefault=True,
    )

    tracker = traits.Enum(
        "fact",
        "euler",
        "rk4",
        argstr="-tracker %s",
        desc=(
            "The tracking algorithm controls streamlines are "
            "generated from the data. The choices are: "
            "- FACT, which follows the local fibre orientation "
            "in each voxel. No interpolation is used."
            "- EULER, which uses a fixed step size along the "
            "local fibre orientation. With nearest-neighbour "
            "interpolation, this method may be very similar to "
            "FACT, except that the step size is fixed, whereas "
            "FACT steps extend to the boundary of the next voxel "
            "(distance variable depending on the entry and exit "
            "points to the voxel)."
            "- RK4: Fourth-order Runge-Kutta method. The step "
            "size is fixed, however the eventual direction of "
            "the step is determined by taking and averaging a "
            "series of partial steps."
        ),
        usedefault=True,
    )

    interpolator = traits.Enum(
        "nn",
        "prob_nn",
        "linear",
        argstr="-interpolator %s",
        desc=(
            "The interpolation algorithm determines how "
            "the fiber orientation(s) are defined at a given "
            "continuous point within the input image. "
            "Interpolators are only used when the tracking "
            "algorithm is not FACT. The choices are: "
            "- NN: Nearest-neighbour interpolation, just "
            "uses the local voxel data directly."
            "- PROB_NN: Probabilistic nearest-neighbor "
            "interpolation,  similar  to the method pro- "
            "posed by Behrens et al [Magnetic Resonance "
            "in Medicine, 50:1077-1088, 2003]. The data "
            "is not interpolated, but at each point we "
            "randomly choose one of the 8 voxels sur- "
            "rounding a point. The probability of choosing "
            "a particular voxel is based on how close the "
            "point is to the centre of that voxel."
            "- LINEAR: Linear interpolation of the vector "
            "field containing the principal directions at "
            "each point."
        ),
    )

    stepsize = traits.Float(
        argstr="-stepsize %f",
        requires=["tracker"],
        desc=("Step size for EULER and RK4 tracking. " "The default is 1mm."),
    )

    inputdatatype = traits.Enum(
        "float", "double", argstr="-inputdatatype %s", desc="input file type"
    )

    gzip = traits.Bool(argstr="-gzip", desc="save the output image in gzip format")

    maxcomponents = traits.Int(
        argstr="-maxcomponents %d",
        units="NA",
        desc=(
            "The maximum number of tensor components in a "
            "voxel. This determines the size of the input "
            "file and does not say anything about the "
            "voxel classification. The default is 2 if "
            "the input model is multitensor and 1 if the "
            "input model is dt."
        ),
    )

    numpds = traits.Int(
        argstr="-numpds %d",
        units="NA",
        desc=(
            "The maximum number of PDs in a voxel for input "
            "models sfpeak and pico. The default is 3 for input "
            "model sfpeak and 1 for input model pico. This option "
            "determines the size of the voxels in the input file "
            "and does not affect tracking. For tensor data, use "
            "the -maxcomponents option."
        ),
    )

    data_dims = traits.List(
        traits.Int,
        desc="data dimensions in voxels",
        argstr="-datadims %s",
        minlen=3,
        maxlen=3,
        units="voxels",
    )

    voxel_dims = traits.List(
        traits.Float,
        desc="voxel dimensions in mm",
        argstr="-voxeldims %s",
        minlen=3,
        maxlen=3,
        units="mm",
    )

    ipthresh = traits.Float(
        argstr="-ipthresh %f",
        desc=(
            "Curvature threshold for tracking, expressed as "
            "the minimum dot product between two streamline "
            "orientations calculated over the length of a "
            "voxel. If the dot product between the previous "
            "and current directions is less than this "
            "threshold, then the streamline terminates. The "
            "default setting will terminate fibres that curve "
            "by more than 80 degrees. Set this to -1.0 to "
            "disable curvature checking completely."
        ),
    )

    curvethresh = traits.Float(
        argstr="-curvethresh %f",
        desc=(
            "Curvature threshold for tracking, expressed "
            "as the maximum angle (in degrees) between "
            "between two streamline orientations "
            "calculated over the length of a voxel. If "
            "the angle is greater than this, then the "
            "streamline terminates."
        ),
    )

    curveinterval = traits.Float(
        argstr="-curveinterval %f",
        requires=["curvethresh"],
        desc=(
            "Interval over which the curvature threshold "
            "should be evaluated, in mm. The default is "
            "5mm. When using the default curvature "
            "threshold of 90 degrees, this means that "
            "streamlines will terminate if they curve by "
            "more than  90  degrees over a path length "
            "of 5mm."
        ),
    )

    anisthresh = traits.Float(
        argstr="-anisthresh %f",
        desc=(
            "Terminate fibres that enter a voxel with lower "
            "anisotropy than the threshold."
        ),
    )

    anisfile = File(
        argstr="-anisfile %s",
        exists=True,
        desc=(
            "File containing the anisotropy map. This is required to "
            "apply an anisotropy threshold with non tensor data. If "
            "the map issupplied it is always used, even in tensor "
            "data."
        ),
    )

    outputtracts = traits.Enum(
        "float",
        "double",
        "oogl",
        argstr="-outputtracts %s",
        desc="output tract file type",
    )

    out_file = File(
        argstr="-outputfile %s", position=-1, genfile=True, desc="output data file"
    )

    output_root = File(
        exists=False,
        argstr="-outputroot %s",
        position=-1,
        desc="root directory for output",
    )


class TrackOutputSpec(TraitedSpec):
    tracked = File(exists=True, desc="output file containing reconstructed tracts")


class Track(CommandLine):
    """
    Performs tractography using one of the following models:
    dt', 'multitensor', 'pds', 'pico', 'bootstrap', 'ballstick', 'bayesdirac'

    Example
    -------
    >>> import nipype.interfaces.camino as cmon
    >>> track = cmon.Track()
    >>> track.inputs.inputmodel = 'dt'
    >>> track.inputs.in_file = 'data.Bfloat'
    >>> track.inputs.seed_file = 'seed_mask.nii'
    >>> track.run()                  # doctest: +SKIP

    """

    _cmd = "track"

    input_spec = TrackInputSpec
    output_spec = TrackOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_file):
            out_file_path = os.path.abspath(self.inputs.out_file)
        else:
            out_file_path = os.path.abspath(self._gen_outfilename())
        outputs["tracked"] = out_file_path
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        # Currently in_file is only undefined for bedpostx input
        if not isdefined(self.inputs.in_file):
            name = "bedpostx"
        else:
            _, name, _ = split_filename(self.inputs.in_file)
        return name + "_tracked"


class TrackDT(Track):
    """
    Performs streamline tractography using tensor data

    Example
    -------
    >>> import nipype.interfaces.camino as cmon
    >>> track = cmon.TrackDT()
    >>> track.inputs.in_file = 'tensor_fitted_data.Bdouble'
    >>> track.inputs.seed_file = 'seed_mask.nii'
    >>> track.run()                 # doctest: +SKIP

    """

    def __init__(self, command=None, **inputs):
        inputs["inputmodel"] = "dt"
        return super(TrackDT, self).__init__(command, **inputs)


class TrackPICoInputSpec(TrackInputSpec):
    pdf = traits.Enum(
        "bingham",
        "watson",
        "acg",
        argstr="-pdf %s",
        desc='Specifies the model for PICo parameters. The default is "bingham.',
    )

    iterations = traits.Int(
        argstr="-iterations %d",
        units="NA",
        desc="Number of streamlines to generate at each seed point. The default is 5000.",
    )


class TrackPICo(Track):
    """
    Performs streamline tractography using Probabilistic Index of Connectivity (PICo).

    Example
    -------
    >>> import nipype.interfaces.camino as cmon
    >>> track = cmon.TrackPICo()
    >>> track.inputs.in_file = 'pdfs.Bfloat'
    >>> track.inputs.seed_file = 'seed_mask.nii'
    >>> track.run()                  # doctest: +SKIP

    """

    input_spec = TrackPICoInputSpec

    def __init__(self, command=None, **inputs):
        inputs["inputmodel"] = "pico"
        return super(TrackPICo, self).__init__(command, **inputs)


class TrackBedpostxDeterInputSpec(TrackInputSpec):
    bedpostxdir = Directory(
        argstr="-bedpostxdir %s",
        mandatory=True,
        exists=True,
        desc=("Directory containing bedpostx output"),
    )

    min_vol_frac = traits.Float(
        argstr="-bedpostxminf %d",
        units="NA",
        desc=(
            "Zeros out compartments in bedpostx data "
            "with a mean volume fraction f of less than "
            "min_vol_frac.  The default is 0.01."
        ),
    )


class TrackBedpostxDeter(Track):
    """
    Data from FSL's bedpostx can be imported into Camino for deterministic tracking.
    (Use TrackBedpostxProba for bedpostx probabilistic tractography.)

    The tracking is based on the vector images dyads1.nii.gz, ... , dyadsN.nii.gz,
    where there are a maximum of N compartments (corresponding to each fiber
    population) in each voxel.

    It also uses the N images mean_f1samples.nii.gz, ..., mean_fNsamples.nii.gz,
    normalized such that the sum of all compartments is 1. Compartments where the
    mean_f is less than a threshold are discarded and not used for tracking.
    The default value is 0.01. This can be changed with the min_vol_frac option.

    Example
    -------
    >>> import nipype.interfaces.camino as cam
    >>> track = cam.TrackBedpostxDeter()
    >>> track.inputs.bedpostxdir = 'bedpostxout'
    >>> track.inputs.seed_file = 'seed_mask.nii'
    >>> track.run()                  # doctest: +SKIP

    """

    input_spec = TrackBedpostxDeterInputSpec

    def __init__(self, command=None, **inputs):
        inputs["inputmodel"] = "bedpostx_dyad"
        return super(TrackBedpostxDeter, self).__init__(command, **inputs)


class TrackBedpostxProbaInputSpec(TrackInputSpec):
    bedpostxdir = Directory(
        argstr="-bedpostxdir %s",
        mandatory=True,
        exists=True,
        desc=("Directory containing bedpostx output"),
    )

    min_vol_frac = traits.Float(
        argstr="-bedpostxminf %d",
        units="NA",
        desc=(
            "Zeros out compartments in bedpostx data "
            "with a mean volume fraction f of less than "
            "min_vol_frac.  The default is 0.01."
        ),
    )

    iterations = traits.Int(
        argstr="-iterations %d",
        units="NA",
        desc="Number of streamlines to generate at each seed point. The default is 1.",
    )


class TrackBedpostxProba(Track):
    """
    Data from FSL's bedpostx can be imported into Camino for probabilistic tracking.
    (Use TrackBedpostxDeter for bedpostx deterministic tractography.)

    The tracking uses the files merged_th1samples.nii.gz, merged_ph1samples.nii.gz,
    ... , merged_thNsamples.nii.gz, merged_phNsamples.nii.gz where there are a
    maximum of N compartments (corresponding to each fiber population) in each
    voxel. These images contain M samples of theta and phi, the polar coordinates
    describing the "stick" for each compartment. At each iteration, a random number
    X between 1 and M is drawn and the Xth samples of theta and phi become the
    principal directions in the voxel.

    It also uses the N images mean_f1samples.nii.gz, ..., mean_fNsamples.nii.gz,
    normalized such that the sum of all compartments is 1. Compartments where the
    mean_f is less than a threshold are discarded and not used for tracking.
    The default value is 0.01. This can be changed with the min_vol_frac option.

    Example
    -------
    >>> import nipype.interfaces.camino as cam
    >>> track = cam.TrackBedpostxProba()
    >>> track.inputs.bedpostxdir = 'bedpostxout'
    >>> track.inputs.seed_file = 'seed_mask.nii'
    >>> track.inputs.iterations = 100
    >>> track.run()                  # doctest: +SKIP

    """

    input_spec = TrackBedpostxProbaInputSpec

    def __init__(self, command=None, **inputs):
        inputs["inputmodel"] = "bedpostx"
        return super(TrackBedpostxProba, self).__init__(command, **inputs)


class TrackBayesDiracInputSpec(TrackInputSpec):
    scheme_file = File(
        argstr="-schemefile %s",
        mandatory=True,
        exists=True,
        desc=("The scheme file corresponding to the data being " "processed."),
    )

    iterations = traits.Int(
        argstr="-iterations %d",
        units="NA",
        desc=(
            "Number of streamlines to generate at each "
            "seed point. The default is 5000."
        ),
    )

    pdf = traits.Enum(
        "bingham",
        "watson",
        "acg",
        argstr="-pdf %s",
        desc="Specifies the model for PICo priors (not the curvature priors). "
        "The default is 'bingham'.",
    )

    pointset = traits.Int(
        argstr="-pointset %s",
        desc="""\
Index to the point set to use for Bayesian likelihood calculation. The index
specifies a set of evenly distributed points on the unit sphere, where each point x
defines two possible step directions (x or -x) for the streamline path. A larger
number indexes a larger point set, which gives higher angular resolution at the
expense of computation time. The default is index 1, which gives 1922 points, index 0
gives 1082 points, index 2 gives 3002 points.""",
    )

    datamodel = traits.Enum(
        "cylsymmdt",
        "ballstick",
        argstr="-datamodel %s",
        desc="""\
Model of the data for Bayesian tracking. The default model is "cylsymmdt", a diffusion
tensor with cylindrical symmetry about e_1, ie L1 >= L_2 = L_3. The other model is
"ballstick", the partial volume model (see ballstickfit).""",
    )

    curvepriork = traits.Float(
        argstr="-curvepriork %G",
        desc="""\
Concentration parameter for the prior distribution on fibre orientations given the fibre
orientation at the previous step. Larger values of k make curvature less likely.""",
    )

    curvepriorg = traits.Float(
        argstr="-curvepriorg %G",
        desc="""\
Concentration parameter for the prior distribution on fibre orientations given
the fibre orientation at the previous step. Larger values of g make curvature less likely.""",
    )

    extpriorfile = File(
        exists=True,
        argstr="-extpriorfile %s",
        desc="""\
Path to a PICo image produced by picopdfs. The PDF in each voxel is used as a prior for
the fibre orientation in Bayesian tracking. The prior image must be in the same space
as the diffusion data.""",
    )

    extpriordatatype = traits.Enum(
        "float",
        "double",
        argstr="-extpriordatatype %s",
        desc='Datatype of the prior image. The default is "double".',
    )


class TrackBayesDirac(Track):
    """
    Perform streamline tractography using a Bayesian tracking with Dirac priors.

    Example
    -------

    >>> import nipype.interfaces.camino as cmon
    >>> track = cmon.TrackBayesDirac()
    >>> track.inputs.in_file = 'tensor_fitted_data.Bdouble'
    >>> track.inputs.seed_file = 'seed_mask.nii'
    >>> track.inputs.scheme_file = 'bvecs.scheme'
    >>> track.run()                  # doctest: +SKIP

    """

    input_spec = TrackBayesDiracInputSpec

    def __init__(self, command=None, **inputs):
        inputs["inputmodel"] = "bayesdirac"
        return super(TrackBayesDirac, self).__init__(command, **inputs)


class TrackBallStick(Track):
    """
    Performs streamline tractography using ball-stick fitted data

    Example
    -------
    >>> import nipype.interfaces.camino as cmon
    >>> track = cmon.TrackBallStick()
    >>> track.inputs.in_file = 'ballstickfit_data.Bfloat'
    >>> track.inputs.seed_file = 'seed_mask.nii'
    >>> track.run()                  # doctest: +SKIP

    """

    def __init__(self, command=None, **inputs):
        inputs["inputmodel"] = "ballstick"
        return super(TrackBallStick, self).__init__(command, **inputs)


class TrackBootstrapInputSpec(TrackInputSpec):
    scheme_file = File(
        argstr="-schemefile %s",
        mandatory=True,
        exists=True,
        desc="The scheme file corresponding to the data being processed.",
    )

    iterations = traits.Int(
        argstr="-iterations %d",
        units="NA",
        desc="Number of streamlines to generate at each seed point.",
    )

    inversion = traits.Int(
        argstr="-inversion %s",
        desc="""\
Tensor reconstruction algorithm for repetition bootstrapping.
Default is 1 (linear reconstruction, single tensor).""",
    )

    bsdatafiles = traits.List(
        File(exists=True),
        mandatory=True,
        argstr="-bsdatafile %s",
        desc="""\
Specifies files containing raw data for repetition bootstrapping.
Use -inputfile for wild bootstrap data.""",
    )

    bgmask = File(
        argstr="-bgmask %s",
        exists=True,
        desc="""\
Provides the name of a file containing a background mask computed using, for example,
FSL's bet2 program.
The mask file contains zero in background voxels and non-zero in foreground.""",
    )


class TrackBootstrap(Track):
    """
    Performs bootstrap streamline tractography using multiple scans of the same subject

    Example
    -------
    >>> import nipype.interfaces.camino as cmon
    >>> track = cmon.TrackBootstrap()
    >>> track.inputs.inputmodel='repbs_dt'
    >>> track.inputs.scheme_file = 'bvecs.scheme'
    >>> track.inputs.bsdatafiles = ['fitted_data1.Bfloat', 'fitted_data2.Bfloat']
    >>> track.inputs.seed_file = 'seed_mask.nii'
    >>> track.run()                  # doctest: +SKIP

    """

    input_spec = TrackBootstrapInputSpec

    def __init__(self, command=None, **inputs):
        return super(TrackBootstrap, self).__init__(command, **inputs)


class ComputeMeanDiffusivityInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="< %s",
        mandatory=True,
        position=1,
        desc="Tensor-fitted data filename",
    )

    scheme_file = File(
        exists=True,
        argstr="%s",
        position=2,
        desc="Camino scheme file (b values / vectors, see camino.fsl2scheme)",
    )

    out_file = File(argstr="> %s", position=-1, genfile=True)

    inputmodel = traits.Enum(
        "dt",
        "twotensor",
        "threetensor",
        argstr="-inputmodel %s",
        desc="""\
Specifies the model that the input tensor data contains parameters for.
By default, the program assumes that the input data
contains a single diffusion tensor in each voxel.""",
    )

    inputdatatype = traits.Enum(
        "char",
        "short",
        "int",
        "long",
        "float",
        "double",
        argstr="-inputdatatype %s",
        desc="Specifies the data type of the input file.",
    )

    outputdatatype = traits.Enum(
        "char",
        "short",
        "int",
        "long",
        "float",
        "double",
        argstr="-outputdatatype %s",
        desc="Specifies the data type of the output data.",
    )


class ComputeMeanDiffusivityOutputSpec(TraitedSpec):
    md = File(exists=True, desc="Mean Diffusivity Map")


class ComputeMeanDiffusivity(StdOutCommandLine):
    """
    Computes the mean diffusivity (trace/3) from diffusion tensors.

    Example
    -------
    >>> import nipype.interfaces.camino as cmon
    >>> md = cmon.ComputeMeanDiffusivity()
    >>> md.inputs.in_file = 'tensor_fitted_data.Bdouble'
    >>> md.inputs.scheme_file = 'A.scheme'
    >>> md.run()                  # doctest: +SKIP

    """

    _cmd = "md"
    input_spec = ComputeMeanDiffusivityInputSpec
    output_spec = ComputeMeanDiffusivityOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["md"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + "_MD.img"  # Need to change to self.inputs.outputdatatype


class ComputeFractionalAnisotropyInputSpec(StdOutCommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="< %s",
        mandatory=True,
        position=1,
        desc="Tensor-fitted data filename",
    )

    scheme_file = File(
        exists=True,
        argstr="%s",
        position=2,
        desc="Camino scheme file (b values / vectors, see camino.fsl2scheme)",
    )

    inputmodel = traits.Enum(
        "dt",
        "twotensor",
        "threetensor",
        "multitensor",
        argstr="-inputmodel %s",
        desc="""\
Specifies the model that the input tensor data contains parameters for.
By default, the program assumes that the input data
contains a single diffusion tensor in each voxel.""",
    )

    inputdatatype = traits.Enum(
        "char",
        "short",
        "int",
        "long",
        "float",
        "double",
        argstr="-inputdatatype %s",
        desc="Specifies the data type of the input file.",
    )

    outputdatatype = traits.Enum(
        "char",
        "short",
        "int",
        "long",
        "float",
        "double",
        argstr="-outputdatatype %s",
        desc="Specifies the data type of the output data.",
    )


class ComputeFractionalAnisotropyOutputSpec(TraitedSpec):
    fa = File(exists=True, desc="Fractional Anisotropy Map")


class ComputeFractionalAnisotropy(StdOutCommandLine):
    """
    Computes the fractional anisotropy of tensors.

    Reads diffusion tensor (single, two-tensor or three-tensor) data from the standard input,
    computes the fractional anisotropy (FA) of each tensor and outputs the results to the
    standard output. For multiple-tensor data the program outputs the FA of each tensor,
    so for three-tensor data, for example, the output contains three fractional anisotropy
    values per voxel.

    Example
    -------
    >>> import nipype.interfaces.camino as cmon
    >>> fa = cmon.ComputeFractionalAnisotropy()
    >>> fa.inputs.in_file = 'tensor_fitted_data.Bdouble'
    >>> fa.inputs.scheme_file = 'A.scheme'
    >>> fa.run()                  # doctest: +SKIP

    """

    _cmd = "fa"
    input_spec = ComputeFractionalAnisotropyInputSpec
    output_spec = ComputeFractionalAnisotropyOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["fa"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + "_FA.Bdouble"  # Need to change to self.inputs.outputdatatype


class ComputeTensorTraceInputSpec(StdOutCommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="< %s",
        mandatory=True,
        position=1,
        desc="Tensor-fitted data filename",
    )

    scheme_file = File(
        exists=True,
        argstr="%s",
        position=2,
        desc="Camino scheme file (b values / vectors, see camino.fsl2scheme)",
    )

    inputmodel = traits.Enum(
        "dt",
        "twotensor",
        "threetensor",
        "multitensor",
        argstr="-inputmodel %s",
        desc="""\
Specifies the model that the input tensor data contains parameters for.
By default, the program assumes that the input data
contains a single diffusion tensor in each voxel.""",
    )

    inputdatatype = traits.Enum(
        "char",
        "short",
        "int",
        "long",
        "float",
        "double",
        argstr="-inputdatatype %s",
        desc="Specifies the data type of the input file.",
    )

    outputdatatype = traits.Enum(
        "char",
        "short",
        "int",
        "long",
        "float",
        "double",
        argstr="-outputdatatype %s",
        desc="Specifies the data type of the output data.",
    )


class ComputeTensorTraceOutputSpec(TraitedSpec):
    trace = File(exists=True, desc="Trace of the diffusion tensor")


class ComputeTensorTrace(StdOutCommandLine):
    """
    Computes the trace of tensors.

    Reads diffusion tensor (single, two-tensor or three-tensor) data from the standard input,
    computes the trace of each tensor, i.e., three times the mean diffusivity, and outputs
    the results to the standard output. For multiple-tensor data the program outputs the
    trace of each tensor, so for three-tensor data, for example, the output contains three
    values per voxel.

    Divide the output by three to get the mean diffusivity.

    Example
    -------
    >>> import nipype.interfaces.camino as cmon
    >>> trace = cmon.ComputeTensorTrace()
    >>> trace.inputs.in_file = 'tensor_fitted_data.Bdouble'
    >>> trace.inputs.scheme_file = 'A.scheme'
    >>> trace.run()                 # doctest: +SKIP

    """

    _cmd = "trd"
    input_spec = ComputeTensorTraceInputSpec
    output_spec = ComputeTensorTraceOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["trace"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + "_TrD.img"  # Need to change to self.inputs.outputdatatype


class ComputeEigensystemInputSpec(StdOutCommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="< %s",
        mandatory=True,
        position=1,
        desc="Tensor-fitted data filename",
    )

    inputmodel = traits.Enum(
        "dt",
        "multitensor",
        argstr="-inputmodel %s",
        desc="Specifies the model that the input data contains parameters for",
    )

    maxcomponents = traits.Int(
        argstr="-maxcomponents %d",
        desc="The maximum number of tensor components in a voxel of the input data.",
    )

    inputdatatype = traits.Enum(
        "double",
        "float",
        "long",
        "int",
        "short",
        "char",
        argstr="-inputdatatype %s",
        usedefault=True,
        desc=(
            "Specifies the data type of the input data. "
            "The data type can be any of the following strings: "
            '"char", "short", "int", "long", "float" or "double".'
            "Default is double data type"
        ),
    )

    outputdatatype = traits.Enum(
        "double",
        "float",
        "long",
        "int",
        "short",
        "char",
        argstr="-outputdatatype %s",
        usedefault=True,
        desc="Specifies the data type of the output data.",
    )


class ComputeEigensystemOutputSpec(TraitedSpec):
    eigen = File(exists=True, desc="Trace of the diffusion tensor")


class ComputeEigensystem(StdOutCommandLine):
    """
    Computes the eigensystem from tensor fitted data.

    Reads diffusion tensor (single, two-tensor, three-tensor or multitensor) data from the
    standard input, computes the eigenvalues and eigenvectors of each tensor and outputs the
    results to the standard output. For multiple-tensor data the program outputs the
    eigensystem of each tensor. For each tensor the program outputs: {l_1, e_11, e_12, e_13,
    l_2, e_21, e_22, e_33, l_3, e_31, e_32, e_33}, where l_1 >= l_2 >= l_3 and e_i = (e_i1,
    e_i2, e_i3) is the eigenvector with eigenvalue l_i. For three-tensor data, for example,
    the output contains thirty-six values per voxel.

    Example
    -------

    >>> import nipype.interfaces.camino as cmon
    >>> dteig = cmon.ComputeEigensystem()
    >>> dteig.inputs.in_file = 'tensor_fitted_data.Bdouble'
    >>> dteig.run()                  # doctest: +SKIP
    """

    _cmd = "dteig"
    input_spec = ComputeEigensystemInputSpec
    output_spec = ComputeEigensystemOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["eigen"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        datatype = self.inputs.outputdatatype
        return name + "_eig.B" + datatype
