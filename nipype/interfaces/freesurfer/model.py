# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The freesurfer module provides basic functions for interfacing with
   freesurfer tools.

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)

"""
__docformat__ = 'restructuredtext'

import os

from nipype.utils.filemanip import fname_presuffix, split_filename
from nipype.interfaces.freesurfer.base import FSCommand, FSTraitedSpec
from nipype.interfaces.base import (TraitedSpec, File, traits, InputMultiPath,
                                    OutputMultiPath, Directory, isdefined)


class MRISPreprocInputSpec(FSTraitedSpec):
    out_file = File(argstr='--out %s', genfile=True,
                   desc='output filename')
    target = traits.Str(argstr='--target %s', mandatory=True,
                         desc='target subject name')
    hemi = traits.Enum('lh', 'rh', argstr='--hemi %s',
                       mandatory=True,
                       desc='hemisphere for source and target')
    surf_measure = traits.Str(argstr='--meas %s',
                             xor=('surf_measure', 'surf_measure_file', 'surf_area'),
                desc='Use subject/surf/hemi.surf_measure as input')
    surf_area = traits.Str(argstr='--area %s',
                          xor=('surf_measure', 'surf_measure_file', 'surf_area'),
       desc='Extract vertex area from subject/surf/hemi.surfname to use as input.')
    subjects = traits.List(argstr='--s %s...',
                           xor=('subjects', 'fsgd_file', 'subject_file'),
                   desc='subjects from who measures are calculated')
    fsgd_file = File(exists=True, argstr='--fsgd %s',
                    xor=('subjects', 'fsgd_file', 'subject_file'),
                    desc='specify subjects using fsgd file')
    subject_file = File(exists=True, argstr='--f %s',
                    xor=('subjects', 'fsgd_file', 'subject_file'),
                    desc='file specifying subjects separated by white space')
    surf_measure_file = InputMultiPath(File(exists=True), argstr='--is %s...',
                           xor=('surf_measure', 'surf_measure_file', 'surf_area'),
          desc='file alternative to surfmeas, still requires list of subjects')
    source_format = traits.Str(argstr='--srcfmt %s', desc='source format')
    surf_dir = traits.Str(argstr='--surfdir %s',
                         desc='alternative directory (instead of surf)')
    vol_measure_file = InputMultiPath(traits.Tuple(File(exists=True),
                                      File(exists=True)),
                                      argstr='--iv %s %s...',
                                 desc='list of volume measure and reg file tuples')
    proj_frac = traits.Float(argstr='--projfrac %s',
                            desc='projection fraction for vol2surf')
    fwhm = traits.Float(argstr='--fwhm %f',
                        xor=['num_iters'],
                        desc='smooth by fwhm mm on the target surface')
    num_iters = traits.Int(argstr='--niters %d',
                        xor=['fwhm'],
                        desc='niters : smooth by niters on the target surface')
    fwhm_source = traits.Float(argstr='--fwhm-src %f',
                        xor=['num_iters_source'],
                        desc='smooth by fwhm mm on the source surface')
    num_iters_source = traits.Int(argstr='--niterssrc %d',
                        xor=['fwhm_source'],
                        desc='niters : smooth by niters on the source surface')
    smooth_cortex_only = traits.Bool(argstr='--smooth-cortex-only',
                       desc='only smooth cortex (ie, exclude medial wall)')


class MRISPreprocOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='preprocessed output file')


class MRISPreproc(FSCommand):
    """Use FreeSurfer mris_preproc to prepare a group of contrasts for
    a second level analysis

    Examples
    --------

    >>> preproc = MRISPreproc()
    >>> preproc.inputs.target = 'fsaverage'
    >>> preproc.inputs.hemi = 'lh'
    >>> preproc.inputs.vol_measure_file = [('cont1.nii', 'register.dat'), \
                                           ('cont1a.nii', 'register.dat')]
    >>> preproc.inputs.out_file = 'concatenated_file.mgz'
    >>> preproc.cmdline
    'mris_preproc --hemi lh --out concatenated_file.mgz --target fsaverage --iv cont1.nii register.dat --iv cont1a.nii register.dat'

    """

    _cmd = 'mris_preproc'
    input_spec = MRISPreprocInputSpec
    output_spec = MRISPreprocOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outfile = self.inputs.out_file
        if not isdefined(outfile):
            outputs['out_file'] = os.path.join(os.getcwd(),
                                   'concat_%s_%s.mgz' % (self.inputs.hemi,
                                                         self.inputs.target))
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None


class GLMFitInputSpec(FSTraitedSpec):
    glm_dir = traits.Str(argstr='--glmdir %s', desc='save outputs to dir',
                         genfile=True)
    in_file = File(desc='input 4D file', argstr='--y %s', mandatory=True,
                  copyfile=False)
    _design_xor = ('fsgd', 'design', 'one_sample')
    fsgd = traits.Tuple(File(exists=True), traits.Enum('doss', 'dods'),
                        argstr='--fsgd %s %s', xor=_design_xor,
                        desc='freesurfer descriptor file')
    design = File(exists=True, argstr='--X %s', xor=_design_xor,
                  desc='design matrix file')
    contrast = InputMultiPath(File(exists=True), argstr='--C %s...',
                              desc='contrast file')

    one_sample = traits.Bool(argstr='--osgm',
                            xor=('one_sample', 'fsgd', 'design', 'contrast'),
                            desc='construct X and C as a one-sample group mean')
    no_contrast_sok = traits.Bool(argstr='--no-contrasts-ok',
                                desc='do not fail if no contrasts specified')
    per_voxel_reg = InputMultiPath(File(exists=True), argstr='--pvr %s...',
                                 desc='per-voxel regressors')
    self_reg = traits.Tuple(traits.Int, traits.Int, traits.Int,
                           argstr='--selfreg %d %d %d',
                           desc='self-regressor from index col row slice')
    weighted_ls = File(exists=True, argstr='--wls %s',
                       xor=('weight_file', 'weight_inv', 'weight_sqrt'),
                       desc='weighted least squares')
    fixed_fx_var = File(exists=True, argstr='--yffxvar %s',
                      desc='for fixed effects analysis')
    fixed_fx_dof = traits.Int(argstr='--ffxdof %d',
                            xor=['fixed_fx_dof_file'],
                            desc='dof for fixed effects analysis')
    fixed_fx_dof_file = File(argstr='--ffxdofdat %d',
                          xor=['fixed_fx_dof'],
                          desc='text file with dof for fixed effects analysis')
    weight_file = File(exists=True, xor=['weighted_ls'],
                       desc='weight for each input at each voxel')
    weight_inv = traits.Bool(argstr='--w-inv', desc='invert weights',
                             xor=['weighted_ls'])
    weight_sqrt = traits.Bool(argstr='--w-sqrt', desc='sqrt of weights',
                              xor=['weighted_ls'])
    fwhm = traits.Float(min=0, argstr='--fwhm %f',
                        desc='smooth input by fwhm')
    var_fwhm = traits.Float(min=0, argstr='--var-fwhm %f',
                            desc='smooth variance by fwhm')
    no_mask_smooth = traits.Bool(argstr='--no-mask-smooth',
                                 desc='do not mask when smoothing')
    no_est_fwhm = traits.Bool(argstr='--no-est-fwhm',
                              desc='turn off FWHM output estimation')
    mask_file = File(exists=True, argstr='--mask %s', desc='binary mask')
    label_file = File(exists=True, argstr='--label %s',
                     xor=['cortex'],
                     desc='use label as mask, surfaces only')
    cortex = traits.Bool(argstr='--cortex',
                         xor=['label_file'],
                         desc='use subjects ?h.cortex.label as label')
    invert_mask = traits.Bool(argstr='--mask-inv',
                             desc='invert mask')
    prune = traits.Bool(argstr='--prune',
       desc='remove voxels that do not have a non-zero value at each frame (def)')
    no_prune = traits.Bool(argstr='--no-prune',
                           xor=['prunethresh'],
                           desc='do not prune')
    prune_thresh = traits.Float(argstr='--prune_thr %f',
                                xor=['noprune'],
                                desc='prune threshold. Default is FLT_MIN')
    compute_log_y = traits.Bool(argstr='--logy',
                       desc='compute natural log of y prior to analysis')
    save_estimate = traits.Bool(argstr='--yhat-save',
                               desc='save signal estimate (yhat)')
    save_residual = traits.Bool(argstr='--eres-save',
                               desc='save residual error (eres)')
    save_res_corr_mtx = traits.Bool(argstr='--eres-scm',
       desc='save residual error spatial correlation matrix (eres.scm). Big!')
    surf = traits.Bool(argstr="--surf %s %s %s",
                       requires=["subject_id", "hemi"],
                       desc="analysis is on a surface mesh")
    subject_id = traits.Str(desc="subject id for surface geometry")
    hemi = traits.Enum("lh", "rh", desc="surface hemisphere")
    surf_geo = traits.Str("white", usedefault=True,
                          desc="surface geometry name (e.g. white, pial)")
    simulation = traits.Tuple(traits.Enum('perm', 'mc-full', 'mc-z'),
                              traits.Int(min=1), traits.Float, traits.Str,
                              argstr='--sim %s %d %f %s',
                              desc='nulltype nsim thresh csdbasename')
    sim_sign = traits.Enum('abs', 'pos', 'neg', argstr='--sim-sign %s',
                          desc='abs, pos, or neg')
    uniform = traits.Tuple(traits.Float, traits.Float,
                           argstr='--uniform %f %f',
                      desc='use uniform distribution instead of gaussian')
    pca = traits.Bool(argstr='--pca',
                      desc='perform pca/svd analysis on residual')
    calc_AR1 = traits.Bool(argstr='--tar1',
                          desc='compute and save temporal AR1 of residual')
    save_cond = traits.Bool(argstr='--save-cond',
            desc='flag to save design matrix condition at each voxel')
    vox_dump = traits.Tuple(traits.Int, traits.Int, traits.Int,
                           argstr='--voxdump %d %d %d',
                           desc='dump voxel GLM and exit')
    seed = traits.Int(argstr='--seed %d', desc='used for synthesizing noise')
    synth = traits.Bool(argstr='--synth', desc='replace input with gaussian')
    resynth_test = traits.Int(argstr='--resynthtest %d', desc='test GLM by resynthsis')
    profile = traits.Int(argstr='--profile %d', desc='niters : test speed')
    force_perm = traits.Bool(argstr='--perm-force',
              desc='force perumtation test, even when design matrix is not orthog')
    diag = traits.Int('--diag %d', desc='Gdiag_no : set diagnositc level')
    diag_cluster = traits.Bool(argstr='--diag-cluster',
                            desc='save sig volume and exit from first sim loop')
    debug = traits.Bool(argstr='--debug', desc='turn on debugging')
    check_opts = traits.Bool(argstr='--checkopts',
                            desc="don't run anything, just check options and exit")
    allow_repeated_subjects = traits.Bool(argstr='--allowsubjrep',
      desc='allow subject names to repeat in the fsgd file (must appear before --fsgd')
    allow_ill_cond = traits.Bool(argstr='--illcond',
                 desc='allow ill-conditioned design matrices')
    sim_done_file = File(argstr='--sim-done %s',
                   desc='create file when simulation finished')


class GLMFitOutputSpec(TraitedSpec):

    glm_dir = Directory(exists=True, desc="output directory")
    beta_file = File(exists=True, desc="map of regression coefficients")
    error_file = File(desc="map of residual error")
    error_var_file = File(desc="map of residual error variance")
    error_stddev_file = File(desc="map of residual error standard deviation")
    estimate_file = File(desc="map of the estimated Y values")
    mask_file = File(desc="map of the mask used in the analysis")
    fwhm_file = File(desc="text file with estimated smoothness")
    dof_file = File(desc="text file with effective degrees-of-freedom for the analysis")
    gamma_file = OutputMultiPath(desc="map of contrast of regression coefficients")
    gamma_var_file = OutputMultiPath(desc="map of regression contrast variance")
    sig_file = OutputMultiPath(desc="map of F-test significance (in -log10p)")
    ftest_file = OutputMultiPath(desc="map of test statistic values")
    spatial_eigenvectors = File(desc="map of spatial eigenvectors from residual PCA")
    frame_eigenvectors = File(desc="matrix of frame eigenvectors from residual PCA")
    singular_values = File(desc="matrix singular values from residual PCA")
    svd_stats_file = File(desc="text file summarizing the residual PCA")


class GLMFit(FSCommand):
    """Use FreeSurfer's mri_glmfit to specify and estimate a general linear model.

    Examples
    --------

    >>> glmfit = GLMFit()
    >>> glmfit.inputs.in_file = 'functional.nii'
    >>> glmfit.inputs.one_sample = True
    >>> glmfit.cmdline == 'mri_glmfit --glmdir %s --y functional.nii --osgm'%os.getcwd()
    True

    """

    _cmd = 'mri_glmfit'
    input_spec = GLMFitInputSpec
    output_spec = GLMFitOutputSpec

    def _format_arg(self, name, spec, value):
        if name == "surf":
            _si = self.inputs
            return spec.argstr % (_si.subject_id, _si.hemi, _si.surf_geo)
        return super(GLMFit, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        # Get the top-level output directory
        if not isdefined(self.inputs.glm_dir):
            glmdir = os.getcwd()
        else:
            glmdir = os.path.abspath(self.inputs.glm_dir)
        outputs["glm_dir"] = glmdir

        # Assign the output files that always get created
        outputs["beta_file"] = os.path.join(glmdir, "beta.mgh")
        outputs["error_var_file"] = os.path.join(glmdir, "rvar.mgh")
        outputs["error_stddev_file"] = os.path.join(glmdir, "rstd.mgh")
        outputs["mask_file"] = os.path.join(glmdir, "mask.mgh")
        outputs["fwhm_file"] = os.path.join(glmdir, "fwhm.dat")
        outputs["dof_file"] = os.path.join(glmdir, "dof.dat")
        # Assign the conditional outputs
        if isdefined(self.inputs.save_residual) and self.inputs.save_residual:
            outputs["error_file"] = os.path.join(glmdir, "eres.mgh")
        if isdefined(self.inputs.save_estimate) and self.inputs.save_estimate:
            outputs["estimate_file"] = os.path.join(glmdir, "yhat.mgh")

        # Get the contrast directory name(s)
        if isdefined(self.inputs.contrast):
            contrasts = []
            for c in self.inputs.contrast:
                if split_filename(c)[2] in [".mat", ".dat", ".mtx", ".con"]:
                    contrasts.append(split_filename(c)[1])
                else:
                    contrasts.append(os.path.split(c)[1])
        elif isdefined(self.inputs.one_sample) and self.inputs.one_sample:
            contrasts = ["osgm"]

        # Add in the contrast images
        outputs["sig_file"] = [os.path.join(glmdir, c, "sig.mgh") for c in contrasts]
        outputs["ftest_file"] = [os.path.join(glmdir, c, "F.mgh") for c in contrasts]
        outputs["gamma_file"] = [os.path.join(glmdir, c, "gamma.mgh") for c in contrasts]
        outputs["gamma_var_file"] = [os.path.join(glmdir, c, "gammavar.mgh") for c in contrasts]

        # Add in the PCA results, if relevant
        if isdefined(self.inputs.pca) and self.inputs.pca:
            pcadir = os.path.join(glmdir, "pca-eres")
            outputs["spatial_eigenvectors"] = os.path.join(pcadir, "v.mgh")
            outputs["frame_eigenvectors"] = os.path.join(pcadir, "u.mtx")
            outputs["singluar_values"] = os.path.join(pcadir, "sdiag.mat")
            outputs["svd_stats_file"] = os.path.join(pcadir, "stats.dat")

        return outputs

    def _gen_filename(self, name):
        if name == 'glm_dir':
            return os.getcwd()
        return None


class OneSampleTTest(GLMFit):

    def __init__(self, **kwargs):
        super(OneSampleTTest, self).__init__(**kwargs)
        self.inputs.one_sample = True


class BinarizeInputSpec(FSTraitedSpec):
    in_file = File(exists=True, argstr='--i %s', mandatory=True,
                  copyfile=False, desc='input volume')
    min = traits.Float(argstr='--min %f',
                       desc='min thresh')
    max = traits.Float(argstr='--max %f',
                       desc='max thresh')
    rmin = traits.Float(argstr='--rmin %f',
                        desc='compute min based on rmin*globalmean')
    rmax = traits.Float(argstr='--rmax %f',
                        desc='compute max based on rmax*globalmean')
    match = traits.List(traits.Int, argstr='--match %d...',
                        desc='match instead of threshold')
    wm = traits.Bool(argstr='--wm',
         desc='set match vals to 2 and 41 (aseg for cerebral WM)')
    ventricles = traits.Bool(argstr='--ventricles',
         desc='set match vals those for aseg ventricles+choroid (not 4th)')
    wm_ven_csf = traits.Bool(argstr='--wm+vcsf',
          desc='WM and ventricular CSF, including choroid (not 4th)')
    binary_file = File(argstr='--o %s', genfile=True,
                  desc='binary output volume')
    out_type = traits.Enum('nii', 'nii.gz', 'mgz', argstr='',
                           desc='output file type')
    count_file = traits.Either(traits.Bool, File,
                              argstr='--count %s',
                  desc='save number of hits in ascii file (hits, ntotvox, pct)')
    bin_val = traits.Int(argstr='--binval %d',
                        desc='set vox within thresh to val (default is 1)')
    bin_val_not = traits.Int(argstr='--binvalnot %d',
                        desc='set vox outside range to val (default is 0)')
    invert = traits.Bool(argstr='--inv',
                         desc='set binval=0, binvalnot=1')
    frame_no = traits.Int(argstr='--frame %s',
                         desc='use 0-based frame of input (default is 0)')
    merge_file = File(exists=True, argstr='--merge %s',
                    desc='merge with mergevol')
    mask_file = File(exists=True, argstr='--mask maskvol',
                   desc='must be within mask')
    mask_thresh = traits.Float(argstr='--mask-thresh %f',
                    desc='set thresh for mask')
    abs = traits.Bool(argstr='--abs',
                      desc='take abs of invol first (ie, make unsigned)')
    bin_col_num = traits.Bool(argstr='--bincol',
                desc='set binarized voxel value to its column number')
    zero_edges = traits.Bool(argstr='--zero-edges',
                            desc='zero the edge voxels')
    zero_slice_edge = traits.Bool(argstr='--zero-slice-edges',
                       desc='zero the edge slice voxels')
    dilate = traits.Int(argstr='--dilate %d',
                        desc='niters: dilate binarization in 3D')
    erode = traits.Int(argstr='--erode  %d',
                       desc='nerode: erode binarization in 3D (after any dilation)')
    erode2d = traits.Int(argstr='--erode2d %d',
                         desc='nerode2d: erode binarization in 2D (after any 3D erosion)')


class BinarizeOutputSpec(TraitedSpec):
    binary_file = File(exists=True, desc='binarized output volume')
    count_file = File(desc='ascii file containing number of hits')


class Binarize(FSCommand):
    """Use FreeSurfer mri_binarize to threshold an input volume

    Examples
    --------

    >>> binvol = Binarize(in_file='structural.nii', min=10, binary_file='foo_out.nii')
    >>> binvol.cmdline
    'mri_binarize --o foo_out.nii --i structural.nii --min 10.000000'

   """

    _cmd = 'mri_binarize'
    input_spec = BinarizeInputSpec
    output_spec = BinarizeOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outfile = self.inputs.binary_file
        if not isdefined(outfile):
            if isdefined(self.inputs.out_type):
                outfile = fname_presuffix(self.inputs.in_file,
                                          newpath=os.getcwd(),
                                          suffix='.'.join(('_thresh',
                                                          self.inputs.out_type)),
                                          use_ext=False)
            else:
                outfile = fname_presuffix(self.inputs.in_file,
                                          newpath=os.getcwd(),
                                          suffix='_thresh')
        outputs['binary_file'] = outfile
        value = self.inputs.count_file
        if isdefined(value):
            if isinstance(value, bool):
                if value:
                    outputs['count_file'] = fname_presuffix(self.inputs.in_file,
                                                            suffix='_count.txt',
                                                            newpath=os.getcwd(),
                                                            use_ext=False)
            else:
                outputs['count_file'] = value
        return outputs

    def _format_arg(self, name, spec, value):
        if name == 'count_file':
            if isinstance(value, bool):
                fname = self._list_outputs()[name]
            else:
                fname = value
            return spec.argstr % fname
        if name == 'out_type':
            return ''
        return super(Binarize, self)._format_arg(name, spec, value)

    def _gen_filename(self, name):
        if name == 'binary_file':
            return self._list_outputs()[name]
        return None


class ConcatenateInputSpec(FSTraitedSpec):
    in_files = InputMultiPath(File(exists=True),
                 desc='Individual volumes to be concatenated',
                 argstr='--i %s...', mandatory=True)
    concatenated_file = File(desc='Output volume', argstr='--o %s',
                             genfile=True)
    sign = traits.Enum('abs', 'pos', 'neg', argstr='--%s',
          desc='Take only pos or neg voxles from input, or take abs')
    stats = traits.Enum('sum', 'var', 'std', 'max', 'min', 'mean', argstr='--%s',
          desc='Compute the sum, var, std, max, min or mean of the input volumes')
    paired_stats = traits.Enum('sum', 'avg', 'diff', 'diff-norm', 'diff-norm1',
                              'diff-norm2', argstr='--paired-%s',
                              desc='Compute paired sum, avg, or diff')
    gmean = traits.Int(argstr='--gmean %d',
                       desc='create matrix to average Ng groups, Nper=Ntot/Ng')
    mean_div_n = traits.Bool(argstr='--mean-div-n',
                           desc='compute mean/nframes (good for var)')
    multiply_by = traits.Float(argstr='--mul %f',
          desc='Multiply input volume by some amount')
    add_val = traits.Float(argstr='--add %f',
                          desc='Add some amount to the input volume')
    multiply_matrix_file = File(exists=True, argstr='--mtx %s',
          desc='Multiply input by an ascii matrix in file')
    combine = traits.Bool(argstr='--combine',
          desc='Combine non-zero values into single frame volume')
    keep_dtype = traits.Bool(argstr='--keep-datatype',
          desc='Keep voxelwise precision type (default is float')
    max_bonfcor = traits.Bool(argstr='--max-bonfcor',
          desc='Compute max and bonferroni correct (assumes -log10(ps))')
    max_index = traits.Bool(argstr='--max-index',
          desc='Compute the index of max voxel in concatenated volumes')
    mask_file = File(exists=True, argstr='--mask %s', desc='Mask input with a volume')
    vote = traits.Bool(argstr='--vote',
          desc='Most frequent value at each voxel and fraction of occurances')
    sort = traits.Bool(argstr='--sort',
          desc='Sort each voxel by ascending frame value')


class ConcatenateOutputSpec(TraitedSpec):
    concatenated_file = File(exists=True,
                  desc='Path/name of the output volume')


class Concatenate(FSCommand):
    """Use Freesurfer mri_concat to combine several input volumes
    into one output volume.  Can concatenate by frames, or compute
    a variety of statistics on the input volumes.

    Examples
    --------

    Combine two input volumes into one volume with two frames

    >>> concat = Concatenate()
    >>> concat.inputs.in_files = ['cont1.nii', 'cont2.nii']
    >>> concat.inputs.concatenated_file = 'bar.nii'
    >>> concat.cmdline
    'mri_concat --o bar.nii --i cont1.nii --i cont2.nii'

    """

    _cmd = 'mri_concat'
    input_spec = ConcatenateInputSpec
    output_spec = ConcatenateOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.concatenated_file):
            outputs['concatenated_file'] = os.path.join(os.getcwd(),
                                                        'concat_output.nii.gz')
        else:
            outputs['concatenated_file'] = self.inputs.concatenated_file
        return outputs

    def _gen_filename(self, name):
        if name == 'concatenated_file':
            return self._list_outputs()[name]
        return None


class SegStatsInputSpec(FSTraitedSpec):
    _xor_inputs = ('segmentation_file', 'annot', 'surf_label')
    segmentation_file = File(exists=True, argstr='--seg %s', xor=_xor_inputs,
                  mandatory=True, desc='segmentation volume path')
    annot = traits.Tuple(traits.Str, traits.Enum('lh', 'rh'), traits.Str,
                         argstr='--annot %s %s %s', xor=_xor_inputs,
                         mandatory=True,
                         desc='subject hemi parc : use surface parcellation')
    surf_label = traits.Tuple(traits.Str, traits.Enum('lh', 'rh'), traits.Str,
                             argstr='--slabel %s %s %s', xor=_xor_inputs,
                             mandatory=True,
                             desc='subject hemi label : use surface label')
    summary_file = File(argstr='--sum %s', genfile=True,
                   desc='Segmentation stats summary table file')
    partial_volume_file = File(exists=True, argstr='--pv %f',
                  desc='Compensate for partial voluming')
    in_file = File(exists=True, argstr='--i %s',
                 desc='Use the segmentation to report stats on this volume')
    frame = traits.Int(argstr='--frame %d',
                       desc='Report stats on nth frame of input volume')
    multiply = traits.Float(argstr='--mul %f', desc='multiply input by val')
    calc_snr = traits.Bool(argstr='--snr', desc='save mean/std as extra column in output table')
    calc_power = traits.Enum('sqr', 'sqrt', argstr='--%s',
                          desc='Compute either the sqr or the sqrt of the input')
    _ctab_inputs = ('color_table_file', 'default_color_table', 'gca_color_table')
    color_table_file = File(exists=True, argstr='--ctab %s', xor=_ctab_inputs,
                desc='color table file with seg id names')
    default_color_table = traits.Bool(argstr='--ctab-default', xor=_ctab_inputs,
                desc='use $FREESURFER_HOME/FreeSurferColorLUT.txt')
    gca_color_table = File(exists=True, argstr='--ctab-gca %s', xor=_ctab_inputs,
                desc='get color table from GCA (CMA)')
    segment_id = traits.List(argstr='--id %s...', desc='Manually specify segmentation ids')
    exclude_id = traits.Int(argstr='--excludeid %d', desc='Exclude seg id from report')
    exclude_ctx_gm_wm = traits.Bool(argstr='--excl-ctxgmwm',
                                 desc='exclude cortical gray and white matter')
    wm_vol_from_surf = traits.Bool(argstr='--surf-wm-vol', desc='Compute wm volume from surf')
    cortex_vol_from_surf = traits.Bool(argstr='--surf-ctx-vol', desc='Compute cortex volume from surf')
    non_empty_only = traits.Bool(argstr='--nonempty', desc='Only report nonempty segmentations')
    mask_file = File(exists=True, argstr='--mask %s',
                   desc='Mask volume (same size as seg')
    mask_thresh = traits.Float(argstr='--maskthresh %f',
                              desc='binarize mask with this threshold <0.5>')
    mask_sign = traits.Enum('abs', 'pos', 'neg', '--masksign %s',
                           desc='Sign for mask threshold: pos, neg, or abs')
    mask_frame = traits.Int('--maskframe %d',
                            requires=['mask_file'],
                            desc='Mask with this (0 based) frame of the mask volume')
    mask_invert = traits.Bool(argstr='--maskinvert', desc='Invert binarized mask volume')
    mask_erode = traits.Int(argstr='--maskerode %d', desc='Erode mask by some amount')
    brain_vol = traits.Enum('brain-vol-from-seg', 'brainmask', '--%s',
         desc='Compute brain volume either with ``brainmask`` or ``brain-vol-from-seg``')
    etiv = traits.Bool(argstr='--etiv', desc='Compute ICV from talairach transform')
    etiv_only = traits.Enum('etiv', 'old-etiv', '--%s-only',
                           desc='Compute etiv and exit.  Use ``etiv`` or ``old-etiv``')
    avgwf_txt_file = traits.Either(traits.Bool, File, argstr='--avgwf %s',
                             desc='Save average waveform into file (bool or filename)')
    avgwf_file = traits.Either(traits.Bool, File, argstr='--avgwfvol %s',
                             desc='Save as binary volume (bool or filename)')
    sf_avg_file = traits.Either(traits.Bool, File, argstr='--sfavg %s',
                          desc='Save mean across space and time')
    vox = traits.List(traits.Int, argstr='--vox %s',
                     desc='Replace seg with all 0s except at C R S (three int inputs)')


class SegStatsOutputSpec(TraitedSpec):
    summary_file = File(exists=True, desc='Segmentation summary statistics table')
    avgwf_txt_file = File(desc='Text file with functional statistics averaged over segs')
    avgwf_file = File(desc='Volume with functional statistics averaged over segs')
    sf_avg_file = File(desc='Text file with func statistics averaged over segs and framss')


class SegStats(FSCommand):
    """Use FreeSurfer mri_segstats for ROI analysis

    Examples
    --------

    >>> import nipype.interfaces.freesurfer as fs
    >>> ss = fs.SegStats()
    >>> ss.inputs.annot = ('PWS04', 'lh', 'aparc')
    >>> ss.inputs.in_file = 'functional.nii'
    >>> ss.inputs.subjects_dir = '.'
    >>> ss.inputs.avgwf_txt_file = './avgwf.txt'
    >>> ss.inputs.summary_file = './summary.stats'
    >>> ss.cmdline
    'mri_segstats --annot PWS04 lh aparc --avgwf ./avgwf.txt --i functional.nii --sum ./summary.stats'

    """

    _cmd = 'mri_segstats'
    input_spec = SegStatsInputSpec
    output_spec = SegStatsOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['summary_file'] = self.inputs.summary_file
        if not isdefined(outputs['summary_file']):
            outputs['summary_file'] = os.path.join(os.getcwd(), 'summary.stats')
        suffices = dict(avgwf_txt_file='_avgwf.txt', avgwf_file='_avgwf.nii.gz',
                        sf_avg_file='sfavg.txt')
        if isdefined(self.inputs.segmentation_file):
            _, src = os.path.split(self.inputs.segmentation_file)
        if isdefined(self.inputs.annot):
            src = '_'.join(self.inputs.annot)
        if isdefined(self.inputs.surf_label):
            src = '_'.join(self.inputs.surf_label)
        for name, suffix in suffices.items():
            value = getattr(self.inputs, name)
            if isdefined(value):
                if isinstance(value, bool):
                    outputs[name] = fname_presuffix(src, suffix=suffix,
                                                    newpath=os.getcwd(),
                                                    use_ext=False)
                else:
                    outputs[name] = value
        return outputs

    def _format_arg(self, name, spec, value):
        if name in ['avgwf_txt_file', 'avgwf_file', 'sf_avg_file']:
            if isinstance(value, bool):
                fname = self._list_outputs()[name]
            else:
                fname = value
            return spec.argstr % fname
        return super(SegStats, self)._format_arg(name, spec, value)

    def _gen_filename(self, name):
        if name == 'summary_file':
            return self._list_outputs()[name]
        return None


class Label2VolInputSpec(FSTraitedSpec):
    label_file = InputMultiPath(File(exists=True), argstr='--label %s...',
                   xor=('label_file', 'annot_file', 'seg_file', 'aparc_aseg'),
                               copyfile=False,
                               mandatory=True,
                               desc='list of label files')
    annot_file = File(exists=True, argstr='--annot %s',
                     xor=('label_file', 'annot_file', 'seg_file', 'aparc_aseg'),
                     requires=('subject_id', 'hemi'),
                     mandatory=True,
                     copyfile=False,
                     desc='surface annotation file')
    seg_file = File(exists=True, argstr='--seg %s',
                   xor=('label_file', 'annot_file', 'seg_file', 'aparc_aseg'),
                   mandatory=True,
                   copyfile=False,
                   desc='segmentation file')
    aparc_aseg = traits.Bool(argstr='--aparc+aseg',
                            xor=('label_file', 'annot_file', 'seg_file', 'aparc_aseg'),
                            mandatory=True,
                            desc='use aparc+aseg.mgz in subjectdir as seg')
    template_file = File(exists=True, argstr='--temp %s', mandatory=True,
                    desc='output template volume')
    reg_file = File(exists=True, argstr='--reg %s',
                    xor=('reg_file', 'reg_header', 'identity'),
                    desc='tkregister style matrix VolXYZ = R*LabelXYZ')
    reg_header = File(exists=True, argstr='--regheader %s',
                      xor=('reg_file', 'reg_header', 'identity'),
                      desc='label template volume')
    identity = traits.Bool(argstr='--identity',
                           xor=('reg_file', 'reg_header', 'identity'),
                           desc='set R=I')
    invert_mtx = traits.Bool(argstr='--invertmtx',
                            desc='Invert the registration matrix')
    fill_thresh = traits.Range(0., 1., argstr='--fillthresh %.f',
                              desc='thresh : between 0 and 1')
    label_voxel_volume = traits.Float(argstr='--labvoxvol %f',
                             desc='volume of each label point (def 1mm3)')
    proj = traits.Tuple(traits.Enum('abs', 'frac'), traits.Float,
                        traits.Float, traits.Float,
                        argstr='--proj %s %f %f %f',
                        requries=('subject_id', 'hemi'),
                        desc='project along surface normal')
    subject_id = traits.Str(argstr='--subject %s',
                           desc='subject id')
    hemi = traits.Enum('lh', 'rh', argstr='--hemi %s',
                       desc='hemisphere to use lh or rh')
    surface = traits.Str(argstr='--surf %s',
                         desc='use surface instead of white')
    vol_label_file = File(argstr='--o %s', genfile=True,
                          desc='output volume')
    label_hit_file = File(argstr='--hits %s',
                           desc='file with each frame is nhits for a label')
    map_label_stat = File(argstr='--label-stat %s',
                    desc='map the label stats field into the vol')
    native_vox2ras = traits.Bool(argstr='--native-vox2ras',
               desc='use native vox2ras xform instead of  tkregister-style')


class Label2VolOutputSpec(TraitedSpec):
    vol_label_file = File(exists=True, desc='output volume')


class Label2Vol(FSCommand):
    """Make a binary volume from a Freesurfer label

    Examples
    --------

    >>> binvol = Label2Vol(label_file='cortex.label', template_file='structural.nii', reg_file='register.dat', fill_thresh=0.5, vol_label_file='foo_out.nii')
    >>> binvol.cmdline
    'mri_label2vol --fillthresh 0 --label cortex.label --reg register.dat --temp structural.nii --o foo_out.nii'

   """

    _cmd = 'mri_label2vol'
    input_spec = Label2VolInputSpec
    output_spec = Label2VolOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outfile = self.inputs.vol_label_file
        if not isdefined(outfile):
            for key in ['label_file', 'annot_file', 'seg_file']:
                if isdefined(getattr(self.inputs,key)):
                    _, src = os.path.split(getattr(self.inputs, key))
            if isdefined(self.inputs.aparc_aseg):
                src = 'aparc+aseg.mgz'
            outfile = fname_presuffix(src, suffix='_vol.nii.gz',
                                      newpath=os.getcwd(),
                                      use_ext=False)
        outputs['vol_label_file'] = outfile
        return outputs

    def _gen_filename(self, name):
        if name == 'vol_label_file':
            return self._list_outputs()[name]
        return None


class MS_LDAInputSpec(FSTraitedSpec):
    lda_labels = traits.List(traits.Int(), argstr='-lda %s', mandatory=True,
                             minlen=2, maxlen=2, sep=' ',
                             desc='pair of class labels to optimize')
    weight_file = traits.File(argstr='-weight %s', mandatory=True,
                        desc='filename for the LDA weights (input or output)')
    output_synth = traits.File(exists=False, argstr='-synth %s',
                               mandatory=True,
                             desc='filename for the synthesized output volume')
    label_file = traits.File(exists=True, argstr='-label %s',
                             desc='filename of the label volume')
    mask_file = traits.File(exists=True, argstr='-mask %s',
                            desc='filename of the brain mask volume')
    shift = traits.Int(argstr='-shift %d',
                      desc='shift all values equal to the given value to zero')
    conform = traits.Bool(argstr='-conform',
                          desc=('Conform the input volumes (brain mask '
                                'typically already conformed)'))
    use_weights = traits.Bool(argstr='-W',
                              desc=('Use the weights from a previously '
                                    'generated weight file'))
    images = InputMultiPath(File(exists=True), argstr='%s', mandatory=True,
                            copyfile=False, desc='list of input FLASH images',
                            position=-1)


class MS_LDAOutputSpec(TraitedSpec):
    weight_file = File(exists=True, desc='')
    vol_synth_file = File(exists=True, desc='')


class MS_LDA(FSCommand):
    """Perform LDA reduction on the intensity space of an arbitrary # of FLASH images

    Examples
    --------

    >>> grey_label = 2
    >>> white_label = 3
    >>> zero_value = 1
    >>> optimalWeights = MS_LDA(lda_labels=[grey_label, white_label], \
                                label_file='label.mgz', weight_file='weights.txt', \
                                shift=zero_value, output_synth='synth_out.mgz', \
                                conform=True, use_weights=True, \
                                images=['FLASH1.mgz', 'FLASH2.mgz', 'FLASH3.mgz'])
    >>> optimalWeights.cmdline
    'mri_ms_LDA -conform -label label.mgz -lda 2 3 -synth synth_out.mgz -shift 1 -W -weight weights.txt FLASH1.mgz FLASH2.mgz FLASH3.mgz'
    """

    _cmd = 'mri_ms_LDA'
    input_spec = MS_LDAInputSpec
    output_spec = MS_LDAOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['vol_synth_file'] = os.path.abspath(self.inputs.output_synth)
        if not isdefined(self.inputs.use_weights) or self.inputs.use_weights is False:
            outputs['weight_file'] = os.path.abspath(self.inputs.weight_file)
        return outputs

    def _verify_weights_file_exists(self):
        if not os.path.exists(os.path.abspath(self.inputs.weight_file)):
            raise traits.TraitError("MS_LDA: use_weights must accompany an existing weights file")

    def _format_arg(self, name, spec, value):
        if name is 'use_weights':
            if self.inputs.use_weights is True:
                self._verify_weights_file_exists()
            else:
                return ''
                # TODO: Fix bug when boolean values are set explicitly to false
        return super(MS_LDA, self)._format_arg(name, spec, value)

    def _gen_filename(self, name):
        pass
