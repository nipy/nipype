import os
import tempfile
import shutil
from nose import with_setup

from nipype.testing import assert_equal, assert_not_equal, assert_raises
import nipype.interfaces.fsl.dti as fsl

# nosetests --with-doctest path_to/test_fsl.py

# test bedpostx
def test_bedpostx():
    bpx = fsl.Bedpostx()

    # make sure command gets called
    yield assert_equal, bpx.cmd, 'bedpostx'

    # test raising error with mandatory args absent
    yield assert_raises, AttributeError, bpx.run

    # .inputs based parameters setting
    bpx2 = fsl.Bedpostx()
    bpx2.inputs.directory = 'inputDir'
    bpx2.inputs.fibres = 2
    bpx2.inputs.weight = 0.3
    bpx2.inputs.burn_period = 200
    bpx2.inputs.jumps = 500
    bpx2.inputs.sampling = 20
    actualCmdline = sorted(bpx2.cmdline.split())
    cmd = 'bedpostx inputDir -w 0.30 -n 2 -j 500 -b 200 -s 20'
    desiredCmdline = sorted(cmd.split())
    yield assert_equal, actualCmdline, desiredCmdline


    # .run based parameter setting
    bpx3 = fsl.Bedpostx(fibres=1, directory='inputDir')
    yield assert_equal, bpx3.cmdline, 'bedpostx inputDir -n 1'

    results = bpx3.run(fibres=1, directory='inputDir', noseTest=True)
    yield assert_not_equal, results.runtime.returncode, 0
    yield assert_equal, results.interface.inputs.fibres, 1
    yield assert_equal, results.interface.inputs.directory, 'inputDir'
    yield assert_equal, results.runtime.cmdline, 'bedpostx inputDir -n 1'

    # test arguments for opt_map
    opt_map = {
                'fibres':               ('-n 1', 1),
                'weight':               ('-w 1.00', 1.0),
                'burn_period':          ('-b 1000', 1000),
                'jumps':                ('-j 1250', 1250),
                'sampling':             ('-s 25', 25)}

    for name, settings in opt_map.items():
        bpx4 = fsl.Bedpostx(directory='inputDir', **{name: settings[1]})
        yield assert_equal, bpx4.cmdline, bpx4.cmd + ' inputDir ' + settings[0]


# test eddy_correct
def test_eddy_correct():
    eddy = fsl.EddyCorrect()

    # make sure command gets called
    yield assert_equal, eddy.cmd, 'eddy_correct'

    # test raising error with mandatory args absent
    yield assert_raises, AttributeError, eddy.run

    # .inputs based parameters setting
    eddy.inputs.infile = 'foo.nii'
    eddy.inputs.outfile = 'foo_eddc.nii'
    eddy.inputs.reference_vol = 100
    yield assert_equal, eddy.cmdline, 'eddy_correct foo.nii foo_eddc.nii 100'

    # .run based parameter setting
    eddy2 = fsl.EddyCorrect(infile='foo', outfile='foo_eddc', reference_vol=20)
    yield assert_equal, eddy2.cmdline, 'eddy_correct foo foo_eddc 20'

    eddy3 = fsl.EddyCorrect()
    results = eddy3.run(infile='foo', outfile='foo_eddc', reference_vol=10)
    yield assert_equal, results.interface.inputs.infile, 'foo'
    yield assert_equal, results.interface.inputs.outfile, 'foo_eddc'
    yield assert_equal, results.runtime.cmdline, 'eddy_correct foo foo_eddc 10'

    # test arguments for opt_map
    # eddy_correct class doesn't have opt_map{}


