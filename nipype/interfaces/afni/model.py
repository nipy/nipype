# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft = python sts = 4 ts = 4 sw = 4 et:
"""AFNI modeling interfaces

Examples
--------
See the docstrings of the individual classes for examples.
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import os

from ..base import (CommandLineInputSpec, CommandLine, Directory, TraitedSpec,
                    traits, isdefined, File, InputMultiObject, Undefined, Str)
from ...external.due import BibTeX

from .base import (AFNICommandBase, AFNICommand, AFNICommandInputSpec,
                   AFNICommandOutputSpec)


class DeconvolveInputSpec(AFNICommandInputSpec):
    in_files = InputMultiObject(
        File(exists=True),
        desc='filenames of 3D+time input datasets. More than one filename can '
        'be given and the datasets will be auto-catenated in time. '
        'You can input a 1D time series file here, but the time axis '
        'should run along the ROW direction, not the COLUMN direction as '
        'in the \'input1D\' option.',
        argstr='-input %s',
        copyfile=False,
        sep=" ",
        position=1)
    sat = traits.Bool(
        desc='check the dataset time series for initial saturation transients,'
        ' which should normally have been excised before data analysis.',
        argstr='-sat',
        xor=['trans'])
    trans = traits.Bool(
        desc='check the dataset time series for initial saturation transients,'
        ' which should normally have been excised before data analysis.',
        argstr='-trans',
        xor=['sat'])
    noblock = traits.Bool(
        desc='normally, if you input multiple datasets with \'input\', then '
        'the separate datasets are taken to be separate image runs that '
        'get separate baseline models. Use this options if you want to '
        'have the program consider these to be all one big run.'
        '* If any of the input dataset has only 1 sub-brick, then this '
        'option is automatically invoked!'
        '* If the auto-catenation feature isn\'t used, then this option '
        'has no effect, no how, no way.',
        argstr='-noblock')
    force_TR = traits.Float(
        desc='use this value instead of the TR in the \'input\' '
             'dataset. (It\'s better to fix the input using Refit.)',
        argstr='-force_TR %f',
        position=0)
    input1D = File(
        desc='filename of single (fMRI) .1D time series where time runs down '
        'the column.',
        argstr='-input1D %s',
        exists=True)
    TR_1D = traits.Float(
        desc='TR to use with \'input1D\'. This option has no effect if you do '
        'not also use \'input1D\'.',
        argstr='-TR_1D %f')
    legendre = traits.Bool(
        desc='use Legendre polynomials for null hypothesis (baseline model)',
        argstr='-legendre')
    nolegendre = traits.Bool(
        desc='use power polynomials for null hypotheses. Don\'t do this '
        'unless you are crazy!',
        argstr='-nolegendre')
    nodmbase = traits.Bool(
        desc='don\'t de-mean baseline time series', argstr='-nodmbase')
    dmbase = traits.Bool(
        desc='de-mean baseline time series (default if \'polort\' >= 0)',
        argstr='-dmbase')
    svd = traits.Bool(
        desc='use SVD instead of Gaussian elimination (default)',
        argstr='-svd')
    nosvd = traits.Bool(
        desc='use Gaussian elimination instead of SVD', argstr='-nosvd')
    rmsmin = traits.Float(
        desc='minimum rms error to reject reduced model (default = 0; don\'t '
        'use this option normally!)',
        argstr='-rmsmin %f')
    nocond = traits.Bool(
        desc='DON\'T calculate matrix condition number', argstr='-nocond')
    singvals = traits.Bool(
        desc='print out the matrix singular values', argstr='-singvals')
    goforit = traits.Int(
        desc='use this to proceed even if the matrix has bad problems (e.g., '
        'duplicate columns, large condition number, etc.).',
        argstr='-GOFORIT %i')
    allzero_OK = traits.Bool(
        desc='don\'t consider all zero matrix columns to be the type of error '
        'that \'gotforit\' is needed to ignore.',
        argstr='-allzero_OK')
    dname = traits.Tuple(
        Str,
        Str,
        desc='set environmental variable to provided value',
        argstr='-D%s=%s')
    mask = File(
        desc='filename of 3D mask dataset; only data time series from within '
        'the mask will be analyzed; results for voxels outside the mask '
        'will be set to zero.',
        argstr='-mask %s',
        exists=True)
    automask = traits.Bool(
        desc='build a mask automatically from input data (will be slow for '
        'long time series datasets)',
        argstr='-automask')
    STATmask = File(
        desc='build a mask from provided file, and use this mask for the '
        'purpose of reporting truncation-to float issues AND for '
        'computing the FDR curves. The actual results ARE not masked '
        'with this option (only with \'mask\' or \'automask\' options).',
        argstr='-STATmask %s',
        exists=True)
    censor = File(
        desc='filename of censor .1D time series. This is a file of 1s and '
        '0s, indicating which time points are to be included (1) and '
        'which are to be excluded (0).',
        argstr='-censor %s',
        exists=True)
    polort = traits.Int(
        desc='degree of polynomial corresponding to the null hypothesis '
        '[default: 1]',
        argstr='-polort %d')
    ortvec = traits.Tuple(
        File(desc='filename', exists=True),
        Str(desc='label'),
        desc='this option lets you input a rectangular array of 1 or more '
        'baseline vectors from a file. This method is a fast way to '
        'include a lot of baseline regressors in one step. ',
        argstr='-ortvec %s %s')
    x1D = File(desc='specify name for saved X matrix', argstr='-x1D %s')
    x1D_stop = traits.Bool(
        desc='stop running after writing .xmat.1D file', argstr='-x1D_stop')
    cbucket = traits.Str(
        desc='Name for dataset in which to save the regression '
        'coefficients (no statistics). This dataset '
        'will be used in a -xrestore run [not yet implemented] '
        'instead of the bucket dataset, if possible.',
        argstr='-cbucket %s')
    out_file = File(desc='output statistics file', argstr='-bucket %s')
    num_threads = traits.Int(
        desc='run the program with provided number of sub-processes',
        argstr='-jobs %d',
        nohash=True)
    fout = traits.Bool(
        desc='output F-statistic for each stimulus', argstr='-fout')
    rout = traits.Bool(
        desc='output the R^2 statistic for each stimulus', argstr='-rout')
    tout = traits.Bool(
        desc='output the T-statistic for each stimulus', argstr='-tout')
    vout = traits.Bool(
        desc='output the sample variance (MSE) for each stimulus',
        argstr='-vout')
    nofdr = traits.Bool(
        desc="Don't compute the statistic-vs-FDR curves for the bucket "
             "dataset.",
        argstr='-noFDR')
    global_times = traits.Bool(
        desc='use global timing for stimulus timing files',
        argstr='-global_times',
        xor=['local_times'])
    local_times = traits.Bool(
        desc='use local timing for stimulus timing files',
        argstr='-local_times',
        xor=['global_times'])
    num_stimts = traits.Int(
        desc='number of stimulus timing files',
        argstr='-num_stimts %d',
        position=-6)
    stim_times = traits.List(
        traits.Tuple(
            traits.Int(desc='k-th response model'),
            File(desc='stimulus timing file', exists=True),
            Str(desc='model')),
        desc='generate a response model from a set of stimulus times'
        ' given in file.',
        argstr='-stim_times %d %s \'%s\'...',
        position=-5)
    stim_label = traits.List(
        traits.Tuple(
            traits.Int(desc='k-th input stimulus'),
            Str(desc='stimulus label')),
        desc='label for kth input stimulus (e.g., Label1)',
        argstr='-stim_label %d %s...',
        requires=['stim_times'],
        position=-4)
    stim_times_subtract = traits.Float(
        desc='this option means to subtract specified seconds from each time '
        'encountered in any \'stim_times\' option. The purpose of this '
        'option is to make it simple to adjust timing files for the '
        'removal of images from the start of each imaging run.',
        argstr='-stim_times_subtract %f')
    num_glt = traits.Int(
        desc='number of general linear tests (i.e., contrasts)',
        argstr='-num_glt %d',
        position=-3)
    gltsym = traits.List(
        Str(desc='symbolic general linear test'),
        desc='general linear tests (i.e., contrasts) using symbolic '
        'conventions (e.g., \'+Label1 -Label2\')',
        argstr='-gltsym \'SYM: %s\'...',
        position=-2)
    glt_label = traits.List(
        traits.Tuple(
            traits.Int(desc='k-th general linear test'),
            Str(desc='GLT label')),
        desc='general linear test (i.e., contrast) labels',
        argstr='-glt_label %d %s...',
        requires=['gltsym'],
        position=-1)


class DeconvolveOutputSpec(TraitedSpec):
    out_file = File(desc='output statistics file', exists=True)
    reml_script = File(
        desc='automatical generated script to run 3dREMLfit', exists=True)
    x1D = File(desc='save out X matrix', exists=True)
    cbucket = File(desc='output regression coefficients file (if generated)')


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

    _cmd = '3dDeconvolve'
    input_spec = DeconvolveInputSpec
    output_spec = DeconvolveOutputSpec

    def _format_arg(self, name, trait_spec, value):
        if name == 'gltsym':
            for n, val in enumerate(value):
                if val.startswith('SYM: '):
                    value[n] = val.lstrip('SYM: ')

        return super(Deconvolve, self)._format_arg(name, trait_spec, value)

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []
        if len(self.inputs.stim_times) and not isdefined(
                self.inputs.num_stimts):
            self.inputs.num_stimts = len(self.inputs.stim_times)
        if len(self.inputs.gltsym) and not isdefined(self.inputs.num_glt):
            self.inputs.num_glt = len(self.inputs.gltsym)
        if not isdefined(self.inputs.out_file):
            self.inputs.out_file = 'Decon.nii'

        return super(Deconvolve, self)._parse_inputs(skip)

    def _list_outputs(self):
        outputs = self.output_spec().get()

        _gen_fname_opts = {}
        _gen_fname_opts['basename'] = self.inputs.out_file
        _gen_fname_opts['cwd'] = os.getcwd()

        if isdefined(self.inputs.x1D):
            if not self.inputs.x1D.endswith('.xmat.1D'):
                outputs['x1D'] = os.path.abspath(self.inputs.x1D + '.xmat.1D')
            else:
                outputs['x1D'] = os.path.abspath(self.inputs.x1D)
        else:
            outputs['x1D'] = self._gen_fname(
                suffix='.xmat.1D', **_gen_fname_opts)

        if isdefined(self.inputs.cbucket):
            outputs['cbucket'] = os.path.abspath(self.inputs.cbucket)

        outputs['reml_script'] = self._gen_fname(
            suffix='.REML_cmd', **_gen_fname_opts)
        # remove out_file from outputs if x1d_stop set to True
        if self.inputs.x1D_stop:
            del outputs['out_file'], outputs['cbucket']
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)

        return outputs


class RemlfitInputSpec(AFNICommandInputSpec):
    # mandatory files
    in_files = InputMultiObject(
        File(exists=True),
        desc='Read time series dataset',
        argstr='-input "%s"',
        mandatory=True,
        copyfile=False,
        sep=" ")
    matrix = File(
        desc='the design matrix file, which should have been output from '
        'Deconvolve via the \'x1D\' option',
        argstr='-matrix %s',
        mandatory=True)
    # "Semi-Hidden Alternative Ways to Define the Matrix"
    polort = traits.Int(
        desc='if no \'matrix\' option is given, AND no \'matim\' option, '
        'create a matrix with Legendre polynomial regressors'
        'up to the specified order. The default value is 0, which'
        'produces a matrix with a single column of all ones',
        argstr='-polort %d',
        xor=['matrix'])
    matim = traits.File(
        desc='read a standard file as the matrix. You can use only Col as '
        'a name in GLTs with these nonstandard matrix input methods, '
        'since the other names come from the \'matrix\' file. '
        'These mutually exclusive options are ignored if \'matrix\' '
        'is used.',
        argstr='-matim %s',
        xor=['matrix'])
    # Other arguments
    mask = File(
        desc='filename of 3D mask dataset; only data time series from within '
        'the mask will be analyzed; results for voxels outside the mask '
        'will be set to zero.',
        argstr='-mask %s',
        exists=True)
    automask = traits.Bool(
        usedefault=True,
        argstr='-automask',
        desc='build a mask automatically from input data (will be slow for '
        'long time series datasets)')
    STATmask = File(
        desc='filename of 3D mask dataset to be used for the purpose '
        'of reporting truncation-to float issues AND for computing the '
        'FDR curves. The actual results ARE not masked with this option '
        '(only with \'mask\' or \'automask\' options).',
        argstr='-STATmask %s',
        exists=True)
    addbase = InputMultiObject(
        File(
            exists=True,
            desc='file containing columns to add to regression matrix'),
        desc='file(s) to add baseline model columns to the matrix with this '
        'option. Each column in the specified file(s) will be appended '
        'to the matrix. File(s) must have at least as many rows as the '
        'matrix does.',
        copyfile=False,
        sep=" ",
        argstr='-addbase %s')
    slibase = InputMultiObject(
        File(
            exists=True,
            desc='file containing columns to add to regression matrix'),
        desc='similar to \'addbase\' in concept, BUT each specified file '
        'must have an integer multiple of the number of slices '
        'in the input dataset(s); then, separate regression '
        'matrices are generated for each slice, with the '
        'first column of the file appended to the matrix for '
        'the first slice of the dataset, the second column of the file '
        'appended to the matrix for the first slice of the dataset, '
        'and so on. Intended to help model physiological noise in FMRI, '
        'or other effects you want to regress out that might '
        'change significantly in the inter-slice time intervals. This '
        'will slow the program down, and make it use a lot more memory '
        '(to hold all the matrix stuff).',
        argstr='-slibase %s')
    slibase_sm = InputMultiObject(
        File(
            exists=True,
            desc='file containing columns to add to regression matrix'),
        desc='similar to \'slibase\', BUT each file much be in slice major '
        'order (i.e. all slice0 columns come first, then all slice1 '
        'columns, etc).',
        argstr='-slibase_sm %s')
    usetemp = traits.Bool(
        desc='write intermediate stuff to disk, to economize on RAM. '
        'Using this option might be necessary to run with '
        '\'slibase\' and with \'Grid\' values above the default, '
        'since the program has to store a large number of '
        'matrices for such a problem: two for every slice and '
        'for every (a,b) pair in the ARMA parameter grid. Temporary '
        'files are written to the directory given in environment '
        'variable TMPDIR, or in /tmp, or in ./ (preference is in that '
        'order)',
        argstr='-usetemp')
    nodmbase = traits.Bool(
        desc='by default, baseline columns added to the matrix via '
        '\'addbase\' or \'slibase\' or \'dsort\' will each have their '
        'mean removed (as is done in Deconvolve); this option turns this '
        'centering off',
        argstr='-nodmbase',
        requires=['addbase', 'dsort'])
    dsort = File(
        desc='4D dataset to be used as voxelwise baseline regressor',
        exists=True,
        copyfile=False,
        argstr='-dsort %s')
    dsort_nods = traits.Bool(
        desc='if \'dsort\' option is used, this command will output '
        'additional results files excluding the \'dsort\' file',
        argstr='-dsort_nods',
        requires=['dsort'])
    fout = traits.Bool(
        desc='output F-statistic for each stimulus', argstr='-fout')
    rout = traits.Bool(
        desc='output the R^2 statistic for each stimulus', argstr='-rout')
    tout = traits.Bool(
        desc='output the T-statistic for each stimulus; if you use '
        '\'out_file\' and do not give any of \'fout\', \'tout\','
        'or \'rout\', then the program assumes \'fout\' is activated.',
        argstr='-tout')
    nofdr = traits.Bool(
        desc='do NOT add FDR curve data to bucket datasets; FDR curves can '
        'take a long time if \'tout\' is used',
        argstr='-noFDR')
    nobout = traits.Bool(
        desc='do NOT add baseline (null hypothesis) regressor betas '
        'to the \'rbeta_file\' and/or \'obeta_file\' output datasets.',
        argstr='-nobout')
    gltsym = traits.List(
        traits.Either(
            traits.Tuple(File(exists=True), Str()), traits.Tuple(Str(),
                                                                 Str())),
        desc='read a symbolic GLT from input file and associate it with a '
        'label. As in Deconvolve, you can also use the \'SYM:\' method '
        'to provide the definition of the GLT directly as a string '
        '(e.g., with \'SYM: +Label1 -Label2\'). Unlike Deconvolve, you '
        'MUST specify \'SYM: \' if providing the GLT directly as a '
        'string instead of from a file',
        argstr='-gltsym "%s" %s...')
    out_file = File(
        desc='output dataset for beta + statistics from the REML estimation; '
        'also contains the results of any GLT analysis requested '
        'in the Deconvolve setup, similar to the \'bucket\' output '
        'from Deconvolve. This dataset does NOT get the betas '
        '(or statistics) of those regressors marked as \'baseline\' '
        'in the matrix file.',
        argstr='-Rbuck %s')
    var_file = File(
        desc='output dataset for REML variance parameters', argstr='-Rvar %s')
    rbeta_file = File(
        desc='output dataset for beta weights from the REML estimation, '
        'similar to the \'cbucket\' output from Deconvolve. This dataset '
        'will contain all the beta weights, for baseline and stimulus '
        'regressors alike, unless the \'-nobout\' option is given -- '
        'in that case, this dataset will only get the betas for the '
        'stimulus regressors.',
        argstr='-Rbeta %s')
    glt_file = File(
        desc='output dataset for beta + statistics from the REML estimation, '
        'but ONLY for the GLTs added on the REMLfit command line itself '
        'via \'gltsym\'; GLTs from Deconvolve\'s command line will NOT '
        'be included.',
        argstr='-Rglt %s')
    fitts_file = File(
        desc='ouput dataset for REML fitted model', argstr='-Rfitts %s')
    errts_file = File(
        desc='output dataset for REML residuals = data - fitted model',
        argstr='-Rerrts %s')
    wherr_file = File(
        desc='dataset for REML residual, whitened using the estimated '
        'ARMA(1,1) correlation matrix of the noise',
        argstr='-Rwherr %s')
    quiet = traits.Bool(
        desc='turn off most progress messages', argstr='-quiet')
    verb = traits.Bool(
        desc='turns on more progress messages, including memory usage '
        'progress reports at various stages',
        argstr='-verb')
    ovar = File(
        desc='dataset for OLSQ st.dev. parameter (kind of boring)',
        argstr='-Ovar %s')
    obeta = File(
        desc='dataset for beta weights from the OLSQ estimation',
        argstr='-Obeta %s')
    obuck = File(
        desc='dataset for beta + statistics from the OLSQ estimation',
        argstr='-Obuck %s')
    oglt = File(
        desc='dataset for beta + statistics from \'gltsym\' options',
        argstr='-Oglt %s')
    ofitts = File(desc='dataset for OLSQ fitted model', argstr='-Ofitts %s')
    oerrts = File(
        desc='dataset for OLSQ residuals (data - fitted model)',
        argstr='-Oerrts %s')


class RemlfitOutputSpec(AFNICommandOutputSpec):
    out_file = File(
        desc='dataset for beta + statistics from the REML estimation (if '
        'generated')
    var_file = File(desc='dataset for REML variance parameters (if generated)')
    rbeta_file = File(
        desc='dataset for beta weights from the REML estimation (if '
        'generated)')
    rbeta_file = File(
        desc='output dataset for beta weights from the REML estimation (if '
        'generated')
    glt_file = File(
        desc='output dataset for beta + statistics from the REML estimation, '
        'but ONLY for the GLTs added on the REMLfit command '
        'line itself via \'gltsym\' (if generated)')
    fitts_file = File(
        desc='ouput dataset for REML fitted model (if generated)')
    errts_file = File(
        desc='output dataset for REML residuals = data - fitted model (if '
        'generated')
    wherr_file = File(
        desc='dataset for REML residual, whitened using the estimated '
        'ARMA(1,1) correlation matrix of the noise (if generated)')
    ovar = File(desc='dataset for OLSQ st.dev. parameter (if generated)')
    obeta = File(desc='dataset for beta weights from the OLSQ estimation (if '
                 'generated)')
    obuck = File(
        desc='dataset for beta + statistics from the OLSQ estimation (if '
        'generated)')
    oglt = File(
        desc='dataset for beta + statistics from \'gltsym\' options (if '
        'generated')
    ofitts = File(desc='dataset for OLSQ fitted model (if generated)')
    oerrts = File(desc='dataset for OLSQ residuals = data - fitted model (if '
                  'generated')


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

    _cmd = '3dREMLfit'
    input_spec = RemlfitInputSpec
    output_spec = RemlfitOutputSpec

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []
        return super(Remlfit, self)._parse_inputs(skip)

    def _list_outputs(self):
        outputs = self.output_spec().get()

        for key in outputs.keys():
            if isdefined(self.inputs.get()[key]):
                outputs[key] = os.path.abspath(self.inputs.get()[key])

        return outputs


class SynthesizeInputSpec(AFNICommandInputSpec):
    cbucket = File(
        desc='Read the dataset output from '
        '3dDeconvolve via the \'-cbucket\' option.',
        argstr='-cbucket %s',
        copyfile=False,
        mandatory=True)
    matrix = File(
        desc='Read the matrix output from '
        '3dDeconvolve via the \'-x1D\' option.',
        argstr='-matrix %s',
        copyfile=False,
        mandatory=True)
    select = traits.List(
        Str(desc='selected columns to synthesize'),
        argstr='-select %s',
        desc='A list of selected columns from the matrix (and the '
        'corresponding coefficient sub-bricks from the '
        'cbucket). Valid types include \'baseline\', '
        ' \'polort\', \'allfunc\', \'allstim\', \'all\', '
        'Can also provide \'something\' where something matches '
        'a stim_label from 3dDeconvolve, and \'digits\' where digits '
        'are the numbers of the select matrix columns by '
        'numbers (starting at 0), or number ranges of the form '
        '\'3..7\' and \'3-7\'.',
        mandatory=True)
    out_file = File(
        name_template='syn',
        desc='output dataset prefix name (default \'syn\')',
        argstr='-prefix %s')
    dry_run = traits.Bool(
        desc='Don\'t compute the output, just '
        'check the inputs.',
        argstr='-dry')
    TR = traits.Float(
        desc='TR to set in the output.  The default value of '
        'TR is read from the header of the matrix file.',
        argstr='-TR %f')
    cenfill = traits.Enum(
        'zero',
        'nbhr',
        'none',
        argstr='-cenfill %s',
        desc='Determines how censored time points from the '
        '3dDeconvolve run will be filled. Valid types '
        'are \'zero\', \'nbhr\' and \'none\'.')


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

    _cmd = '3dSynthesize'
    input_spec = SynthesizeInputSpec
    output_spec = AFNICommandOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()

        for key in outputs.keys():
            if isdefined(self.inputs.get()[key]):
                outputs[key] = os.path.abspath(self.inputs.get()[key])

        return outputs


class MemaInputSpec(AFNICommandInputSpec):
    # mandatory inputs
    _subject_trait = traits.Either(
        traits.Tuple(
            Str(minlen=1), File(exists=True), File(exists=True)
        ),
        traits.Tuple(
            Str(minlen=1), File(exists=True), File(exists=True), Str(''), Str('')
        )
    )

    sets = traits.List(
        traits.Tuple(Str(minlen=1), traits.List(_subject_trait, minlen=1)),
        desc="""\
