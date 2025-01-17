# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft = python sts = 4 ts = 4 sw = 4 et:
"""
AFNI modeling interfaces.

Examples
--------
See the docstrings of the individual classes for examples.

"""

import os

from ..base import (
    TraitedSpec,
    traits,
    isdefined,
    File,
    InputMultiPath,
    Str,
    Tuple,
)

from .base import (
    AFNICommand,
    AFNICommandInputSpec,
    AFNICommandOutputSpec,
)


class DeconvolveInputSpec(AFNICommandInputSpec):
    in_files = InputMultiPath(
        File(exists=True),
        desc="filenames of 3D+time input datasets. More than one filename can "
        "be given and the datasets will be auto-catenated in time. "
        "You can input a 1D time series file here, but the time axis "
        "should run along the ROW direction, not the COLUMN direction as "
        "in the 'input1D' option.",
        argstr="-input %s",
        copyfile=False,
        sep=" ",
        position=1,
    )
    sat = traits.Bool(
        desc="check the dataset time series for initial saturation transients,"
        " which should normally have been excised before data analysis.",
        argstr="-sat",
        xor=["trans"],
    )
    trans = traits.Bool(
        desc="check the dataset time series for initial saturation transients,"
        " which should normally have been excised before data analysis.",
        argstr="-trans",
        xor=["sat"],
    )
    noblock = traits.Bool(
        desc="normally, if you input multiple datasets with 'input', then "
        "the separate datasets are taken to be separate image runs that "
        "get separate baseline models. Use this options if you want to "
        "have the program consider these to be all one big run."
        "* If any of the input dataset has only 1 sub-brick, then this "
        "option is automatically invoked!"
        "* If the auto-catenation feature isn't used, then this option "
        "has no effect, no how, no way.",
        argstr="-noblock",
    )
    force_TR = traits.Float(
        desc="use this value instead of the TR in the 'input' "
        "dataset. (It's better to fix the input using Refit.)",
        argstr="-force_TR %f",
        position=0,
    )
    input1D = File(
        desc="filename of single (fMRI) .1D time series where time runs down "
        "the column.",
        argstr="-input1D %s",
        exists=True,
    )
    TR_1D = traits.Float(
        desc="TR to use with 'input1D'. This option has no effect if you do "
        "not also use 'input1D'.",
        argstr="-TR_1D %f",
    )
    legendre = traits.Bool(
        desc="use Legendre polynomials for null hypothesis (baseline model)",
        argstr="-legendre",
    )
    nolegendre = traits.Bool(
        desc="use power polynomials for null hypotheses. Don't do this "
        "unless you are crazy!",
        argstr="-nolegendre",
    )
    nodmbase = traits.Bool(
        desc="don't de-mean baseline time series", argstr="-nodmbase"
    )
    dmbase = traits.Bool(
        desc="de-mean baseline time series (default if 'polort' >= 0)", argstr="-dmbase"
    )
    svd = traits.Bool(
        desc="use SVD instead of Gaussian elimination (default)", argstr="-svd"
    )
    nosvd = traits.Bool(desc="use Gaussian elimination instead of SVD", argstr="-nosvd")
    rmsmin = traits.Float(
        desc="minimum rms error to reject reduced model (default = 0; don't "
        "use this option normally!)",
        argstr="-rmsmin %f",
    )
    nocond = traits.Bool(
        desc="DON'T calculate matrix condition number", argstr="-nocond"
    )
    singvals = traits.Bool(
        desc="print out the matrix singular values", argstr="-singvals"
    )
    goforit = traits.Int(
        desc="use this to proceed even if the matrix has bad problems (e.g., "
        "duplicate columns, large condition number, etc.).",
        argstr="-GOFORIT %i",
    )
    allzero_OK = traits.Bool(
        desc="don't consider all zero matrix columns to be the type of error "
        "that 'gotforit' is needed to ignore.",
        argstr="-allzero_OK",
    )
    dname = Tuple(
        Str, Str, desc="set environmental variable to provided value", argstr="-D%s=%s"
    )
    mask = File(
        desc="filename of 3D mask dataset; only data time series from within "
        "the mask will be analyzed; results for voxels outside the mask "
        "will be set to zero.",
        argstr="-mask %s",
        exists=True,
    )
    automask = traits.Bool(
        desc="build a mask automatically from input data (will be slow for "
        "long time series datasets)",
        argstr="-automask",
    )
    STATmask = File(
        desc="build a mask from provided file, and use this mask for the "
        "purpose of reporting truncation-to float issues AND for "
        "computing the FDR curves. The actual results ARE not masked "
        "with this option (only with 'mask' or 'automask' options).",
        argstr="-STATmask %s",
        exists=True,
    )
    censor = File(
        desc="filename of censor .1D time series. This is a file of 1s and "
        "0s, indicating which time points are to be included (1) and "
        "which are to be excluded (0).",
        argstr="-censor %s",
        exists=True,
    )
    polort = traits.Int(
        desc="degree of polynomial corresponding to the null hypothesis "
        "[default: 1]",
        argstr="-polort %d",
    )
    ortvec = Tuple(
        File(desc="filename", exists=True),
        Str(desc="label"),
        desc="this option lets you input a rectangular array of 1 or more "
        "baseline vectors from a file. This method is a fast way to "
        "include a lot of baseline regressors in one step. ",
        argstr="-ortvec %s %s",
    )
    x1D = File(desc="specify name for saved X matrix", argstr="-x1D %s")
    x1D_stop = traits.Bool(
        desc="stop running after writing .xmat.1D file", argstr="-x1D_stop"
    )
    cbucket = traits.Str(
        desc="Name for dataset in which to save the regression "
        "coefficients (no statistics). This dataset "
        "will be used in a -xrestore run [not yet implemented] "
        "instead of the bucket dataset, if possible.",
        argstr="-cbucket %s",
    )
    out_file = File(desc="output statistics file", argstr="-bucket %s")
    num_threads = traits.Int(
        desc="run the program with provided number of sub-processes",
        argstr="-jobs %d",
        nohash=True,
    )
    fout = traits.Bool(desc="output F-statistic for each stimulus", argstr="-fout")
    rout = traits.Bool(
        desc="output the R^2 statistic for each stimulus", argstr="-rout"
    )
    tout = traits.Bool(desc="output the T-statistic for each stimulus", argstr="-tout")
    vout = traits.Bool(
        desc="output the sample variance (MSE) for each stimulus", argstr="-vout"
    )
    nofdr = traits.Bool(
        desc="Don't compute the statistic-vs-FDR curves for the bucket dataset.",
        argstr="-noFDR",
    )
    global_times = traits.Bool(
        desc="use global timing for stimulus timing files",
        argstr="-global_times",
        xor=["local_times"],
    )
    local_times = traits.Bool(
        desc="use local timing for stimulus timing files",
        argstr="-local_times",
        xor=["global_times"],
    )
    num_stimts = traits.Int(
        desc="number of stimulus timing files", argstr="-num_stimts %d", position=-6
    )
    stim_times = traits.List(
        Tuple(
            traits.Int(desc="k-th response model"),
            File(desc="stimulus timing file", exists=True),
            Str(desc="model"),
        ),
        desc="generate a response model from a set of stimulus times given in file.",
        argstr="-stim_times %d %s '%s'...",
        position=-5,
    )
    stim_label = traits.List(
        Tuple(traits.Int(desc="k-th input stimulus"), Str(desc="stimulus label")),
        desc="label for kth input stimulus (e.g., Label1)",
        argstr="-stim_label %d %s...",
        requires=["stim_times"],
        position=-4,
    )
    stim_times_subtract = traits.Float(
        desc="this option means to subtract specified seconds from each time "
        "encountered in any 'stim_times' option. The purpose of this "
        "option is to make it simple to adjust timing files for the "
        "removal of images from the start of each imaging run.",
        argstr="-stim_times_subtract %f",
    )
    num_glt = traits.Int(
        desc="number of general linear tests (i.e., contrasts)",
        argstr="-num_glt %d",
        position=-3,
    )
    gltsym = traits.List(
        Str(desc="symbolic general linear test"),
        desc="general linear tests (i.e., contrasts) using symbolic "
        "conventions (e.g., '+Label1 -Label2')",
        argstr="-gltsym 'SYM: %s'...",
        position=-2,
    )
    glt_label = traits.List(
        Tuple(traits.Int(desc="k-th general linear test"), Str(desc="GLT label")),
        desc="general linear test (i.e., contrast) labels",
        argstr="-glt_label %d %s...",
        requires=["gltsym"],
        position=-1,
    )


