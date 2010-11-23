# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import tempfile
import shutil

from tempfile import mkdtemp
from shutil import rmtree

import numpy as np

import nibabel as nb

from nose import with_setup

from nipype.testing import ( assert_equal, assert_not_equal,
                             assert_raises, skipif, example_data)
import nipype.interfaces.fsl.dti as fsl
from nipype.interfaces.fsl import Info, no_fsl

# nosetests --with-doctest path_to/test_fsl.py

def test_bedpostx():
    input_map = dict(args = dict(argstr='%s',),
                     bpx_directory = dict(argstr='%s',),
                     burn_period = dict(argstr='-b %d',),
                     bvals = dict(mandatory=True,),
                     bvecs = dict(mandatory=True,),
                     dwi = dict(mandatory=True,),
                     environ = dict(),
                     fibres = dict(argstr='-n %d',),
                     jumps = dict(argstr='-j %d',),
                     mask = dict(mandatory=True,),
                     output_type = dict(),
                     sampling = dict(argstr='-s %d',),
                     weight = dict(argstr='-w %.2f',),
                     )
    instance = fsl.BEDPOSTX()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_dtifit():
    input_map = dict(args = dict(argstr='%s',),
                     base_name = dict(argstr='-o %s',),
                     bvals = dict(argstr='-b %s',mandatory=True,),
                     bvecs = dict(argstr='-r %s',mandatory=True,),
                     cni = dict(argstr='-cni %s',),
                     dwi = dict(argstr='-k %s',mandatory=True,),
                     environ = dict(),
                     little_bit = dict(argstr='--littlebit',),
                     mask = dict(argstr='-m %s',mandatory=True,),
                     max_x = dict(argstr='-X %d',),
                     max_y = dict(argstr='-Y %d',),
                     max_z = dict(argstr='-Z %d',),
                     min_x = dict(argstr='-x %d',),
                     min_y = dict(argstr='-y %d',),
                     min_z = dict(argstr='-z %d',),
                     output_type = dict(),
                     save = dict(argstr='--save_tensor',),
                     sse = dict(argstr='--sse',),
                     )
    instance = fsl.DTIFit()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

@skipif(no_fsl)
def test_eddycorrect():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(),
                     in_file = dict(argstr='%s',mandatory=True,),
                     out_file = dict(argstr='%s',),
                     output_type = dict(),
                     ref_num = dict(mandatory=True,argstr='%d',),
                     )
    instance = fsl.EddyCorrect()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

@skipif(no_fsl)
def test_findthebiggest():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(),
                     in_files = dict(argstr='%s',mandatory=True,),
                     out_file = dict(argstr='%s',),
                     output_type = dict(),
                     )
    instance = fsl.FindTheBiggest()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

@skipif(no_fsl)
def test_probtrackx():
    input_map = dict(args = dict(argstr='%s',),
                     avoid_mp = dict(argstr='--avoid=%s',),
                     bpx_directory = dict(mandatory=True,),
                     c_thresh = dict(argstr='--cthr=%.3f',),
                     correct_path_distribution = dict(argstr='--pd',),
                     dist_thresh = dict(argstr='--distthresh=%.3f',),
                     environ = dict(),
                     fibst = dict(argstr='--fibst=%d',),
                     force_dir = dict(argstr='--forcedir',),
                     inv_xfm = dict(argstr='--invxfm=%s',),
                     loop_check = dict(argstr='--loopcheck',),
                     mask = dict(argstr='-m %s',mandatory=True,),
                     mask2 = dict(argstr='--mask2=%s',),
                     mesh = dict(argstr='--mesh=%s',),
                     mod_euler = dict(argstr='--modeuler',),
                     mode = dict(argstr='--mode=%s',),
                     n_samples = dict(argstr='--nsamples=%d',),
                     n_steps = dict(argstr='--nsteps=%d',),
                     network = dict(argstr='--network',),
                     opd = dict(argstr='--opd',),
                     os2t = dict(argstr='--os2t',),
                     out_dir = dict(argstr='--dir=%s',),
                     output_type = dict(),
                     paths_file = dict(argstr='--out=%s',),
                     rand_fib = dict(argstr='--randfib %d',),
                     random_seed = dict(argstr='--rseed',),
                     s2tastext = dict(argstr='--s2tastext',),
                     sample_random_points = dict(argstr='--sampvox',),
                     samplesbase_name = dict(argstr='-s %s',),
                     seed_file = dict(argstr='-x %s',mandatory=True,),
                     seed_ref = dict(argstr='--seedref=%s',),
                     step_length = dict(argstr='--steplength=%.3f',),
                     stop_mask = dict(argstr='--stop=%s',),
                     target_masks = dict(argstr='--targetmasks=%s',),
                     use_anisotropy = dict(argstr='--usef',),
                     waypoints = dict(argstr='--waypoints=%s',),
                     xfm = dict(argstr='--xfm=%s',),
                     )
    instance = fsl.ProbTrackX()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