Specify the data for one of two test variables (either group, contrast/GLTs) A & B.

SETNAME is the name assigned to the set, which is only for the
      user's information, and not used by the program. When
      there are two groups, the 1st and 2nd datasets are
      associated with the 1st and 2nd labels specified
      through option -set, and the group difference is
      the second group minus the first one, similar to
      3dttest but different from 3dttest++.
SUBJ_K is the label for the subject K whose datasets will be
     listed next
BETA_DSET is the name of the dataset of the beta coefficient or GLT.
T_DSET is the name of the dataset containing the Tstat
     corresponding to BETA_DSET.
 To specify BETA_DSET, and T_DSET, you can use the standard AFNI
 notation, which, in addition to sub-brick indices, now allows for
 the use of sub-brick labels as selectors
e.g: -set Placebo Jane pb05.Jane.Regression+tlrc'[face#0_Beta]'
                       pb05.Jane.Regression+tlrc'[face#0_Tstat]'
""",
        argstr='-set %s...',
        mandatory=True,
        minlen=1,
        maxlen=2,
    )

    # conditionally mandatory arguments
    groups = traits.List(
        ['G1'],
        Str(minlen=1),
        desc='Name of 1 or 2 groups. This option must be used when comparing two groups.',
        argstr='-groups %s',
        minlen=1,
        maxlen=2,
    )

    """"
   -groups GROUP1 [GROUP2]: Name of 1 or 2 groups. This option must be used
                          when comparing two groups. Default is one group
                          named 'G1'. The labels here are used to name
                          the sub-bricks in the output. When there are
                          two groups, the 1st and 2nd labels here are
                          associated with the 1st and 2nd datasets
                          specified respectively through option -set,
                          and their group difference is the second group
                          minus the first one, similar to 3dttest but
                          different from 3dttest++.
    """

    equal_variance = traits.Bool(
        True,
        usedefault=True,
        argstr=['-unequal_variance', '-equal_variance'],
        xor=['covariates'],
        desc="""\