class DeconvolveOutputSpec(TraitedSpec):
    out_file = File(desc="output statistics file", exists=True)
    reml_script = File(
        desc="automatically generated script to run 3dREMLfit", exists=True
    )
    x1D = File(desc="save out X matrix", exists=True)
    cbucket = File(desc="output regression coefficients file (if generated)")


class Deconvolve(AFNICommand):
    """Performs OLS regression given a 4D neuroimage file and stimulus timings

    For complete details, see the `3dDeconvolve Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dDeconvolve.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> deconvolve = afni.Deconvolve()
    >>> deconvolve.inputs.in_files = ['functional.nii', 'functional2.nii']
    >>> deconvolve.inputs.out_file = 'output.nii'
    >>> deconvolve.inputs.x1D = 'output.1D'
    >>> stim_times = [(1, 'timeseries.txt', 'SPMG1(4)')]
    >>> deconvolve.inputs.stim_times = stim_times
    >>> deconvolve.inputs.stim_label = [(1, 'Houses')]
    >>> deconvolve.inputs.gltsym = ['SYM: +Houses']
    >>> deconvolve.inputs.glt_label = [(1, 'Houses')]
    >>> deconvolve.cmdline
    "3dDeconvolve -input functional.nii functional2.nii -bucket output.nii -x1D output.1D -num_stimts 1 -stim_times 1 timeseries.txt 'SPMG1(4)' -stim_label 1 Houses -num_glt 1 -gltsym 'SYM: +Houses' -glt_label 1 Houses"
    >>> res = deconvolve.run()  # doctest: +SKIP
    """

    _cmd = "3dDeconvolve"
    input_spec = DeconvolveInputSpec
    output_spec = DeconvolveOutputSpec

    def _format_arg(self, name, trait_spec, value):
        if name == "gltsym":
            for n, val in enumerate(value):
                if val.startswith("SYM: "):
                    value[n] = val.lstrip("SYM: ")

        return super()._format_arg(name, trait_spec, value)

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []
        if len(self.inputs.stim_times) and not isdefined(self.inputs.num_stimts):
            self.inputs.num_stimts = len(self.inputs.stim_times)
        if len(self.inputs.gltsym) and not isdefined(self.inputs.num_glt):
            self.inputs.num_glt = len(self.inputs.gltsym)
        if not isdefined(self.inputs.out_file):
            self.inputs.out_file = "Decon.nii"

        return super()._parse_inputs(skip)

    def _list_outputs(self):
        outputs = self.output_spec().get()

        _gen_fname_opts = {}
        _gen_fname_opts["basename"] = self.inputs.out_file
        _gen_fname_opts["cwd"] = os.getcwd()

        if isdefined(self.inputs.x1D):
            if not self.inputs.x1D.endswith(".xmat.1D"):
                outputs["x1D"] = os.path.abspath(self.inputs.x1D + ".xmat.1D")
            else:
                outputs["x1D"] = os.path.abspath(self.inputs.x1D)
        else:
            outputs["x1D"] = self._gen_fname(suffix=".xmat.1D", **_gen_fname_opts)

        if isdefined(self.inputs.cbucket):
            outputs["cbucket"] = os.path.abspath(self.inputs.cbucket)

        outputs["reml_script"] = self._gen_fname(suffix=".REML_cmd", **_gen_fname_opts)
        # remove out_file from outputs if x1d_stop set to True
        if self.inputs.x1D_stop:
            del outputs["out_file"], outputs["cbucket"]
        else:
            outputs["out_file"] = os.path.abspath(self.inputs.out_file)

        return outputs