@skipif(no_fsl)
def test_projthresh():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(),
                     in_files = dict(argstr='%s',mandatory=True,),
                     output_type = dict(),
                     threshold = dict(mandatory=True,argstr='%d',),
                     )
    instance = fsl.ProjThresh()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_randomise():
    input_map = dict(args = dict(argstr='%s',),
                     base_name = dict(argstr='-o %s',),
                     c_thresh = dict(argstr='-c %.2f',),
                     cm_thresh = dict(argstr='-C %.2f',),
                     demean = dict(argstr='-D',),
                     design_mat = dict(argstr='-d %s',mandatory=True,),
                     environ = dict(),
                     f_c_thresh = dict(argstr='-F %.2f',),
                     f_cm_thresh = dict(argstr='-S %.2f',),
                     f_only = dict(argstr='--f_only',),
                     fcon = dict(argstr='-f %s',),
                     in_file = dict(argstr='-i %s',mandatory=True,),
                     mask = dict(argstr='-m %s',),
                     num_perm = dict(argstr='-n %d',),
                     one_sample_group_mean = dict(argstr='-l',),
                     output_type = dict(),
                     p_vec_n_dist_files = dict(argstr='-P',),
                     raw_stats_imgs = dict(argstr='-R',),
                     seed = dict(argstr='--seed %d',),
                     show_info_parallel_mode = dict(argstr='-Q',),
                     show_total_perms = dict(argstr='-q',),
                     tcon = dict(argstr='-t %s',mandatory=True,),
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

@skipif(no_fsl)
def test_tbss1preproc():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(),
                     img_list = dict(mandatory=True,),
                     output_type = dict(),
                     )
    instance = fsl.TBSS1Preproc()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

@skipif(no_fsl)
def test_tbss2reg():
    input_map = dict(FMRIB58FA = dict(argstr='-T',xor=('FMRIB58FA', 'target_img', 'find_target'),),
                     args = dict(argstr='%s',),
                     environ = dict(),
                     find_target = dict(argstr='-n',xor=('FMRIB58FA', 'target_img', 'find_target'),),
                     output_type = dict(),
                     target_img = dict(argstr='-t %s',xor=('FMRIB58FA', 'target_img', 'find_target'),),
                     tbss_dir = dict(mandatory=True,),
                     )
    instance = fsl.TBSS2Reg()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

@skipif(no_fsl)
def test_tbss3postreg():
    input_map = dict(FMRIB58FA = dict(argstr='-T',xor=('subject_mean', 'FMRIB58FA'),),
                     args = dict(argstr='%s',),
                     environ = dict(),
                     output_type = dict(),
                     subject_mean = dict(argstr='-S',xor=('subject_mean', 'FMRIB58FA'),),
                     tbss_dir = dict(mandatory=True,),
                     )
    instance = fsl.TBSS3Postreg()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

@skipif(no_fsl)
def test_tbss4prestats():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(),
                     output_type = dict(),
                     tbss_dir = dict(mandatory=True,),
                     threshold = dict(mandatory=True,argstr='%.3f',),
                     )
    instance = fsl.TBSS4Prestats()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

@skipif(no_fsl)
def test_vecreg():
    input_map = dict(affine_mat = dict(argstr='-t %s',),
                     args = dict(argstr='%s',),
                     environ = dict(),
                     in_file = dict(mandatory=True,argstr='-i %s',),
                     interpolation = dict(argstr='--interp=%s',),
                     mask = dict(argstr='-m %s',),
                     out_file = dict(argstr='-o %s',),
                     output_type = dict(),
                     ref_mask = dict(argstr='--refmask=%s',),
                     ref_vol = dict(mandatory=True,argstr='-r %s',),
                     rotation_mat = dict(argstr='--rotmat=%s',),
                     rotation_warp = dict(argstr='--rotwarp=%s',),
                     warp_field = dict(argstr='-w %s',),
                     )
    instance = fsl.VecReg()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value


