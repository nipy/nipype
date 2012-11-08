# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import tempfile
import shutil

from nipype.testing import (assert_equal, assert_not_equal, assert_true,
                            assert_raises, skipif)
import nipype.interfaces.fsl.model as fsl
from nipype.interfaces.fsl import Info
from nipype.interfaces.fsl import no_fsl
# XXX Write tests for fsl_model

tmp_infile = None
tmp_dir = None
cwd = None

@skipif(no_fsl)
def setup_infile():
    global tmp_infile, tmp_dir, cwd
    cwd = os.getcwd()
    ext = Info.output_type_to_ext(Info.output_type())
    tmp_dir = tempfile.mkdtemp()
    tmp_infile = os.path.join(tmp_dir, 'foo' + ext)
    file(tmp_infile, 'w')
    os.chdir(tmp_dir)
    return tmp_infile, tmp_dir

def teardown_infile(tmp_dir):
    os.chdir(cwd)
    shutil.rmtree(tmp_dir)


@skipif(no_fsl)
def test_contrastmgr():
    input_map = dict(args = dict(argstr='%s',),
                    contrast_num = dict(argstr='-cope',),
                    corrections = dict(copyfile=False,mandatory=True,),
                    dof_file = dict(copyfile=False,mandatory=True,argstr='',),
                    environ = dict(usedefault=True,),
                    fcon_file = dict(argstr='-f %s',),
                    ignore_exception = dict(usedefault=True,),
                    output_type = dict(),
                    param_estimates = dict(copyfile=False,mandatory=True,argstr='',),
                    sigmasquareds = dict(copyfile=False,mandatory=True,argstr='',),
                    suffix = dict(argstr='-suffix %s',),
                    tcon_file = dict(mandatory=True,argstr='%s',),
                    )
    instance = fsl.ContrastMgr()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value


@skipif(no_fsl)
def test_feat():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(),
                     fsf_file = dict(mandatory=True,argstr='%s',),
                     output_type = dict(),
                     )
    instance = fsl.FEAT()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

@skipif(no_fsl)
def test_featmodel():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(),
                     fsf_file = dict(copyfile=False,mandatory=True,argstr='%s',),
                     output_type = dict(),
                     )
    instance = fsl.FEATModel()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value


def test_featregister():
    input_map = dict(feat_dirs = dict(mandatory=True,),
                     reg_dof = dict(),
                     reg_image = dict(mandatory=True,),
                     )
    instance = fsl.FEATRegister()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

@skipif(no_fsl)
def test_filmgls():
    input_map = dict(args = dict(argstr='%s',),
                     autocorr_estimate_only = dict(xor=['autocorr_estimate_only', 'fit_armodel', 'tukey_window', 'multitaper_product', 'use_pava', 'autocorr_noestimate'],argstr='-ac',),
                    autocorr_noestimate = dict(xor=['autocorr_estimate_only', 'fit_armodel', 'tukey_window', 'multitaper_product', 'use_pava', 'autocorr_noestimate'],argstr='-noest',),
                    brightness_threshold = dict(argstr='-epith %d',),
                    design_file = dict(argstr='%s',),
                    environ = dict(usedefault=True,),
                    fit_armodel = dict(xor=['autocorr_estimate_only', 'fit_armodel', 'tukey_window', 'multitaper_product', 'use_pava', 'autocorr_noestimate'],argstr='-ar',),
                    full_data = dict(argstr='-v',),
                    ignore_exception = dict(usedefault=True,),
                    in_file = dict(mandatory=True,argstr='%s',),
                    mask_size = dict(argstr='-ms %d',),
                    multitaper_product = dict(xor=['autocorr_estimate_only', 'fit_armodel', 'tukey_window', 'multitaper_product', 'use_pava', 'autocorr_noestimate'],argstr='-mt %d',),
                    output_pwdata = dict(argstr='-output_pwdata',),
                    output_type = dict(),
                    results_dir = dict(usedefault=True,argstr='-rn %s',),
                    smooth_autocorr = dict(argstr='-sa',),
                    threshold = dict(argstr='%f',),
                    tukey_window = dict(xor=['autocorr_estimate_only', 'fit_armodel', 'tukey_window', 'multitaper_product', 'use_pava', 'autocorr_noestimate'],argstr='-tukey %d',),
                    use_pava = dict(argstr='-pava',),
                    )
    instance = fsl.FILMGLS()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