[-equal_variance] Assume same cross-subjects variability between GROUP1 and GROUP2
(homoskedasticity) (Default); or [-unequal_variance] Model cross-subjects variability
difference between GROUP1 and GROUP2 (heteroskedasticity).
This option may NOT be invoked when covariate is present in the
model.""",
    )

    # Other arguments
    cio = traits.Bool(
        desc='use AFNIs C io functions',
        argstr='-cio')

    contrast_name = traits.Str(
        desc='no help available',
        argstr='-contrast_name %s')

    covariates = File(
        File(exists=True),
        desc='Specify the name of a text file containing a table for the covariate(s).'
        ' Each column in the file is treated as a separate covariate, and each row contains'
        ' the values of these covariates for each subject. It is recommended to use the'
        ' covariates file generated by 3dREMLfit.',
        argstr='-covariates %s',
    )

    covariates_center = traits.Str(
        desc="""\
Centering rule for covariates. You can provide centering rules for each coveriate,
or specify mean centering or no centering (using 0). If no specification is made each
covariate will be centered about its own mean.
-covariates_center COV_1=CEN_1 [COV_2=CEN_2 ... ]: (for 1 group)
-covariates_center COV_1=CEN_1.A CEN_1.B [COV_2=CEN_2.A CEN_2.B ... ]:
                                                 (for 2 groups)
 where COV_K is the name assigned to the K-th covariate,
 either from the header of the covariates file, or from the option
 -covariates_name. This makes clear which center belongs to which
 covariate. When two groups are used, you need to specify a center for
 each of the groups (CEN_K.A, CEN_K.B).
 Example: If you had covariates age, and weight, you would use:
        -covariates_center age = 78 55 weight = 165 198""",
        argstr='covariates_center %s'
    )

    covariates_model = traits.Tuple(
        traits.Enum('same', 'different', desc='Specify the center'),
        traits.Enum('same', 'different', desc='Specify the slope'),
        desc='Specify whether to use the same or different intercepts for each of the covariates.'
             ' Similarly for the slope.',
        argstr='-covariates_model center=%s slope=%s'
    )

    covariates_name = traits.List(
        Str(minlen=1),
        desc='Specify the name of each of the N covariates. Only needed if covariate file does'
        ' not have a header. Default is to name covariates cov1, cov2, ...',
        argstr='-covariates_names %s')

    debugArgs = traits.Bool(
        desc='Enable R to save parameters in a file called .3dMEMA.dbg.AFNI.args in the current'
        ' directory for debugging.',
        argstr='-dbArgs'
    )

    hk_test = traits.Bool(
        desc="""\
