# -*- coding: utf-8 -*-

import os

from ...utils.filemanip import split_filename
from ..base import (
    traits,
    TraitedSpec,
    File,
    StdOutCommandLine,
    StdOutCommandLineInputSpec,
)


class SFPICOCalibDataInputSpec(StdOutCommandLineInputSpec):
    snr = traits.Float(
        argstr="-snr %f",
        units="NA",
        desc=(
            "Specifies  the  signal-to-noise ratio of the "
            "non-diffusion-weighted measurements to use in simulations."
        ),
    )
    scheme_file = File(
        exists=True,
        argstr="-schemefile %s",
        mandatory=True,
        desc="Specifies the scheme file for the diffusion MRI data",
    )
    info_file = File(
        desc="The name to be given to the information output filename.",
        argstr="-infooutputfile %s",
        mandatory=True,
        genfile=True,
        hash_files=False,
    )  # Genfile and hash_files?
    trace = traits.Float(
        argstr="-trace %f",
        units="NA",
        desc="Trace of the diffusion tensor(s) used in the test function.",
    )
    onedtfarange = traits.List(
        traits.Float,
        argstr="-onedtfarange %s",
        minlen=2,
        maxlen=2,
        units="NA",
        desc=("Minimum and maximum FA for the single tensor " "synthetic data."),
    )
    onedtfastep = traits.Float(
        argstr="-onedtfastep %f",
        units="NA",
        desc=(
            "FA step size controlling how many steps there are "
            "between the minimum and maximum FA settings."
        ),
    )
    twodtfarange = traits.List(
        traits.Float,
        argstr="-twodtfarange %s",
        minlen=2,
        maxlen=2,
        units="NA",
        desc=(
            "Minimum and maximum FA for the two tensor "
            "synthetic data. FA is varied for both tensors "
            "to give all the different permutations."
        ),
    )
    twodtfastep = traits.Float(
        argstr="-twodtfastep %f",
        units="NA",
        desc=(
            "FA step size controlling how many steps there are "
            "between the minimum and maximum FA settings "
            "for the two tensor cases."
        ),
    )
    twodtanglerange = traits.List(
        traits.Float,
        argstr="-twodtanglerange %s",
        minlen=2,
        maxlen=2,
        units="NA",
        desc=("Minimum and maximum crossing angles " "between the two fibres."),
    )
    twodtanglestep = traits.Float(
        argstr="-twodtanglestep %f",
        units="NA",
        desc=(
            "Angle step size controlling how many steps there are "
            "between the minimum and maximum crossing angles for "
            "the two tensor cases."
        ),
    )
    twodtmixmax = traits.Float(
        argstr="-twodtmixmax %f",
        units="NA",
        desc=(
            "Mixing parameter controlling the proportion of one fibre population "
            "to the other. The minimum mixing parameter is (1 - twodtmixmax)."
        ),
    )
    twodtmixstep = traits.Float(
        argstr="-twodtmixstep %f",
        units="NA",
        desc=(
            "Mixing parameter step size for the two tensor cases. "
            "Specify how many mixing parameter increments to use."
        ),
    )
    seed = traits.Float(
        argstr="-seed %f",
        units="NA",
        desc="Specifies the random seed to use for noise generation in simulation trials.",
    )


class SFPICOCalibDataOutputSpec(TraitedSpec):
    PICOCalib = File(exists=True, desc="Calibration dataset")
    calib_info = File(exists=True, desc="Calibration dataset")


class SFPICOCalibData(StdOutCommandLine):
    """
    Generates Spherical Function PICo Calibration Data.

    SFPICOCalibData creates synthetic data for use with SFLUTGen. The
    synthetic data is generated using a mixture of gaussians, in the
    same way datasynth generates data.  Each voxel of data models a
    slightly different fibre configuration (varying FA and fibre-
    crossings) and undergoes a random rotation to help account for any
    directional bias in the chosen acquisition scheme.  A second file,
    which stores information about the datafile, is generated along with
    the datafile.

    Examples
    --------
    To create a calibration dataset using the default settings

    >>> import nipype.interfaces.camino as cam
    >>> calib = cam.SFPICOCalibData()
    >>> calib.inputs.scheme_file = 'A.scheme'
    >>> calib.inputs.snr = 20
    >>> calib.inputs.info_file = 'PICO_calib.info'
    >>> calib.run()           # doctest: +SKIP

    The default settings create a large dataset (249,231 voxels), of
    which 3401 voxels contain a single fibre population per voxel and
    the rest of the voxels contain two fibre-populations. The amount of
    data produced can be varied by specifying the ranges and steps of
    the parameters for both the one and two fibre datasets used.

    To create a custom calibration dataset

    >>> import nipype.interfaces.camino as cam
    >>> calib = cam.SFPICOCalibData()
    >>> calib.inputs.scheme_file = 'A.scheme'
    >>> calib.inputs.snr = 20
    >>> calib.inputs.info_file = 'PICO_calib.info'
    >>> calib.inputs.twodtfarange = [0.3, 0.9]
    >>> calib.inputs.twodtfastep = 0.02
    >>> calib.inputs.twodtanglerange = [0, 0.785]
    >>> calib.inputs.twodtanglestep = 0.03925
    >>> calib.inputs.twodtmixmax = 0.8
    >>> calib.inputs.twodtmixstep = 0.1
    >>> calib.run()              # doctest: +SKIP

    This would provide 76,313 voxels of synthetic data, where 3401 voxels
    simulate the one fibre cases and 72,912 voxels simulate the various
    two fibre cases. However, care should be taken to ensure that enough
    data is generated for calculating the LUT.      # doctest: +SKIP

    """

    _cmd = "sfpicocalibdata"
    input_spec = SFPICOCalibDataInputSpec
    output_spec = SFPICOCalibDataOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["PICOCalib"] = os.path.abspath(self._gen_outfilename())
        outputs["calib_info"] = os.path.abspath(self.inputs.info_file)
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.scheme_file)
        return name + "_PICOCalib.Bfloat"