@skipif(no_fsl)
def test_flameo():
    input_map = dict(args = dict(argstr='%s',),
                     burnin = dict(argstr='--burnin=%d',),
                     cope_file = dict(mandatory=True,argstr='--copefile=%s',),
                     cov_split_file = dict(mandatory=True,argstr='--covsplitfile=%s',),
                     design_file = dict(mandatory=True,argstr='--designfile=%s',),
                     dof_var_cope_file = dict(argstr='--dofvarcopefile=%s',),
                     environ = dict(),
                     f_con_file = dict(argstr='--fcontrastsfile=%s',),
                     fix_mean = dict(argstr='--fixmean',),
                     infer_outliers = dict(argstr='--inferoutliers',),
                     log_dir = dict(argstr='--ld=%s',),
                     mask_file = dict(mandatory=True,argstr='--maskfile=%s',),
                     n_jumps = dict(argstr='--njumps=%d',),
                     no_pe_outputs = dict(argstr='--nopeoutput',),
                     outlier_iter = dict(argstr='--ioni=%d',),
                     output_type = dict(),
                     run_mode = dict(argstr='--runmode=%s',mandatory=True,),
                     sample_every = dict(argstr='--sampleevery=%d',),
                     sigma_dofs = dict(argstr='--sigma_dofs=%d',),
                     t_con_file = dict(mandatory=True,argstr='--tcontrastsfile=%s',),
                     var_cope_file = dict(argstr='--varcopefile=%s',),
                     )
    instance = fsl.FLAMEO()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

@skipif(no_fsl)
def test_l2model():
    input_map = dict(num_copes = dict(mandatory=True,),
                     )
    instance = fsl.L2Model()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_level1design():
    input_map = dict(bases = dict(mandatory=True,),
                     contrasts = dict(),
                     interscan_interval = dict(mandatory=True,),
                     model_serial_correlations = dict(),
                     session_info = dict(mandatory=True,),
                     )
    instance = fsl.Level1Design()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

@skipif(no_fsl)
def test_melodic():
    input_map = dict(ICs = dict(),
                     approach = dict(),
                     args = dict(argstr='%s',),
                     bg_image = dict(),
                     bg_threshold = dict(),
                     cov_weight = dict(),
                     dim = dict(),
                     dim_est = dict(),
                     environ = dict(),
                     epsilon = dict(),
                     epsilonS = dict(),
                     in_files = dict(mandatory=True,),
                     log_power = dict(),
                     mask = dict(),
                     max_restart = dict(),
                     maxit = dict(),
                     mix = dict(),
                     mm_thresh = dict(),
                     no_bet = dict(),
                     no_mask = dict(),
                     no_mm = dict(),
                     non_linearity = dict(),
                     num_ICs = dict(),
                     out_all = dict(),
                     out_dir = dict(),
                     out_mean = dict(),
                     out_orig = dict(),
                     out_pca = dict(),
                     out_stats = dict(),
                     out_unmix = dict(),
                     out_white = dict(),
                     output_type = dict(),
                     pbsc = dict(),
                     rem_cmp = dict(),
                     remove_deriv = dict(),
                     report = dict(),
                     report_maps = dict(),
                     s_con = dict(),
                     s_des = dict(),
                     sep_vn = dict(),
                     sep_whiten = dict(),
                     smode = dict(),
                     t_con = dict(),
                     t_des = dict(),
                     tr_sec = dict(),
                     update_mask = dict(),
                     var_norm = dict(),
                     )
    instance = fsl.MELODIC()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

@skipif(no_fsl)
def test_smm():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(),
                     mask = dict(copyfile=False,mandatory=True,argstr='--mask="%s"',),
                     no_deactivation_class = dict(argstr='--zfstatmode',),
                     output_type = dict(),
                     spatial_data_file = dict(copyfile=False,mandatory=True,argstr='--sdf="%s"',),
                     )
    instance = fsl.SMM()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

@skipif(no_fsl)
def test_MultipleRegressDesign():
    _, tp_dir = setup_infile()
    foo = fsl.MultipleRegressDesign()
    foo.inputs.regressors = dict(reg1=[1,1,1],reg2=[0.2,0.4,0.5],reg3=[1,-1,2])
    con1 = ['con1','T',['reg1','reg2'],[0.5,0.5]]
    con2 = ['con2','T',['reg3'],[1]]
    foo.inputs.contrasts = [con1,con2,['con3','F',[con1,con2]]]
    res = foo.run()
    yield assert_equal, res.outputs.design_mat, os.path.join(os.getcwd(),'design.mat')
    yield assert_equal, res.outputs.design_con, os.path.join(os.getcwd(),'design.con')
    yield assert_equal, res.outputs.design_fts, os.path.join(os.getcwd(),'design.fts')
    yield assert_equal, res.outputs.design_grp, os.path.join(os.getcwd(),'design.grp')

