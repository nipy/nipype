import os

from ...utils.filemanip import split_filename
from ..base import (
    traits,
    TraitedSpec,
    File,
    StdOutCommandLine,
    StdOutCommandLineInputSpec,
)


class QBallMXInputSpec(StdOutCommandLineInputSpec):
    basistype = traits.Enum(
        "rbf",
        "sh",
        argstr="-basistype %s",
        desc=(
            'Basis function type. "rbf" to use radial basis functions '
            '"sh" to use spherical harmonics'
        ),
        usedefault=True,
    )
    scheme_file = File(
        exists=True,
        argstr="-schemefile %s",
        mandatory=True,
        desc="Specifies the scheme file for the diffusion MRI data",
    )
    order = traits.Int(
        argstr="-order %d",
        units="NA",
        desc=(
            "Specific to sh. Maximum order of the spherical harmonic series. "
            "Default is 4."
        ),
    )
    rbfpointset = traits.Int(
        argstr="-rbfpointset %d",
        units="NA",
        desc=(
            "Specific to rbf. Sets the number of radial basis functions to use. "
            "The value specified must be present in the Pointsets directory. "
            "The default value is 246."
        ),
    )
    rbfsigma = traits.Float(
        argstr="-rbfsigma %f",
        units="NA",
        desc=(
            "Specific to rbf. Sets the width of the interpolating basis functions. "
            "The default value is 0.2618 (15 degrees)."
        ),
    )
    smoothingsigma = traits.Float(
        argstr="-smoothingsigma %f",
        units="NA",
        desc=(
            "Specific to rbf. Sets the width of the smoothing basis functions. "
            "The default value is 0.1309 (7.5 degrees)."
        ),
    )


class QBallMXOutputSpec(TraitedSpec):
    qmat = File(exists=True, desc="Q-Ball reconstruction matrix")


class QBallMX(StdOutCommandLine):
    """
    Generates a reconstruction matrix for Q-Ball. Used in LinRecon with
    the same scheme file to reconstruct data.

    Examples
    --------
    To create  a linear transform matrix using Spherical Harmonics (sh).

    >>> import nipype.interfaces.camino as cam
    >>> qballmx = cam.QBallMX()
    >>> qballmx.inputs.scheme_file = 'A.scheme'
    >>> qballmx.inputs.basistype = 'sh'
    >>> qballmx.inputs.order = 6
    >>> qballmx.run()            # doctest: +SKIP

    To create  a linear transform matrix using Radial Basis Functions
    (rbf). This command uses the default setting of rbf sigma = 0.2618
    (15 degrees), data smoothing sigma = 0.1309 (7.5 degrees), rbf
    pointset 246

    >>> import nipype.interfaces.camino as cam
    >>> qballmx = cam.QBallMX()
    >>> qballmx.inputs.scheme_file = 'A.scheme'
    >>> qballmx.run()              # doctest: +SKIP

    The linear transform matrix from any of these two examples can then
    be run over each voxel using LinRecon

    >>> qballcoeffs = cam.LinRecon()
    >>> qballcoeffs.inputs.in_file = 'SubjectA.Bfloat'
    >>> qballcoeffs.inputs.scheme_file = 'A.scheme'
    >>> qballcoeffs.inputs.qball_mat = 'A_qmat.Bdouble'
    >>> qballcoeffs.inputs.normalize = True
    >>> qballcoeffs.inputs.bgmask = 'brain_mask.nii'
    >>> qballcoeffs.run()             # doctest: +SKIP

    """

    _cmd = "qballmx"
    input_spec = QBallMXInputSpec
    output_spec = QBallMXOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["qmat"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.scheme_file)
        return name + "_qmat.Bdouble"