Perform Hartung-Knapp adjustment for the output t-statistic. \
This approach is more robust when the number of subjects \
is small, and is generally preferred. -KHtest is the default \
with t-statistic output.""",
        argstr=['-no_HKtest', '-HKtest'],
    )

    num_threads = traits.Int(
        desc='run the program with provided number of sub-processes',
        argstr='-jobs %d',
        nohash=True
    )

    mask = File(
        exists=True,
        desc='Process voxels from inside this mask only. Default is no masking',
        argstr='-mask %s'
    )

    max_zeros = traits.Range(  # Please revise all the other possible settings\
        desc="""\
Do not compute statistics at any voxel that has \
more than MM zero beta coefficients or GLTs. Voxels around \
the edges of the group brain will not have data from \
some of the subjects. Therefore, some of their beta's or \
GLTs and t-stats are masked with 0. 3dMEMA can handle \
missing data at those voxels but obviously too much \
missing data is not good. Setting -max_zeros to 0.25 \
means process data only at voxels where no more than 1/4 \
of the data is missing. The default value is 0 (no \
missing values allowed). MM can be a positive integer \
less than the number of subjects, or a fraction \
between 0 and 1. Alternatively option -missing_data \
can be used to handle missing data.""",
        low=0.0, high=1.0,
        argstr='-max_zeros %f',
        xor=['missing_data'],
    )

    missing_data = traits.Either(
        0,
        traits.List(File(exists=True), minlen=1, maxlen=2,),
        desc="""\
This option corrects for inflated statistics for the voxels where
some subjects do not have any data available due to imperfect
spatial alignment or other reasons. The absence of this option
means no missing data will be assumed.""",
        argstr='-missing_data %s',
        xor=['max_zeros']
    )

    # -missing_data: This option corrects for inflated statistics for the voxels where
    #             some subjects do not have any data available due to imperfect
    #             spatial alignment or other reasons. The absence of this option
    #             means no missing data will be assumed. Two formats of option
    #             setting exist as shown below.
    # -missing_data 0: With this format the zero value at a voxel of each subject
    #               will be interpreted as missing data.
    # -missing_data File1 [File2]: Information about missing data is specified
    #                             with file of 1 or 2 groups (the number 1 or 2
    #                             and file order should be consistent with those
    #                             in option -groups). The voxel value of each file
    #                             indicates the number of sujects with missing data
    #                             in that group.

    outliers = traits.Bool(
        False,
        usedefault=True,
        desc='Model outlier betas with a Laplace distribution of '
             'subject-specific error. Default is -no_model_outliers',
        argstr=['-no_model_outliers', '-model_outliers'],
    )

    nonzeros = traits.Float(
        desc="""\
Do not compute statistics at any voxel that has \
less than NN non-zero beta values. This options is \
complimentary to -max_zeros, and matches an option in \
the interactive 3dMEMA mode. NN is basically (number of \
unique subjects - MM). Alternatively option -missing_data \
can be used to handle missing data.""",
        argstr='-n_nonzero %f',
        xor=['missing_data']
    )

    residualZ = traits.Bool(
        False,
        usedefault=True,
        desc='Output residuals and their Z values used in identifying '
             'outliers at voxel level. Default is -no_residual_Z',
        argstr=['-no_residual_Z', '-residual_Z']
    )

    # -prefix PREFIX: Output prefix (just prefix, no view+suffix needed)
    out_file = File(
        desc='output dataset prefix name',
        argstr='-prefix %s')

    rio = traits.Bool(
        desc='use R\'s io functions',
        argstr='-rio')

    verbosity = traits.Range(
        value=1,
        usedefault=True,
        low=0,
        desc='An integer specifying verbosity level. 0 is quiet, 1+ is talkative.',
        argstr='-verb %d'
    )