def skip_dti_tests():
    """XXX These tests are skipped until we clean up some of this code
    """
    return True

def create_files_in_directory():
    outdir = mkdtemp()
    cwd = os.getcwd()
    os.chdir(outdir)
    filelist = ['a.nii','b.nii']
    for f in filelist:
        hdr = nb.Nifti1Header()
        shape = (3,3,3,4)
        hdr.set_data_shape(shape)
        img = np.random.random(shape)
        nb.save(nb.Nifti1Image(img,np.eye(4),hdr),
                 os.path.join(outdir,f))
    return filelist, outdir, cwd
    
def clean_directory(outdir, old_wd):
    if os.path.exists(outdir):
        rmtree(outdir)
    os.chdir(old_wd)


# test bedpostx
def test_bedpostx():
    filelist, outdir, cwd = create_files_in_directory()
    bpx = fsl.BEDPOSTX()

    # make sure command gets called
    yield assert_equal, bpx.cmd, 'bedpostx'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, bpx.run

    # .inputs based parameters setting
    bpx2 = fsl.BEDPOSTX()
    bpx2.inputs.mask = example_data('mask.nii')
    bpx2.inputs.dwi = example_data('diffusion.nii')
    bpx2.inputs.bvals = example_data('bvals')
    bpx2.inputs.bvecs = example_data('bvecs')
    bpx2.inputs.fibres = 2
    bpx2.inputs.weight = 0.3
    bpx2.inputs.burn_period = 200
    bpx2.inputs.jumps = 500
    bpx2.inputs.sampling = 20
    actualCmdline = sorted(bpx2.cmdline.split())
    cmd = 'bedpostx bedpostx -b 200 -n 2 -j 500 -s 20 -w 0.30'
    desiredCmdline = sorted(cmd.split())
    yield assert_equal, actualCmdline, desiredCmdline


 
# test eddy_correct
@skipif(no_fsl)
def test_eddy_correct():
    filelist, outdir, cwd = create_files_in_directory()
    eddy = fsl.EddyCorrect()

    # make sure command gets called
    yield assert_equal, eddy.cmd, 'eddy_correct'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, eddy.run

    # .inputs based parameters setting
    eddy.inputs.in_file = filelist[0]
    eddy.inputs.out_file = 'foo_eddc.nii'
    eddy.inputs.ref_num = 100
    yield assert_equal, eddy.cmdline, 'eddy_correct %s foo_eddc.nii 100'%filelist[0]

    # .run based parameter setting
    eddy2 = fsl.EddyCorrect(in_file=filelist[0], out_file='foo_ec.nii', ref_num=20)
    yield assert_equal, eddy2.cmdline, 'eddy_correct %s foo_ec.nii 20'%filelist[0]

    # test arguments for opt_map
    # eddy_correct class doesn't have opt_map{}
    clean_directory(outdir, cwd)


# test dtifit
@skipif(no_fsl)
def test_dtifit():
    filelist, outdir, cwd = create_files_in_directory()
    dti = fsl.DTIFit()

    # make sure command gets called
    yield assert_equal, dti.cmd, 'dtifit'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, dti.run

    # .inputs based parameters setting
    dti.inputs.dwi = filelist[0]
    dti.inputs.base_name = 'foo.dti.nii'
    dti.inputs.mask = filelist[1]
    dti.inputs.bvecs = filelist[0]
    dti.inputs.bvals = filelist[1]
    dti.inputs.min_z = 10
    dti.inputs.max_z = 50

    yield assert_equal, dti.cmdline, \
        'dtifit -k %s -o foo.dti.nii -m %s -r %s -b %s -Z 50 -z 10'%(filelist[0],
                                                                     filelist[1],
                                                                     filelist[0],
                                                                     filelist[1])

    clean_directory(outdir, cwd)


# Globals to store paths for tbss tests
tbss_dir = None
test_dir = None
def setup_tbss():
    # Setup function is called before each test.  Setup is called only
    # once for each generator function.
    global tbss_dir, tbss_files, test_dir
    test_dir = os.getcwd()
    tbss_dir = tempfile.mkdtemp()
    os.chdir(tbss_dir)
    tbss_files = ['a.nii','b.nii']
    for f in tbss_files:
        fp = open(f,'wt')
        fp.write('dummy')
        fp.close()