class LinReconInputSpec(StdOutCommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=1,
        desc="voxel-order data filename",
    )
    scheme_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=2,
        desc="Specifies the scheme file for the diffusion MRI data",
    )
    qball_mat = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=3,
        desc="Linear transformation matrix.",
    )
    normalize = traits.Bool(
        argstr="-normalize",
        desc=(
            "Normalize the measurements and discard "
            "the zero measurements before the linear transform."
        ),
    )
    log = traits.Bool(
        argstr="-log",
        desc=("Transform the log measurements rather than the measurements themselves"),
    )
    bgmask = File(exists=True, argstr="-bgmask %s", desc="background mask")


class LinReconOutputSpec(TraitedSpec):
    recon_data = File(exists=True, desc="Transformed data")


class LinRecon(StdOutCommandLine):
    """
    Runs a linear transformation in each voxel.

    Reads  a  linear  transformation from the matrix file assuming the
    imaging scheme specified in the scheme file. Performs the linear
    transformation on the data in every voxel and outputs the result to
    the standard output. The output in every voxel is actually: ::

        [exit code, ln(S(0)), p1, ..., pR]

    where p1, ..., pR are the parameters of the reconstruction.
    Possible exit codes are:

        - 0. No problems.
        - 6. Bad data replaced by substitution of zero.

    The matrix must be R by N+M where N+M is the number of measurements
    and R is the number of parameters of the reconstruction. The matrix
    file contains binary double-precision floats. The matrix elements
    are stored row by row.

    Example
    -------
    First run QBallMX and create a linear transform matrix using
    Spherical Harmonics (sh).

    >>> import nipype.interfaces.camino as cam
    >>> qballmx = cam.QBallMX()
    >>> qballmx.inputs.scheme_file = 'A.scheme'
    >>> qballmx.inputs.basistype = 'sh'
    >>> qballmx.inputs.order = 4
    >>> qballmx.run()            # doctest: +SKIP

    Then run it over each voxel using LinRecon

    >>> qballcoeffs = cam.LinRecon()
    >>> qballcoeffs.inputs.in_file = 'SubjectA.Bfloat'
    >>> qballcoeffs.inputs.scheme_file = 'A.scheme'
    >>> qballcoeffs.inputs.qball_mat = 'A_qmat.Bdouble'
    >>> qballcoeffs.inputs.normalize = True
    >>> qballcoeffs.run()         # doctest: +SKIP

    """

    _cmd = "linrecon"
    input_spec = LinReconInputSpec
    output_spec = LinReconOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["recon_data"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.scheme_file)
        return name + "_recondata.Bdouble"


class MESDInputSpec(StdOutCommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="-inputfile %s",
        mandatory=True,
        position=1,
        desc="voxel-order data filename",
    )
    inverter = traits.Enum(
        "SPIKE",
        "PAS",
        argstr="-filter %s",
        position=2,
        mandatory=True,
        desc="""
The inversion index specifies the type of inversion to perform on the data.
The currently available choices are:

  +----------------+---------------------------------------------+
  | Inverter name  | Inverter parameters                         |
  +================+=============================================+
  | SPIKE          | bd (b-value x diffusivity along the fibre.) |
  +----------------+---------------------------------------------+
  | PAS            | r                                           |
  +----------------+---------------------------------------------+

""",
    )
    inverter_param = traits.Float(
        argstr="%f",
        units="NA",
        position=3,
        mandatory=True,
        desc=(
            "Parameter associated with the inverter. Cf. inverter description for"
            "more information."
        ),
    )
    fastmesd = traits.Bool(
        argstr="-fastmesd",
        requires=["mepointset"],
        desc=(
            "Turns off numerical integration checks and fixes the integration point set size at that of"
            "the index specified by -basepointset.."
        ),
    )
    mepointset = traits.Int(
        argstr="-mepointset %d",
        units="NA",
        desc=(
            "Use a set of directions other than those in the scheme file for the deconvolution kernel."
            "The number refers to the number of directions on the unit sphere. For example, "
            '"-mepointset 54" uses the directions in "camino/PointSets/Elec054.txt".'
        ),
    )
    scheme_file = File(
        exists=True,
        argstr="-schemefile %s",
        mandatory=True,
        desc="Specifies the scheme file for the diffusion MRI data",
    )
    bgmask = File(exists=True, argstr="-bgmask %s", desc="background mask")
    inputdatatype = traits.Enum(
        "float",
        "char",
        "short",
        "int",
        "long",
        "double",
        argstr="-inputdatatype %s",
        desc=(
            'Specifies the data type of the input file: "char", "short", "int", "long",'
            '"float" or "double". The input file must have BIG-ENDIAN ordering.'
            'By default, the input type is "float".'
        ),
    )