class RemlfitInputSpec(AFNICommandInputSpec):
    # mandatory files
    in_files = InputMultiPath(
        File(exists=True),
        desc="Read time series dataset",
        argstr='-input "%s"',
        mandatory=True,
        copyfile=False,
        sep=" ",
    )
    matrix = File(
        desc="the design matrix file, which should have been output from "
        "Deconvolve via the 'x1D' option",
        argstr="-matrix %s",
        mandatory=True,
    )
    # "Semi-Hidden Alternative Ways to Define the Matrix"
    polort = traits.Int(
        desc="if no 'matrix' option is given, AND no 'matim' option, "
        "create a matrix with Legendre polynomial regressors"
        "up to the specified order. The default value is 0, which"
        "produces a matrix with a single column of all ones",
        argstr="-polort %d",
        xor=["matrix"],
    )
    matim = File(
        desc="read a standard file as the matrix. You can use only Col as "
        "a name in GLTs with these nonstandard matrix input methods, "
        "since the other names come from the 'matrix' file. "
        "These mutually exclusive options are ignored if 'matrix' "
        "is used.",
        argstr="-matim %s",
        xor=["matrix"],
    )
    # Other arguments
    mask = File(
        desc="filename of 3D mask dataset; only data time series from within "
        "the mask will be analyzed; results for voxels outside the mask "
        "will be set to zero.",
        argstr="-mask %s",
        exists=True,
    )
    automask = traits.Bool(
        usedefault=True,
        argstr="-automask",
        desc="build a mask automatically from input data (will be slow for "
        "long time series datasets)",
    )
    STATmask = File(
        desc="filename of 3D mask dataset to be used for the purpose "
        "of reporting truncation-to float issues AND for computing the "
        "FDR curves. The actual results ARE not masked with this option "
        "(only with 'mask' or 'automask' options).",
        argstr="-STATmask %s",
        exists=True,
    )
    addbase = InputMultiPath(
        File(exists=True, desc="file containing columns to add to regression matrix"),
        desc="file(s) to add baseline model columns to the matrix with this "
        "option. Each column in the specified file(s) will be appended "
        "to the matrix. File(s) must have at least as many rows as the "
        "matrix does.",
        copyfile=False,
        sep=" ",
        argstr="-addbase %s",
    )
    slibase = InputMultiPath(
        File(exists=True, desc="file containing columns to add to regression matrix"),
        desc="similar to 'addbase' in concept, BUT each specified file "
        "must have an integer multiple of the number of slices "
        "in the input dataset(s); then, separate regression "
        "matrices are generated for each slice, with the "
        "first column of the file appended to the matrix for "
        "the first slice of the dataset, the second column of the file "
        "appended to the matrix for the first slice of the dataset, "
        "and so on. Intended to help model physiological noise in FMRI, "
        "or other effects you want to regress out that might "
        "change significantly in the inter-slice time intervals. This "
        "will slow the program down, and make it use a lot more memory "
        "(to hold all the matrix stuff).",
        argstr="-slibase %s",
    )
    slibase_sm = InputMultiPath(
        File(exists=True, desc="file containing columns to add to regression matrix"),
        desc="similar to 'slibase', BUT each file much be in slice major "
        "order (i.e. all slice0 columns come first, then all slice1 "
        "columns, etc).",
        argstr="-slibase_sm %s",
    )
    usetemp = traits.Bool(
        desc="write intermediate stuff to disk, to economize on RAM. "
        "Using this option might be necessary to run with "
        "'slibase' and with 'Grid' values above the default, "
        "since the program has to store a large number of "
        "matrices for such a problem: two for every slice and "
        "for every (a,b) pair in the ARMA parameter grid. Temporary "
        "files are written to the directory given in environment "
        "variable TMPDIR, or in /tmp, or in ./ (preference is in that "
        "order)",
        argstr="-usetemp",
    )
    nodmbase = traits.Bool(
        desc="by default, baseline columns added to the matrix via "
        "'addbase' or 'slibase' or 'dsort' will each have their "
        "mean removed (as is done in Deconvolve); this option turns this "
        "centering off",
        argstr="-nodmbase",
        requires=["addbase", "dsort"],
    )
    dsort = File(
        desc="4D dataset to be used as voxelwise baseline regressor",
        exists=True,
        copyfile=False,
        argstr="-dsort %s",
    )
    dsort_nods = traits.Bool(
        desc="if 'dsort' option is used, this command will output "
        "additional results files excluding the 'dsort' file",
        argstr="-dsort_nods",
        requires=["dsort"],
    )
    fout = traits.Bool(desc="output F-statistic for each stimulus", argstr="-fout")
    rout = traits.Bool(
        desc="output the R^2 statistic for each stimulus", argstr="-rout"
    )
    tout = traits.Bool(
        desc="output the T-statistic for each stimulus; if you use "
        "'out_file' and do not give any of 'fout', 'tout',"
        "or 'rout', then the program assumes 'fout' is activated.",
        argstr="-tout",
    )
    nofdr = traits.Bool(
        desc="do NOT add FDR curve data to bucket datasets; FDR curves can "
        "take a long time if 'tout' is used",
        argstr="-noFDR",
    )
    nobout = traits.Bool(
        desc="do NOT add baseline (null hypothesis) regressor betas "
        "to the 'rbeta_file' and/or 'obeta_file' output datasets.",
        argstr="-nobout",
    )
    gltsym = traits.List(
        traits.Either(Tuple(File(exists=True), Str()), Tuple(Str(), Str())),
        desc="read a symbolic GLT from input file and associate it with a "
        "label. As in Deconvolve, you can also use the 'SYM:' method "
        "to provide the definition of the GLT directly as a string "
        "(e.g., with 'SYM: +Label1 -Label2'). Unlike Deconvolve, you "
        "MUST specify 'SYM: ' if providing the GLT directly as a "
        "string instead of from a file",
        argstr='-gltsym "%s" %s...',
    )
    out_file = File(
        desc="output dataset for beta + statistics from the REML estimation; "
        "also contains the results of any GLT analysis requested "
        "in the Deconvolve setup, similar to the 'bucket' output "
        "from Deconvolve. This dataset does NOT get the betas "
        "(or statistics) of those regressors marked as 'baseline' "
        "in the matrix file.",
        argstr="-Rbuck %s",
    )
    var_file = File(
        desc="output dataset for REML variance parameters", argstr="-Rvar %s"
    )
    rbeta_file = File(
        desc="output dataset for beta weights from the REML estimation, "
        "similar to the 'cbucket' output from Deconvolve. This dataset "
        "will contain all the beta weights, for baseline and stimulus "
        "regressors alike, unless the '-nobout' option is given -- "
        "in that case, this dataset will only get the betas for the "
        "stimulus regressors.",
        argstr="-Rbeta %s",
    )
    glt_file = File(
        desc="output dataset for beta + statistics from the REML estimation, "
        "but ONLY for the GLTs added on the REMLfit command line itself "
        "via 'gltsym'; GLTs from Deconvolve's command line will NOT "
        "be included.",
        argstr="-Rglt %s",
    )
    fitts_file = File(desc="output dataset for REML fitted model", argstr="-Rfitts %s")
    errts_file = File(
        desc="output dataset for REML residuals = data - fitted model",
        argstr="-Rerrts %s",
    )
    wherr_file = File(
        desc="dataset for REML residual, whitened using the estimated "
        "ARMA(1,1) correlation matrix of the noise",
        argstr="-Rwherr %s",
    )
    quiet = traits.Bool(desc="turn off most progress messages", argstr="-quiet")
    verb = traits.Bool(
        desc="turns on more progress messages, including memory usage "
        "progress reports at various stages",
        argstr="-verb",
    )
    goforit = traits.Bool(
        desc="With potential issues flagged in the design matrix, an attempt "
        "will nevertheless be made to fit the model",
        argstr="-GOFORIT",
    )
    ovar = File(
        desc="dataset for OLSQ st.dev. parameter (kind of boring)", argstr="-Ovar %s"
    )
    obeta = File(
        desc="dataset for beta weights from the OLSQ estimation", argstr="-Obeta %s"
    )
    obuck = File(
        desc="dataset for beta + statistics from the OLSQ estimation",
        argstr="-Obuck %s",
    )
    oglt = File(
        desc="dataset for beta + statistics from 'gltsym' options", argstr="-Oglt %s"
    )
    ofitts = File(desc="dataset for OLSQ fitted model", argstr="-Ofitts %s")
    oerrts = File(
        desc="dataset for OLSQ residuals (data - fitted model)", argstr="-Oerrts %s"
    )