def teardown_tbss():
    # Teardown is called after each test to perform cleanup
    os.chdir(test_dir)
    shutil.rmtree(tbss_dir)

@skipif(skip_dti_tests)
@with_setup(setup_tbss, teardown_tbss)
def test_tbss_1_preproc():
    tbss1 = fsl.TBSS1Preproc()

    # make sure command gets called
    yield assert_equal, tbss1.cmd, 'tbss_1_preproc'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, tbss1.run

    # .inputs based parameters setting
    tbss1.inputs.img_list = tbss_files
    yield assert_equal, tbss1.cmdline, \
        'tbss_1_preproc %s %s'%(tbss_files[0],tbss_files[1])

    # test arguments for opt_map
    # Tbss_1_preproc class doesn't have opt_map{}

@skipif(skip_dti_tests)
@with_setup(setup_tbss, teardown_tbss)
def test_tbss_2_reg():
    tbss2 = fsl.TBSS2Reg()

    # make sure command gets called
    yield assert_equal, tbss2.cmd, 'tbss_2_reg'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, tbss2.run

    # .inputs based parameters setting
    tbss2.inputs.FMRIB58_FA_1mm = True
    yield assert_equal, tbss2.cmdline, 'tbss_2_reg -T'

    # .run based parameter setting
    tbss22 = fsl.TBSS2Reg(targetImage='targetImg')
    yield assert_equal, tbss22.cmdline, 'tbss_2_reg -t targetImg'

    tbss222 = fsl.TBSS2Reg(findTarget=True)
    yield assert_equal, tbss222.cmdline, 'tbss_2_reg -n'

    tbss21 = fsl.TBSS2Reg()
    results = tbss21.run(FMRIB58_FA_1mm=True, noseTest=True)
    yield assert_equal, results.runtime.cmdline, 'tbss_2_reg -T'

    # test arguments for opt_map
    opt_map = { 'FMRIB58_FA_1mm':    ('-T', True),
               'targetImage':       ('-t allimgs', 'allimgs'),
               'findTarget':        ('-n', True)}

    for name, settings in opt_map.items():
        tbss = fsl.TBSS2Reg(**{name: settings[1]})
        yield assert_equal, tbss.cmdline, tbss.cmd + ' ' + settings[0]

@skipif(skip_dti_tests)
@with_setup(setup_tbss, teardown_tbss)
def test_tbss_3_postreg():
    tbss = fsl.TBSS3Postreg()

    # make sure command gets called
    yield assert_equal, tbss.cmd, 'tbss_3_postreg'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, tbss.run

    # .inputs based parameters setting
    tbss.inputs.FMRIB58_FA = True
    yield assert_equal, tbss.cmdline, 'tbss_3_postreg -T'

    # .run based parameter setting
    tbss2 = fsl.TBSS3Postreg(subject_means=True)
    yield assert_equal, tbss2.cmdline, 'tbss_3_postreg -S'

    tbss3 = fsl.TBSS3Postreg()
    results = tbss3.run(FMRIB58_FA=True, noseTest=True)
    yield assert_equal, results.runtime.cmdline, 'tbss_3_postreg -T'

    # test arguments for opt_map
    opt_map = { 'subject_means':     ('-S', True),
               'FMRIB58_FA':        ('-T', True)}

    for name, settings in opt_map.items():
        tbss3 = fsl.TBSS3Postreg(**{name: settings[1]})
        yield assert_equal, tbss3.cmdline, tbss3.cmd + ' ' + settings[0]

@skipif(skip_dti_tests)
@with_setup(setup_tbss, teardown_tbss)
def test_tbss_4_prestats():
    tbss = fsl.TBSS4Prestats()

    # make sure command gets called
    yield assert_equal, tbss.cmd, 'tbss_4_prestats'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, tbss.run

    # .inputs based parameters setting
    tbss.inputs.threshold = 0.3
    yield assert_equal, tbss.cmdline, 'tbss_4_prestats 0.3'

    tbss2 = fsl.TBSS4Prestats(threshold=0.4)
    yield assert_equal, tbss2.cmdline, 'tbss_4_prestats 0.4'

    tbss3 = fsl.TBSS4Prestats()
    results = tbss3.run(threshold=0.2, noseTest=True)
    yield assert_equal, results.runtime.cmdline, 'tbss_4_prestats 0.2'

    # test arguments for opt_map
    # TBSS4Prestats doesn't have an opt_map{}