class MESDOutputSpec(TraitedSpec):
    mesd_data = File(exists=True, desc="MESD data")


class MESD(StdOutCommandLine):
    """
    MESD is a general program for maximum entropy spherical deconvolution.
    It also runs PASMRI, which is a special case of spherical deconvolution.
    The input data must be in voxel order.

    The format of the output in each voxel is:
    { exitcode, ln(A^star(0)), lambda_0, lambda_1, ..., lambda_N }

    The  exitcode  contains  the  results of three tests. The first test thresholds
    the maximum relative error between the numerical integrals computed at con-
    vergence and those computed using a larger test point set; if the error is
    greater than a threshold the exitcode is increased from zero to one as a
    warning; if it is greater than a larger threshold the exitcode is increased to
    two to suggest failure. The  second  test  thresholds  the predicted  error in
    numerical integrals computed using the test point set; if the predicted error
    is greater than a threshold the exitcode is increased by 10. The third test
    thresholds the RMS error between the measurements and their predictions from
    the fitted deconvolution; if the errors are greater than a threshold, the exit
    code is increased by 100. An exitcode of 112 means that all three tests were
    failed and the result is likely to be unreliable.  If all is well the exitcode
    is zero. Results are often still reliable even if one or two of the tests are
    failed.

    Other possible exitcodes are:

        - 5 - The optimization failed to converge
        - -1 - Background
        - -100 - Something wrong in the MRI data, e.g. negative or zero measurements,
          so that the optimization could not run.

    The  standard  MESD  implementation  is computationally demanding, particularly
    as the number of measurements increases (computation is approximately O(N^2),
    where N is the number of measurements). There are two ways to obtain significant
    computational speed-up:

    i) Turn off error checks and use a small point set for computing numerical
    integrals in the algorithm by adding the flag -fastmesd. Sakaie CDMRI 2008
    shows that using the smallest point set  (-basepointset  0)  with  no
    error  checks  usually  has only a minor effect on the output of the algorithm,
    but provides a major reduction in computation time. You can increase the point
    set size using -basepointset with an argument higher than 0, which may produce
    better results in some voxels, but will increase computation time, which
    approximately doubles every time the point set index increases by 1.

    ii) Reduce the complexity of the maximum entropy encoding using -mepointset <X>.
    By default <X> = N, the number of measurements, and is the number of parameters
    in the max.  ent. representation of the  output  function, ie  the  number of
    lambda parameters, as described in Jansons and Alexander Inverse Problems 2003.
    However, we can represent the function using less components and <X> here
    specifies the number of lambda parameters. To obtain speed-up, set <X>
    < N; complexity become O(<X>^2) rather than O(N^2). Note that <X> must be chosen
    so that the camino/PointSets directory contains a point set  with  that  number
    of  elements.  When  -mepointset decreases, the  numerical  integration checks
    make less and less of a difference and smaller point sets for numerical
    integration (see -basepointset) become adequate. So when <X> is low -fastmesd is
    worth using to get even more speed-up.

    The choice of <X> is a parameter of the technique. Too low and you lose angular
    resoloution; too high and you see no computational benefit and may even suffer
    from overfitting. Empirically, we  have  found  that  <X>=16 often  gives  good
    results and good speed up, but it is worth trying a few values a comparing
    performance. The reduced encoding is described in the following ISMRM abstract:
    Sweet and Alexander "Reduced Encoding Persistent Angular Structure" 572 ISMRM 2010.

    Example
    -------
    Run MESD on every voxel of the data file SubjectA.Bfloat using the PASMRI kernel.

    >>> import nipype.interfaces.camino as cam
    >>> mesd = cam.MESD()
    >>> mesd.inputs.in_file = 'SubjectA.Bfloat'
    >>> mesd.inputs.scheme_file = 'A.scheme'
    >>> mesd.inputs.inverter = 'PAS'
    >>> mesd.inputs.inverter_param = 1.4
    >>> mesd.run()            # doctest: +SKIP

    """

    _cmd = "mesd"
    input_spec = MESDInputSpec
    output_spec = MESDOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["mesd_data"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.scheme_file)
        return name + "_MESD.Bdouble"