class RemlfitOutputSpec(AFNICommandOutputSpec):
    out_file = File(
        desc="dataset for beta + statistics from the REML estimation (if generated)"
    )
    var_file = File(desc="dataset for REML variance parameters (if generated)")
    rbeta_file = File(
        desc="dataset for beta weights from the REML estimation (if generated)"
    )
    rbeta_file = File(
        desc="output dataset for beta weights from the REML estimation (if generated)"
    )
    glt_file = File(
        desc="output dataset for beta + statistics from the REML estimation, "
        "but ONLY for the GLTs added on the REMLfit command "
        "line itself via 'gltsym' (if generated)"
    )
    fitts_file = File(desc="output dataset for REML fitted model (if generated)")
    errts_file = File(
        desc="output dataset for REML residuals = data - fitted model (if generated)"
    )
    wherr_file = File(
        desc="dataset for REML residual, whitened using the estimated "
        "ARMA(1,1) correlation matrix of the noise (if generated)"
    )
    ovar = File(desc="dataset for OLSQ st.dev. parameter (if generated)")
    obeta = File(
        desc="dataset for beta weights from the OLSQ estimation (if generated)"
    )
    obuck = File(
        desc="dataset for beta + statistics from the OLSQ estimation (if generated)"
    )
    oglt = File(
        desc="dataset for beta + statistics from 'gltsym' options (if generated)"
    )
    ofitts = File(desc="dataset for OLSQ fitted model (if generated)")
    oerrts = File(
        desc="dataset for OLSQ residuals = data - fitted model (if generated)"
    )