class SFLUTGenInputSpec(StdOutCommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="-inputfile %s",
        mandatory=True,
        desc="Voxel-order data of the spherical functions peaks.",
    )
    info_file = File(
        argstr="-infofile %s",
        mandatory=True,
        desc=(
            "The Info file that corresponds to the calibration "
            "datafile used in the reconstruction."
        ),
    )
    outputstem = traits.Str(
        "LUT",
        argstr="-outputstem %s",
        desc=(
            "Define the name of the generated luts.  The form of the filenames will be "
            "[outputstem]_oneFibreSurfaceCoeffs.Bdouble and "
            "[outputstem]_twoFibreSurfaceCoeffs.Bdouble"
        ),
        usedefault=True,
    )
    pdf = traits.Enum(
        "bingham",
        "watson",
        argstr="-pdf %s",
        desc="""\
Sets the distribution to use for the calibration. The default is the Bingham
distribution, which allows elliptical probability density contours.
Currently supported options are:

  * bingham -- The Bingham distribution, which allows elliptical probability
    density contours.
  * watson -- The Watson distribution. This distribution is rotationally symmetric.

""",
        usedefault=True,
    )
    binincsize = traits.Int(
        argstr="-binincsize %d",
        units="NA",
        desc=(
            "Sets the size of the bins.  In the case of 2D histograms such as the "
            "Bingham, the bins are always square. Default is 1."
        ),
    )
    minvectsperbin = traits.Int(
        argstr="-minvectsperbin %d",
        units="NA",
        desc=(
            "Specifies the minimum number of fibre-orientation estimates a bin "
            "must contain before it is used in the lut line/surface generation. "
            'Default is 50. If you get the error "no fibre-orientation estimates '
            'in histogram!", the calibration data set is too small to get enough '
            "samples in any of the  histogram  bins. You can decrease the minimum "
            "number  per  bin to get things running in quick tests, but the sta- "
            "tistics will not be reliable and for serious applications, you need  "
            "to increase the size of the calibration data set until the error goes."
        ),
    )
    directmap = traits.Bool(
        argstr="-directmap",
        desc=(
            "Use direct mapping between the eigenvalues and the distribution parameters "
            "instead of the log of the eigenvalues."
        ),
    )
    order = traits.Int(
        argstr="-order %d",
        units="NA",
        desc=(
            "The order of the polynomial fitting the surface. Order 1 is linear. "
            "Order 2 (default) is quadratic."
        ),
    )


class SFLUTGenOutputSpec(TraitedSpec):
    lut_one_fibre = File(exists=True, desc="PICo lut for one-fibre model")
    lut_two_fibres = File(exists=True, desc="PICo lut for two-fibre model")


class SFLUTGen(StdOutCommandLine):
    """
    Generates PICo lookup tables (LUT) for multi-fibre methods such as
    PASMRI and Q-Ball.

    SFLUTGen creates the lookup tables for the generalized multi-fibre
    implementation of the PICo tractography algorithm.  The outputs of
    this utility are either surface or line coefficients up to a given
    order. The calibration can be performed for different distributions,
    such as the Bingham and Watson distributions.

    This utility uses calibration data generated from SFPICOCalibData
    and peak information created by SFPeaks.

    The utility outputs two lut's, ``*_oneFibreSurfaceCoeffs.Bdouble`` and
    ``*_twoFibreSurfaceCoeffs.Bdouble``. Each of these files contains big-endian doubles
    as standard. The format of the output is::

          dimensions    (1 for Watson, 2 for Bingham)
          order         (the order of the polynomial)
          coefficient_1
          coefficient_2
          ...
          coefficient_N

    In  the case of the Watson, there is a single set of coefficients,
    which are ordered::

          constant, x, x^2, ..., x^order.

    In the case of the Bingham, there are two sets of coefficients (one
    for each surface), ordered so that::

          for j = 1 to order
            for k = 1 to order
              coeff_i = x^j * y^k
          where j+k < order

    Example
    -------
    To create a calibration dataset using the default settings

    >>> import nipype.interfaces.camino as cam
    >>> lutgen = cam.SFLUTGen()
    >>> lutgen.inputs.in_file = 'QSH_peaks.Bdouble'
    >>> lutgen.inputs.info_file = 'PICO_calib.info'
    >>> lutgen.run()        # doctest: +SKIP

    """

    _cmd = "sflutgen"
    input_spec = SFLUTGenInputSpec
    output_spec = SFLUTGenOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["lut_one_fibre"] = (
            self.inputs.outputstem + "_oneFibreSurfaceCoeffs.Bdouble"
        )
        outputs["lut_two_fibres"] = (
            self.inputs.outputstem + "_twoFibreSurfaceCoeffs.Bdouble"
        )
        return outputs

    def _gen_outfilename(self):
        return "/dev/null"