class SFPeaksInputSpec(StdOutCommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="-inputfile %s",
        mandatory=True,
        desc="Voxel-order data of spherical functions",
    )
    inputmodel = traits.Enum(
        "sh",
        "maxent",
        "rbf",
        argstr="-inputmodel %s",
        mandatory=True,
        desc=(
            "Type of functions input via in_file. Currently supported options are: "
            "  sh - Spherical harmonic series. Specify the maximum order of the SH series "
            '       with the "order" attribute if different from the default of 4. '
            "  maxent - Maximum entropy representations output by MESD. The reconstruction "
            "           directions input to MESD must be specified. By default this is the "
            "           same set of gradient directions (excluding zero gradients) in the "
            '           scheme file, so specify the "schemefile" attribute unless the '
            '           "mepointset" attribute was set in MESD. '
            "  rbf - Sums of radial basis functions. Specify the pointset with the attribute "
            '        "rbfpointset" if different from the default. See QBallMX.'
        ),
    )
    order = traits.Int(
        argstr="-order %d",
        units="NA",
        desc="Specific to sh. Maximum order of the spherical harmonic series.",
    )
    scheme_file = File(
        exists=True, argstr="%s", desc="Specific to maxent. Specifies the scheme file."
    )
    rbfpointset = traits.Int(
        argstr="-rbfpointset %d",
        units="NA",
        desc=(
            "Specific to rbf. Sets the number of radial basis functions to use. "
            "The value specified must be present in the Pointsets directory. "
            "The default value is 246."
        ),
    )
    mepointset = traits.Int(
        argstr="-mepointset %d",
        units="NA",
        desc=(
            "Use a set of directions other than those in the scheme file for the deconvolution "
            "kernel. The number refers to the number of directions on the unit sphere. "
            'For example, "mepointset = 54" uses the directions in "camino/PointSets/Elec054.txt" '
            "Use this option only if you told MESD to use a custom set of directions with the same "
            'option. Otherwise, specify the scheme file with the "schemefile" attribute.'
        ),
    )
    numpds = traits.Int(
        argstr="-numpds %d",
        units="NA",
        desc="The largest number of peak directions to output in each voxel.",
    )
    noconsistencycheck = traits.Bool(
        argstr="-noconsistencycheck",
        desc="Turns off the consistency check. The output shows all consistencies as true.",
    )
    searchradius = traits.Float(
        argstr="-searchradius %f",
        units="NA",
        desc='The search radius in the peak finding algorithm. The default is 0.4 (cf. "density")',
    )
    density = traits.Int(
        argstr="-density %d",
        units="NA",
        desc=(
            "The  number  of  randomly  rotated icosahedra to use in constructing the set of points for "
            "random sampling in the peak finding algorithm. Default is 1000, which works well for very "
            "spiky maxent functions. For other types of function, it is reasonable to set the density "
            "much lower and increase the search radius slightly, which speeds up the computation."
        ),
    )
    pointset = traits.Int(
        argstr="-pointset %d",
        units="NA",
        desc=(
            "To sample using an evenly distributed set of points instead. The integer can be "
            "0, 1, ..., 7. Index 0 gives 1082 points, 1 gives 1922, 2 gives 3002, 3 gives 4322, "
            "4 gives 5882, 5 gives 8672, 6 gives 12002, 7 gives 15872."
        ),
    )
    pdthresh = traits.Float(
        argstr="-pdthresh %f",
        units="NA",
        desc=(
            "Base threshold on the actual peak direction strength divided by the mean of the "
            "function.  The default is 1.0 (the peak must be equal or greater than the mean)."
        ),
    )
    stdsfrommean = traits.Float(
        argstr="-stdsfrommean %f",
        units="NA",
        desc=(
            "This is the number of standard deviations of the function to be added to the "
            '"pdthresh" attribute in the peak directions pruning.'
        ),
    )