@skipif(skip_dti_tests)
def test_randomise():

    rand = fsl.Randomise()

    # make sure command gets called
    yield assert_equal, rand.cmd, 'randomise'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, rand.run

    # .inputs based parameters setting
    rand.inputs.input_4D = 'infile.nii'
    rand.inputs.output_rootname = 'outfile'
    rand.inputs.design_matrix = 'design.mat'
    rand.inputs.t_contrast = 'infile.con'

    actualCmdline = sorted(rand.cmdline.split())
    cmd = 'randomise -i infile.nii -o outfile -d design.mat -t infile.con'
    desiredCmdline = sorted(cmd.split())
    yield assert_equal, actualCmdline, desiredCmdline

    # .run based parameter setting
    rand2 = fsl.Randomise(input_4D='infile2',
                          output_rootname='outfile2',
                          f_contrast='infile.f',
                          one_sample_gmean=True,
                          int_seed=4)

    actualCmdline = sorted(rand2.cmdline.split())
    cmd = 'randomise -i infile2 -o outfile2 -1 -f infile.f --seed 4'
    desiredCmdline = sorted(cmd.split())
    yield assert_equal, actualCmdline, desiredCmdline

    rand3 = fsl.Randomise()
    results = rand3.run(input_4D='infile3',
                      output_rootname='outfile3')
    yield assert_equal, results.runtime.cmdline, \
          'randomise -i infile3 -o outfile3'

    # test arguments for opt_map
    opt_map = {'demean_data':                        ('-D', True),
              'one_sample_gmean':                   ('-1', True),
              'mask_image':                         ('-m inp_mask', 'inp_mask'),
              'design_matrix':                      ('-d design.mat',
                                                     'design.mat'),
              't_contrast':                         ('-t input.con',
                                                     'input.con'),
              'f_contrast':                         ('-f input.fts',
                                                     'input.fts'),
              'xchange_block_labels':               ('-e design.grp',
                                                     'design.grp'),
              'print_unique_perm':                  ('-q', True),
              'print_info_parallelMode':            ('-Q', True),
              'num_permutations':                   ('-n 10', 10),
              'vox_pvalus':                         ('-x', True),
              'fstats_only':                        ('--fonly', True),
              'thresh_free_cluster':                ('-T', True),
              'thresh_free_cluster_2Dopt':          ('--T2', True),
              'cluster_thresholding':               ('-c 0.20', 0.20),
              'cluster_mass_thresholding':          ('-C 0.40', 0.40),
              'fcluster_thresholding':              ('-F 0.10', 0.10),
              'fcluster_mass_thresholding':         ('-S 0.30', 0.30),
              'variance_smoothing':                 ('-v 0.20', 0.20),
              'diagnostics_off':                    ('--quiet', True),
              'output_raw':                         ('-R', True),
              'output_perm_vect':                   ('-P', True),
              'int_seed':                           ('--seed 20', 20),
              'TFCE_height_param':                  ('--tfce_H 0.11', 0.11),
              'TFCE_extent_param':                  ('--tfce_E 0.50', 0.50),
              'TFCE_connectivity':                  ('--tfce_C 0.30', 0.30),
              'list_num_voxel_EVs_pos':             ('--vxl 1,2,3,4',
                                                     '1,2,3,4'),
              'list_img_voxel_EVs':                 ('--vxf 6,7,8,9,3',
                                                     '6,7,8,9,3')}

    for name, settings in opt_map.items():
        rand4 = fsl.Randomise(input_4D='infile', output_rootname='root', 
                              **{name: settings[1]})
        yield assert_equal, rand4.cmdline, rand4.cmd + ' -i infile -o root ' \
            + settings[0]