# test dtifit  
def test_dtifit():
    dti = fsl.Dtifit()

    # make sure command gets called
    yield assert_equal, dti.cmd, 'dtifit'

    # test raising error with mandatory args absent
    yield assert_raises, AttributeError, dti.run

    # .inputs based parameters setting
    dti.inputs.data = 'foo.nii'
    dti.inputs.basename = 'foo.dti.nii'
    dti.inputs.bet_binary_mask = 'nodif_brain_mask'
    dti.inputs.min_z = 10
    dti.inputs.max_z = 50

    actualCmdline = sorted(dti.cmdline.split())
    cmd = 'dtifit -k foo.nii -o foo.dti.nii -m nodif_brain_mask -z 10 -Z 50'
    desiredCmdline = sorted(cmd.split())
    yield assert_equal, actualCmdline, desiredCmdline

    # .run based parameter setting
    dti2 = fsl.Dtifit(data='foo2.nii')
    yield assert_equal, dti2.cmdline, 'dtifit -k foo2.nii'

    dti3 = fsl.Dtifit()
    results = dti3.run(data='foo3.nii', noseTest=True)
    yield assert_not_equal, results.runtime.returncode, 0
    yield assert_equal, results.interface.inputs.data, 'foo3.nii'
    yield assert_equal, results.runtime.cmdline, 'dtifit -k foo3.nii'

    # test arguments for opt_map
    opt_map = {
                'data':                     ('-k subj1', 'subj1'),
                'basename':                 ('-o subj1', 'subj1'),
                'bet_binary_mask':          ('-m nodif_brain_mask', 'nodif_brain_mask'),
                'b_vector_file':            ('-r bvecs', 'bvecs'),
                'b_value_file':             ('-b bvals', 'bvals'),
                'min_z':                    ('-z 10', 10),
                'max_z':                    ('-Z 20', 20),
                'min_y':                    ('-y 10', 10),
                'max_y':                    ('-Y 30', 30),
                'min_x':                    ('-x 5', 5),
                'max_x':                    ('-X 50', 50),
                'verbose':                  ('-V', True),
                'save_tensor':              ('--save_tensor', True),
                'sum_squared_errors':       ('--sse', True),
                'inp_confound_reg':         ('--cni', True),
                'small_brain_area':         ('--littlebit', True)}

    for name, settings in opt_map.items():
        dti4 = fsl.Dtifit(**{name: settings[1]})
        yield assert_equal, dti4.cmdline, dti4.cmd + ' ' + settings[0]


# Globals to store paths for tbss tests
tbss_dir = None
test_dir = None
def setup_tbss():
    # Setup function is called before each test.  Setup is called only
    # once for each generator function.
    global tbss_dir, test_dir
    test_dir = os.getcwd()
    tbss_dir = tempfile.mkdtemp()
    os.chdir(tbss_dir)

def teardown_tbss():
    # Teardown is called after each test to perform cleanup
    os.chdir(test_dir)
    shutil.rmtree(tbss_dir)

@with_setup(setup_tbss, teardown_tbss)
def test_tbss_1_preproc():
    tbss1 = fsl.Tbss1preproc()

    # make sure command gets called
    yield assert_equal, tbss1.cmd, 'tbss_1_preproc'

    # test raising error with mandatory args absent
    yield assert_raises, AttributeError, tbss1.run

    # .inputs based parameters setting
    tbss1.inputs.infiles = 'foo.nii  f002.nii  f003.nii'
    yield assert_equal, tbss1.cmdline, \
        'tbss_1_preproc foo.nii  f002.nii  f003.nii'

    tbss = fsl.Tbss1preproc()
    results = tbss.run(infiles='*.nii.gz', noseTest=True)
    yield assert_equal, results.interface.inputs.infiles, '*.nii.gz'
    yield assert_equal, results.runtime.cmdline, 'tbss_1_preproc *.nii.gz'

    # test arguments for opt_map
    # Tbss_1_preproc class doesn't have opt_map{}

@with_setup(setup_tbss, teardown_tbss)
def test_tbss_2_reg():
    tbss2 = fsl.Tbss2reg()

    # make sure command gets called
    yield assert_equal, tbss2.cmd, 'tbss_2_reg'

    # test raising error with mandatory args absent
    yield assert_raises, AttributeError, tbss2.run

    # .inputs based parameters setting
    tbss2.inputs.FMRIB58_FA_1mm = True
    yield assert_equal, tbss2.cmdline, 'tbss_2_reg -T'

    # .run based parameter setting
    tbss22 = fsl.Tbss2reg(targetImage='targetImg')
    yield assert_equal, tbss22.cmdline, 'tbss_2_reg -t targetImg'

    tbss222 = fsl.Tbss2reg(findTarget=True)
    yield assert_equal, tbss222.cmdline, 'tbss_2_reg -n'

    tbss21 = fsl.Tbss2reg()
    results = tbss21.run(FMRIB58_FA_1mm=True, noseTest=True)
    yield assert_equal, results.runtime.cmdline, 'tbss_2_reg -T'

    # test arguments for opt_map
    opt_map = { 'FMRIB58_FA_1mm':    ('-T', True),
               'targetImage':       ('-t allimgs', 'allimgs'),
               'findTarget':        ('-n', True)}

    for name, settings in opt_map.items():
        tbss = fsl.Tbss2reg(**{name: settings[1]})
        yield assert_equal, tbss.cmdline, tbss.cmd + ' ' + settings[0]