class SFPeaksOutputSpec(TraitedSpec):
    peaks = File(exists=True, desc="Peaks of the spherical functions.")


class SFPeaks(StdOutCommandLine):
    """
    Finds the peaks of spherical functions.

    This utility reads coefficients of the spherical functions and
    outputs a list of peak directions of the function. It computes the
    value of the function at each of a set of sample points. Then it
    finds local maxima by finding all points at which the function is
    larger than for any other point within a fixed search radius (the
    default  is 0.4). The utility then uses Powell's algorithm to
    optimize the position of each local maximum. Finally the utility
    removes duplicates and tiny peaks with function value smaller than
    some threshold, which is the mean of the function plus some number
    of standard deviations. By default the program checks for con-
    sistency with a second set of starting points, but skips the
    optimization step. To speed up execution, you can turn off the con-
    sistency check by setting the noconsistencycheck flag to True.

    By  default, the utility constructs a set of sample points by
    randomly rotating a unit icosahedron repeatedly (the default is 1000
    times, which produces a set of 6000 points) and concatenating the
    lists of vertices. The 'pointset = <index>' attribute can tell the
    utility to use an evenly distributed set of points (index 0 gives
    1082 points, 1 gives 1922, 2 gives 4322, 3 gives 8672, 4 gives 15872,
    5 gives 32762, 6 gives 72032), which is quicker, because you can get
    away with fewer points. We estimate that you can use a factor of 2.5
    less evenly distributed points than randomly distributed points and
    still expect similar performance levels.

    The output for each voxel is:

    - exitcode (inherited from the input data).
    - ln(A(0))
    - number of peaks found.
    - flag for consistency with a repeated run (number of directions is
      the same and the directions are the same to within a threshold.)
    - mean(f).
    - std(f).
    - direction 1 (x, y, z, f, H00, H01, H10, H11).
    - direction 2 (x, y, z, f, H00, H01, H10, H11).
    - direction 3 (x, y, z, f, H00, H01, H10, H11).

    H is the Hessian of f at the peak. It is the matrix: ::

        [d^2f/ds^2 d^2f/dsdt]
        [d^2f/dtds d^2f/dt^2]
        = [H00 H01]
          [H10 H11]

    where s and t are orthogonal coordinates local to the peak.

    By default the maximum number of peak directions output in each
    voxel is three. If less than three directions are found, zeros are
    output for later directions. The peaks are ordered by the value of
    the function at the peak. If more than the maximum number of
    directions are found only the strongest ones are output. The maximum
    number can be changed setting the 'numpds' attribute.

    The utility can read various kinds of spherical function, but must
    be told what kind of function is input using the 'inputmodel'
    attribute. The description of the 'inputmodel' attribute lists
    additional information required by SFPeaks for each input model.


    Example
    -------
    First run QBallMX and create a linear transform matrix using
    Spherical Harmonics (sh).

    >>> import nipype.interfaces.camino as cam
    >>> sf_peaks = cam.SFPeaks()
    >>> sf_peaks.inputs.in_file = 'A_recon_params.Bdouble'
    >>> sf_peaks.inputs.inputmodel = 'sh'
    >>> sf_peaks.inputs.order = 4
    >>> sf_peaks.inputs.density = 100
    >>> sf_peaks.inputs.searchradius = 1.0
    >>> sf_peaks.run()          # doctest: +SKIP

    """

    _cmd = "sfpeaks"
    input_spec = SFPeaksInputSpec
    output_spec = SFPeaksOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["peaks"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + "_peaks.Bdouble"