@skipif(no_fsl)
def test_smoothestimate():
    input_map = dict(args = dict(argstr='%s',),
                     dof = dict(mandatory=True,xor=['zstat_file'],argstr='--dof=%d',),
                     environ = dict(usedefault=True,),
                     mask_file = dict(mandatory=True,argstr='--mask=%s',),
                     output_type = dict(),
                     residual_fit_file = dict(requires=['dof'],argstr='--res=%s',),
                     zstat_file = dict(xor=['dof'],argstr='--zstat=%s',),
                     )
    instance = fsl.SmoothEstimate()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

@skipif(no_fsl)
def test_cluster():
    input_map = dict(args = dict(argstr='%s',),
                     connectivity = dict(argstr='--connectivity=%d',),
                     cope_file = dict(argstr='--cope=%s',),
                     dlh = dict(argstr='--dlh=%.10f',),
                     environ = dict(usedefault=True,),
                     find_min = dict(),
                     fractional = dict(),
                     in_file = dict(mandatory=True,argstr='--in=%s',),
                     minclustersize = dict(argstr='--minclustersize',),
                     no_table = dict(),
                     num_maxima = dict(argstr='--num=%d',),
                     out_index_file = dict(argstr='--oindex=%s',),
                     out_localmax_txt_file = dict(argstr='--olmax=%s',),
                     out_localmax_vol_file = dict(argstr='--olmaxim=%s',),
                     out_max_file = dict(argstr='--omax=%s',),
                     out_mean_file = dict(argstr='--omean=%s',),
                     out_pval_file = dict(argstr='--opvals=%s',),
                     out_size_file = dict(argstr='--osize=%s',),
                     out_threshold_file = dict(argstr='--othresh=%s',),
                     output_type = dict(),
                     peak_distance = dict(argstr='--peakdist=%.10f',),
                     pthreshold = dict(requires=['dlh', 'volume'],argstr='--pthresh=%.10f',),
                     std_space_file = dict(argstr='--stdvol=%s',),
                     threshold = dict(mandatory=True,argstr='--thresh=%.10f',),
                     use_mm = dict(),
                     volume = dict(argstr='--volume=%d',),
                     warpfield_file = dict(argstr='--warpvol=%s',),
                     xfm_file = dict(argstr='--xfm=%s',),
                     )
    instance = fsl.Cluster()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

@skipif(no_fsl)
def test_randomise():
    input_map = dict(args = dict(argstr='%s',),
                     base_name = dict(argstr='-o "%s"',usedefault=True,),
                     c_thresh = dict(argstr='-c %.2f',),
                     cm_thresh = dict(argstr='-C %.2f',),
                     demean = dict(argstr='-D',),
                     design_mat = dict(argstr='-d %s',),
                     environ = dict(usedefault=True,),
                     f_c_thresh = dict(argstr='-F %.2f',),
                     f_cm_thresh = dict(argstr='-S %.2f',),
                     f_only = dict(argstr='--f_only',),
                     fcon = dict(argstr='-f %s',),
                     ignore_exception = dict(usedefault=True,),
                     in_file = dict(argstr='-i %s',mandatory=True,),
                     mask = dict(argstr='-m %s',),
                     num_perm = dict(argstr='-n %d',),
                     one_sample_group_mean = dict(argstr='-1',),
                     output_type = dict(),
                     p_vec_n_dist_files = dict(argstr='-P',),
                     raw_stats_imgs = dict(argstr='-R',),
                     seed = dict(argstr='--seed %d',),
                     show_info_parallel_mode = dict(argstr='-Q',),
                     show_total_perms = dict(argstr='-q',),
                     tcon = dict(argstr='-t %s',),
                     tfce = dict(argstr='-T',),
                     tfce2D = dict(argstr='--T2',),
                     tfce_C = dict(argstr='--tfce_C %.2f',),
                     tfce_E = dict(argstr='--tfce_E %.2f',),
                     tfce_H = dict(argstr='--tfce_H %.2f',),
                     var_smooth = dict(argstr='-v %d',),
                     vox_p_values = dict(argstr='-x',),
                     vxf = dict(argstr='--vxf %d',),
                     vxl = dict(argstr='--vxl %d',),
                     x_block_labels = dict(argstr='-e %s',),
                     )
    instance = fsl.Randomise()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value