@skipif(skip_dti_tests)
def test_Randomise_parallel():
    rand = fsl.Randomise_parallel()

    # make sure command gets called
    yield assert_equal, rand.cmd, 'randomise_parallel'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, rand.run

    # .inputs based parameters setting
    rand.inputs.input_4D = 'infile.nii'
    rand.inputs.output_rootname = 'outfile'
    rand.inputs.design_matrix = 'design.mat'
    rand.inputs.t_contrast = 'infile.con'

    actualCmdline = sorted(rand.cmdline.split())
    cmd = 'randomise_parallel -i infile.nii -o outfile -d design.mat -t infile.con'
    desiredCmdline = sorted(cmd.split())
    yield assert_equal, actualCmdline, desiredCmdline

    # .run based parameter setting
    rand2 = fsl.Randomise_parallel(input_4D='infile2',
                          output_rootname='outfile2',
                          f_contrast='infile.f',
                          one_sample_gmean=True,
                          int_seed=4)

    actualCmdline = sorted(rand2.cmdline.split())
    cmd = 'randomise_parallel -i infile2 -o outfile2 -1 -f infile.f --seed 4'
    desiredCmdline = sorted(cmd.split())
    yield assert_equal, actualCmdline, desiredCmdline

    rand3 = fsl.Randomise_parallel()
    results = rand3.run(input_4D='infile3',
                      output_rootname='outfile3')
    yield assert_equal, results.runtime.cmdline, \
          'randomise_parallel -i infile3 -o outfile3'

    # test arguments for opt_map
    opt_map = {'demean_data':                        ('-D', True),
              'one_sample_gmean':                   ('-1', True),
              'mask_image':                         ('-m inp_mask', 'inp_mask'),
              'design_matrix':                      ('-d design.mat',
                                                     'design.mat'),
              't_contrast':                         ('-t input.con',
                                                     'input.con'),
              'f_contrast':                         ('-f input.fts',
                                                     'input.fts'),
              'xchange_block_labels':               ('-e design.grp',
                                                     'design.grp'),
              'print_unique_perm':                  ('-q', True),
              'print_info_parallelMode':            ('-Q', True),
              'num_permutations':                   ('-n 10', 10),
              'vox_pvalus':                         ('-x', True),
              'fstats_only':                        ('--fonly', True),
              'thresh_free_cluster':                ('-T', True),
              'thresh_free_cluster_2Dopt':          ('--T2', True),
              'cluster_thresholding':               ('-c 0.20', 0.20),
              'cluster_mass_thresholding':          ('-C 0.40', 0.40),
              'fcluster_thresholding':              ('-F 0.10', 0.10),
              'fcluster_mass_thresholding':         ('-S 0.30', 0.30),
              'variance_smoothing':                 ('-v 0.20', 0.20),
              'diagnostics_off':                    ('--quiet', True),
              'output_raw':                         ('-R', True),
              'output_perm_vect':                   ('-P', True),
              'int_seed':                           ('--seed 20', 20),
              'TFCE_height_param':                  ('--tfce_H 0.11', 0.11),
              'TFCE_extent_param':                  ('--tfce_E 0.50', 0.50),
              'TFCE_connectivity':                  ('--tfce_C 0.30', 0.30),
              'list_num_voxel_EVs_pos':             ('--vxl ' \
                                                         + repr([1, 2, 3, 4]), 
                                                     repr([1, 2, 3, 4])),
              'list_img_voxel_EVs':               ('--vxf ' \
                                                       + repr([6, 7, 8, 9, 3]), 
                                                     repr([6, 7, 8, 9, 3]))}

    for name, settings in opt_map.items():
        rand4 = fsl.Randomise_parallel(input_4D='infile', 
                                       output_rootname='root', 
                                       **{name: settings[1]})
        yield assert_equal, rand4.cmdline, rand4.cmd + ' -i infile -o root ' \
            + settings[0]


@skipif(skip_dti_tests)
def test_Probtrackx():
    pass
    # make sure command gets called


    # test raising error with mandatory args absent


    # .inputs based parameters setting


    # .run based parameter setting


    # test generation of outfile


    # test arguments for opt_map