@with_setup(setup_tbss, teardown_tbss)
def test_tbss_3_postreg():
    tbss = fsl.Tbss3postreg()

    # make sure command gets called
    yield assert_equal, tbss.cmd, 'tbss_3_postreg'

    # test raising error with mandatory args absent
    yield assert_raises, AttributeError, tbss.run

    # .inputs based parameters setting
    tbss.inputs.FMRIB58_FA = True
    yield assert_equal, tbss.cmdline, 'tbss_3_postreg -T'

    # .run based parameter setting
    tbss2 = fsl.Tbss3postreg(subject_means=True)
    yield assert_equal, tbss2.cmdline, 'tbss_3_postreg -S'

    tbss3 = fsl.Tbss3postreg()
    results = tbss3.run(FMRIB58_FA=True, noseTest=True)
    yield assert_equal, results.runtime.cmdline, 'tbss_3_postreg -T'

    # test arguments for opt_map
    opt_map = { 'subject_means':     ('-S', True),
               'FMRIB58_FA':        ('-T', True)}

    for name, settings in opt_map.items():
        tbss3 = fsl.Tbss3postreg(**{name: settings[1]})
        yield assert_equal, tbss3.cmdline, tbss3.cmd + ' ' + settings[0]

@with_setup(setup_tbss, teardown_tbss)
def test_tbss_4_prestats():
    tbss = fsl.Tbss4prestats()

    # make sure command gets called
    yield assert_equal, tbss.cmd, 'tbss_4_prestats'

    # test raising error with mandatory args absent
    yield assert_raises, AttributeError, tbss.run

    # .inputs based parameters setting
    tbss.inputs.threshold = 0.3
    yield assert_equal, tbss.cmdline, 'tbss_4_prestats 0.3'

    tbss2 = fsl.Tbss4prestats(threshold=0.4)
    yield assert_equal, tbss2.cmdline, 'tbss_4_prestats 0.4'

    tbss3 = fsl.Tbss4prestats()
    results = tbss3.run(threshold=0.2, noseTest=True)
    yield assert_equal, results.runtime.cmdline, 'tbss_4_prestats 0.2'

    # test arguments for opt_map
    # Tbss4prestats doesn't have an opt_map{}

def test_randomise():

    rand = fsl.Randomise()

    # make sure command gets called
    yield assert_equal, rand.cmd, 'randomise'

    # test raising error with mandatory args absent
    yield assert_raises, AttributeError, rand.run

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

def test_Randomise_parallel():
    rand = fsl.Randomise_parallel()

    # make sure command gets called
    yield assert_equal, rand.cmd, 'randomise_parallel'

    # test raising error with mandatory args absent
    yield assert_raises, AttributeError, rand.run

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


def test_Probtrackx():
    pass
    # make sure command gets called


    # test raising error with mandatory args absent


    # .inputs based parameters setting


    # .run based parameter setting


    # test generation of outfile


    # test arguments for opt_map



# test proj_thresh
def test_Proj_thresh():
    proj = fsl.ProjThresh()

    # make sure command gets called
    yield assert_equal, proj.cmd, 'proj_thresh'

    # test raising error with mandatory args absent
    yield assert_raises, AttributeError, proj.run

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
def test_Vec_reg():

    vrg = fsl.Vecreg()

    # make sure command gets called
    yield assert_equal, vrg.cmd, 'vecreg'

    # test raising error with mandatory args absent
    yield assert_raises, AttributeError, vrg.run

    # .inputs based parameters setting
    vrg.inputs.infile = 'infile'
    vrg.inputs.outfile = 'outfile'
    vrg.inputs.refVolName = 'MNI152'
    vrg.inputs.affineTmat = 'tmat.mat'
    yield assert_equal, vrg.cmdline, \
        'vecreg -i infile -o outfile -r MNI152 -t tmat.mat'

    # .run based parameter setting
    vrg2 = fsl.Vecreg(infile='infile2',
                       outfile='outfile2',
                       refVolName='MNI152',
                       affineTmat='tmat2.mat',
                       brainMask='nodif_brain_mask')

    actualCmdline = sorted(vrg2.cmdline.split())
    cmd = 'vecreg -i infile2 -o outfile2 -r MNI152 -t tmat2.mat -m nodif_brain_mask'
    desiredCmdline = sorted(cmd.split())
    yield assert_equal, actualCmdline, desiredCmdline

    vrg3 = fsl.Vecreg()
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
        vrg4 = fsl.Vecreg(infile='infile', outfile='outfile', 
                          refVolName='MNI152', **{name: settings[1]})
        yield assert_equal, vrg4.cmdline, vrg4.cmd + \
            ' -i infile -o outfile -r MNI152 ' + settings[0]


# test find_the_biggest
def test_Find_the_biggest():
    fbg = fsl.FindTheBiggest()

    # make sure command gets called
    yield assert_equal, fbg.cmd, 'find_the_biggest'

    # test raising error with mandatory args absent
    yield assert_raises, AttributeError, fbg.run

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
