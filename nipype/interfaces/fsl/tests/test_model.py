# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import tempfile
import shutil

from nipype.testing import (assert_equal, assert_not_equal, assert_true,
                            assert_raises, skipif)
import nipype.interfaces.fsl as fsl
from nipype.interfaces.fsl import no_fsl
# XXX Write tests for fsl_model


@skipif(no_fsl)
def test_contrastmgr():
    input_map = dict(args = dict(argstr='%s',),
                     contrast_num = dict(argstr='-cope',),
                     environ = dict(),
                     fcon_file = dict(argstr='-f %s',),
                     output_type = dict(),
                     stats_dir = dict(mandatory=True,argstr='%s',),
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
                     autocorr_estimate = dict(xor=['autocorr_noestimate'],argstr='-ac',),
                     autocorr_noestimate = dict(xor=['autocorr_estimate'],argstr='-noest',),
                     brightness_threshold = dict(argstr='-epith %d',),
                     design_file = dict(argstr='%s',),
                     environ = dict(),
                     fit_armodel = dict(argstr='-ar',),
                     full_data = dict(argstr='-v',),
                     in_file = dict(mandatory=True,argstr='%s',),
                     mask_size = dict(argstr='-ms %d',),
                     multitaper_product = dict(argstr='-mt %d',),
                     output_pwdata = dict(argstr='-output_pwdata',),
                     output_type = dict(),
                     results_dir = dict(argstr='-rn %s',),
                     smooth_autocorr = dict(argstr='-sa',),
                     threshold = dict(argstr='%f',),
                     tukey_window = dict(argstr='-tukey %d',),
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