# test proj_thresh
@skipif(skip_dti_tests)
def test_Proj_thresh():
    proj = fsl.ProjThresh()

    # make sure command gets called
    yield assert_equal, proj.cmd, 'proj_thresh'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, proj.run

    # .inputs based parameters setting
    proj.inputs.volumes = ['vol1', 'vol2', 'vol3']
    proj.inputs.threshold = 3
    yield assert_equal, proj.cmdline, 'proj_thresh vol1 vol2 vol3 3'

    proj2 = fsl.ProjThresh(threshold=10, volumes=['vola', 'volb'])
    yield assert_equal, proj2.cmdline, 'proj_thresh vola volb 10'

    # .run based parameters setting
    proj3 = fsl.ProjThresh()
    results = proj3.run(volumes=['inp1', 'inp3', 'inp2'], threshold=2)
    yield assert_equal, results.runtime.cmdline, 'proj_thresh inp1 inp3 inp2 2'
    yield assert_not_equal, results.runtime.returncode, 0
    yield assert_equal, isinstance(results.interface.inputs.volumes, list), True
    yield assert_equal, results.interface.inputs.threshold, 2

    # test arguments for opt_map
    # Proj_thresh doesn't have an opt_map{}    


# test vec_reg
@skipif(skip_dti_tests)
def test_Vec_reg():

    vrg = fsl.VecReg()

    # make sure command gets called
    yield assert_equal, vrg.cmd, 'vecreg'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, vrg.run

    # .inputs based parameters setting
    vrg.inputs.infile = 'infile'
    vrg.inputs.outfile = 'outfile'
    vrg.inputs.refVolName = 'MNI152'
    vrg.inputs.affineTmat = 'tmat.mat'
    yield assert_equal, vrg.cmdline, \
        'vecreg -i infile -o outfile -r MNI152 -t tmat.mat'

    # .run based parameter setting
    vrg2 = fsl.VecReg(infile='infile2',
                       outfile='outfile2',
                       refVolName='MNI152',
                       affineTmat='tmat2.mat',
                       brainMask='nodif_brain_mask')

    actualCmdline = sorted(vrg2.cmdline.split())
    cmd = 'vecreg -i infile2 -o outfile2 -r MNI152 -t tmat2.mat -m nodif_brain_mask'
    desiredCmdline = sorted(cmd.split())
    yield assert_equal, actualCmdline, desiredCmdline

    vrg3 = fsl.VecReg()
    results = vrg3.run(infile='infile3',
                     outfile='outfile3',
                     refVolName='MNI152',
                     affineTmat='tmat3.mat',)

    yield assert_equal, results.runtime.cmdline, \
          'vecreg -i infile3 -o outfile3 -r MNI152 -t tmat3.mat'
    yield assert_not_equal, results.runtime.returncode, 0
    yield assert_equal, results.interface.inputs.infile, 'infile3'
    yield assert_equal, results.interface.inputs.outfile, 'outfile3'
    yield assert_equal, results.interface.inputs.refVolName, 'MNI152'
    yield assert_equal, results.interface.inputs.affineTmat, 'tmat3.mat'

    # test arguments for opt_map
    opt_map = { 'verbose':           ('-v', True),
               'helpDoc':           ('-h', True),
               'tensor':            ('--tensor', True),
               'affineTmat':        ('-t Tmat', 'Tmat'),
               'warpFile':          ('-w wrpFile', 'wrpFile'),
               'interpolation':     ('--interp sinc', 'sinc'),
               'brainMask':         ('-m mask', 'mask')}

    for name, settings in opt_map.items():
        vrg4 = fsl.VecReg(infile='infile', outfile='outfile', 
                          refVolName='MNI152', **{name: settings[1]})
        yield assert_equal, vrg4.cmdline, vrg4.cmd + \
            ' -i infile -o outfile -r MNI152 ' + settings[0]


# test find_the_biggest
@skipif(skip_dti_tests)
def test_Find_the_biggest():
    fbg = fsl.FindTheBiggest()

    # make sure command gets called
    yield assert_equal, fbg.cmd, 'find_the_biggest'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, fbg.run

    # .inputs based parameters setting
    fbg.inputs.infiles = 'seed*'
    fbg.inputs.outfile = 'fbgfile'
    yield assert_equal, fbg.cmdline, 'find_the_biggest seed* fbgfile'

    fbg2 = fsl.FindTheBiggest(infiles='seed2*', outfile='fbgfile2')
    yield assert_equal, fbg2.cmdline, 'find_the_biggest seed2* fbgfile2'

    # .run based parameters setting
    fbg3 = fsl.FindTheBiggest()
    results = fbg3.run(infiles='seed3', outfile='out3')
    yield assert_equal, results.runtime.cmdline, 'find_the_biggest seed3 out3'

    # test arguments for opt_map
    # Find_the_biggest doesn't have an opt_map{}
