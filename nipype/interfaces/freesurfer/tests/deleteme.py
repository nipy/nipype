# from nipype import config, logging
# config.enable_debug_mode()
# logging.update_logging(config)

from model import MS_LDA
home = '/Volumes/scratch/welchdm/repos/nipype/nipype/interfaces/freesurfer/tests'
test = MS_LDA()
test.inputs.images =["/paulsen/MRx/FMRI_HD_024/0137/80457/10_AUTO.NN3Tv20110419/80457_AVG_T1.nii.gz",
                     "/paulsen/MRx/FMRI_HD_024/0137/80457/10_AUTO.NN3Tv20110419/80457_AVG_T2.nii.gz"]
test.inputs.lda_labels = [2, 3]
test.inputs.label_file = "/paulsen/MRx/FMRI_HD_024/0137/80457/10_AUTO.NN3Tv20110419/BSITKBRAINSABC/0137_80457_T1-30_2_ACPC_labels_BRAINSABC.nii.gz"
#test.inputs.mask_file = "{0}/20120430_1348_txfmv2fv_affine.mat".format(home)
test.inputs.weight_file = "{0}/weights1.txt".format(home)
#test.inputs.shift = 5
test.inputs.output_synth = "{0}/synth1.mgz".format(home)
test.inputs.conform = True
test.inputs.use_weights = True

print test.cmdline
result = test.run()
print result.outputs

# target = "mri_ms_LDA \
# -lda 2 3 \
# -weight deleteme.txt \
# -synth {0}/synth.mgz \
# -label {0}/20120430_1348_txfmv2fv_affine.mat \
# -mask {0}/20120430_1348_txfmv2fv_affine.mat \
# -shift 5 \
# -conform \
# -W \
# {0}/SUBJ_B_T1_resampled.nii.gz \
# {0}/SUBJ_A_T1_resampled.nii.gz ".format(home)

# print test.cmdline
# print '++++++++++++++++'
# print target

# assert test.cmdline.strip() == target.strip()