class MemaOutputSpec(AFNICommandOutputSpec):
    out_file = File(
        desc='...',
        exists=True
    )

    args = File(
        desc='Arguments file for debugging, generated if -dbArgs is set')


class Mema(AFNICommand):
    """Description of 3dMEMA

    For complete details, see the `3dMEMA Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dMEMA.html>`__

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> mema = afni.Mema()
    >>> mema.inputs.sets = [('Placebo', [
    ...     ('Jane', 'pb05.Jane.betas.nii', 'pb05.Jane.tvals.nii'),
    ...     ('John', 'pb05.John.betas.nii', 'pb05.John.tvals.nii'),
    ...     ('Lisa', 'pb05.Lisa.betas.nii', 'pb05.Lisa.tvals.nii')])]
    >>> mema.cmdline
    "3dMEMA -equal_variance -no_model_outliers -no_residual_Z -set Placebo Jane \
pb05.betas.nii pb05.Jane.tvals.nii John pb05.John.betas.nii pb05.John.tvals.nii \
Lisa pb05.Lisa.betas.nii pb05.Lisa.tvals.nii -verb 1"

    >>> mema.inputs.sets = [('Placebo', [
    ...     ('Jane', 'pb05.Jane.Regression+tlrc', 'pb05.Jane.Regression+tlrc',
    ...      '[face#0_Beta]', '[face#0_Tstat]')
    ... ])]
    >>> mema.cmdline
    "3dMEMA -equal_variance -no_model_outliers -no_residual_Z -set Placebo Jane \
pb05.Jane.Regression+tlrc'[face#0_Beta]' pb05.Jane.Regression+tlrc'[face#0_Tstat]' -verb 1"

    >>> mema.inputs.missing_data = 0
    "3dMEMA -equal_variance -missing_data 0 -no_model_outliers -no_residual_Z -set Placebo \
Jane pb05.Jane.Regression+tlrc'[face#0_Beta]' pb05.Jane.Regression+tlrc'[face#0_Tstat]' -verb 1"

    >>> from nipype.interfaces import afni
    >>> mema = afni.Mema()
    >>> mema.inputs.groups = ['group1', 'group2']
    >>> mema.inputs.sets = ['analysis1_name', [[subject_1, s1_betas, s1_ts], [subject2, s2_bets, s2_ts], ...]]
    >>> mema.inputs.sets = ['analysis2_name', [[subject_1, s1_betas, s1_ts], [subject2, s2_bets, s2_ts], ...]]
    >>> mema.inputs.n_nonzero = 18
    >>> mema.inputs.hktest = True
    >>> mema.inputs.outliers = True
    >>> mema.inputs.equal_variance = False
    >>> mema.inputs.residual_z = True
    >>> mema.inputs.covariates = 'CovFile.txt'
    >>> mema.inputs.covariates_center = 'age = 25 13 weight = 100 150'
    >>> mema.inputs.covariates_model = ['different', 'same']
    >>> mema.inputs.out_file = 'Results.BRIK'

    """

    _cmd = '3dMEMA'
    input_spec = MemaInputSpec
    output_spec = MemaOutputSpec

    def _format_arg(self, name, trait_spec, value):
        if name == "sets":
            self._n_sets = len(value)
            formatted_values = []
            for setname, setopts in value:
                formatted_subject = []
                for this_set in setopts:
                    if len(this_set) == 5:
                        subid, beta_file, ttst_file, beta_opts, ttst_opts = this_set
                        if beta_opts:
                            beta_file = "%s'%s'" % (beta_file, beta_opts)
                        if ttst_opts:
                            ttst_file = "%s'%s'" % (ttst_file, ttst_opts)
                    else:
                        subid, beta_file, ttst_file = this_set
                    formatted_subject.append(' '.join((subid, beta_file, ttst_file)))
                formatted_values.append(' '.join([setname] + formatted_subject))
            value = formatted_values

        return super(Mema, self)._format_arg(name, trait_spec, value)

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []
        parsed = super(Mema, self)._parse_inputs(skip)

        # TODO: Check groups
        return parsed

    def _list_outputs(self):
        outputs = self.output_spec().get()

        for key in outputs.keys():
            if isdefined(self.inputs.get()[key]):
                outputs[key] = os.path.abspath(self.inputs.get()[key])

        return outputs