class Remlfit(AFNICommand):
    """Performs Generalized least squares time series fit with Restricted
    Maximum Likelihood (REML) estimation of the temporal auto-correlation
    structure.

    For complete details, see the `3dREMLfit Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dREMLfit.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> remlfit = afni.Remlfit()
    >>> remlfit.inputs.in_files = ['functional.nii', 'functional2.nii']
    >>> remlfit.inputs.out_file = 'output.nii'
    >>> remlfit.inputs.matrix = 'output.1D'
    >>> remlfit.inputs.gltsym = [('SYM: +Lab1 -Lab2', 'TestSYM'), ('timeseries.txt', 'TestFile')]
    >>> remlfit.cmdline
    '3dREMLfit -gltsym "SYM: +Lab1 -Lab2" TestSYM -gltsym "timeseries.txt" TestFile -input "functional.nii functional2.nii" -matrix output.1D -Rbuck output.nii'
    >>> res = remlfit.run()  # doctest: +SKIP
    """

    _cmd = "3dREMLfit"
    input_spec = RemlfitInputSpec
    output_spec = RemlfitOutputSpec

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []
        return super()._parse_inputs(skip)

    def _list_outputs(self):
        outputs = self.output_spec().get()

        for key in outputs:
            if isdefined(self.inputs.get()[key]):
                outputs[key] = os.path.abspath(self.inputs.get()[key])

        return outputs


