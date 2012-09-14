from nipype.interfaces.ants import *

baseDir = '/hjohnson/HDNI/20120828_ANTS_NIPYPE_TESTING'

n4 = N4BiasFieldCorrection()
n4.inputs.dimension = 3
n4.inputs.input_image = baseDir + '/inputData/t1_average_BRAINSABC.nii.gz'
n4.inputs.bspline_fitting_distance = 300
n4.inputs.shrink_factor = 3
n4.inputs.n_iterations = [50,50,30,20]
n4.inputs.convergence_threshold = 1e-6


print n4.cmdline
print "N4BiasFieldCorrection --image-dimension 3 --input-image SUBJ_A_small_T1.nii.gz --output corrected.nii.gz --bsline-fitting [300] --shrink-factor 3 --convergence [50x50x30x20,1d-6]"

#res = n4.run()
#print res.outputs