class SynthesizeInputSpec(AFNICommandInputSpec):
    cbucket = File(
        desc="Read the dataset output from 3dDeconvolve via the '-cbucket' option.",
        argstr="-cbucket %s",
        copyfile=False,
        mandatory=True,
    )
    matrix = File(
        desc="Read the matrix output from 3dDeconvolve via the '-x1D' option.",
        argstr="-matrix %s",
        copyfile=False,
        mandatory=True,
    )
    select = traits.List(
        Str(desc="selected columns to synthesize"),
        argstr="-select %s",
        desc="A list of selected columns from the matrix (and the "
        "corresponding coefficient sub-bricks from the "
        "cbucket). Valid types include 'baseline', "
        " 'polort', 'allfunc', 'allstim', 'all', "
        "Can also provide 'something' where something matches "
        "a stim_label from 3dDeconvolve, and 'digits' where digits "
        "are the numbers of the select matrix columns by "
        "numbers (starting at 0), or number ranges of the form "
        "'3..7' and '3-7'.",
        mandatory=True,
    )
    out_file = File(
        name_template="syn",
        desc="output dataset prefix name (default 'syn')",
        argstr="-prefix %s",
    )
    dry_run = traits.Bool(
        desc="Don't compute the output, just check the inputs.", argstr="-dry"
    )
    TR = traits.Float(
        desc="TR to set in the output.  The default value of "
        "TR is read from the header of the matrix file.",
        argstr="-TR %f",
    )
    cenfill = traits.Enum(
        "zero",
        "nbhr",
        "none",
        argstr="-cenfill %s",
        desc="Determines how censored time points from the "
        "3dDeconvolve run will be filled. Valid types "
        "are 'zero', 'nbhr' and 'none'.",
    )


class Synthesize(AFNICommand):
    """Reads a '-cbucket' dataset and a '.xmat.1D' matrix from 3dDeconvolve,
       and synthesizes a fit dataset using user-selected sub-bricks and
       matrix columns.

    For complete details, see the `3dSynthesize Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dSynthesize.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> synthesize = afni.Synthesize()
    >>> synthesize.inputs.cbucket = 'functional.nii'
    >>> synthesize.inputs.matrix = 'output.1D'
    >>> synthesize.inputs.select = ['baseline']
    >>> synthesize.cmdline
    '3dSynthesize -cbucket functional.nii -matrix output.1D -select baseline'
    >>> syn = synthesize.run()  # doctest: +SKIP
    """

    _cmd = "3dSynthesize"
    input_spec = SynthesizeInputSpec
    output_spec = AFNICommandOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()

        for key in outputs:
            if isdefined(self.inputs.get()[key]):
                outputs[key] = os.path.abspath(self.inputs.get()[key])

        return outputs
