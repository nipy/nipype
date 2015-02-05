from nose import with_setup
from nipype.testing import assert_equal, assert_raises
from nipype.interfaces.base import InputMultiPath
from traits.trait_errors import TraitError
from nipype.interfaces.ants import JointFusion

def setup():
    at = JointFusion()

# @with_setup(setup)
def test_JointFusion_dimension():
    at = JointFusion()
    set_dimension = lambda d: setattr(at.inputs, 'dimension', int(d))
    for d in range(2, 5):
        set_dimension(d)
        yield assert_equal, at.inputs.dimension, int(d)
    for d in [0, 1, 6, 7]:
        yield assert_raises, TraitError, set_dimension, d

def test_JointFusion_modalities():
    at = JointFusion()
    set_modalities = lambda m: setattr(at.inputs, 'modalities', int(m))
    for m in range(1, 5):
        set_modalities(m)
        yield assert_equal, at.inputs.modalities, int(m)

def test_JointFusion_method():
    at = JointFusion()
    set_method = lambda a, b: setattr(at.inputs, 'method', 'Joint[%.1f,%d]'.format(a, b))
    for a in range(10):
        _a = a / 10.0
        for b in range(10):
            set_method(_a, b)
            # set directly
            yield assert_equal, at.inputs.method, 'Joint[%.1f,%d]'.format(_a, b)
            aprime = _a + 0.1
            bprime = b + 1
            at.inputs.alpha = aprime
            at.inputs.beta = bprime
            # set with alpha/beta
            yield assert_equal, at.inputs.method, 'Joint[%.1f,%d]'.format(aprime, bprime)

# def test_JointFusion_radius():
#     at = JointFusion()
#     set_radius = lambda attr,x,y,z: setattr(at.inputs, attr, [x, y, z])
#     for attr in ['patch_radius', 'search_radius']:
#         for x in range(5):
#             set_radius(attr, x, x + 1, x**x)
#             yield assert_equal, getattr(at.inputs, attr), '{0}x{1}x{2}'.format(x, x + 1, x**x)

def test_JointFusion_cmd():
    at = JointFusion()
    at.inputs.dimension = 3
    at.inputs.modalities = 1
    at.inputs.method = 'Joint[0.1,2]'
    at.inputs.output_label_image ='fusion_labelimage_output.nii'
    at.inputs.warped_intensity_images = ['nipype/testing/data/im1.nii',
                                         'nipype/testing/data/im2.nii']
    at.inputs.warped_label_images = ['nipype/testing/data/segmentation0.nii.gz',
                                     'nipype/testing/data/segmentation1.nii.gz']
    at.inputs.target_image = 'nipype/testing/data/T1.nii'
    at.inputs.patch_radius = [3,2,1]
    at.inputs.search_radius = [1,2,3]
    yield assert_equal, at.cmdline, 'jointfusion 3 1' + \
      ' -m Joint[0.1,2]' + \
      ' -rp 3x2x1' + \
      ' -rs 1x2x3' + \
      ' -tg nipype/testing/data/T1.nii' + \
      ' -g nipype/testing/data/im1.nii' + \
      ' -g nipype/testing/data/im2.nii' + \
      ' -l nipype/testing/data/segmentation0.nii.gz' + \
      ' -l nipype/testing/data/segmentation1.nii.gz' + \
      ' fusion_labelimage_output.nii',
    "Command line generation failure", True
    yield assert_raises, AssertionError, at._format_arg, 'warped_intensity_images', InputMultiPath, ['nipype/testing/data/im1.nii', 'nipype/testing/data/im2.nii', 'nipype/testing/data/im3.nii']

def test_JointFusion_method_inputs():
    at = JointFusion()
    at.inputs.dimension = 3
    at.inputs.modalities = 1
    at.inputs.output_label_image ='fusion_labelimage_output.nii'
    at.inputs.warped_intensity_images = ['nipype/testing/data/im1.nii',
                                         'nipype/testing/data/im2.nii']
    at.inputs.warped_label_images = ['nipype/testing/data/segmentation0.nii.gz',
                                     'nipype/testing/data/segmentation1.nii.gz']
    at.inputs.target_image = 'nipype/testing/data/T1.nii'
    at.inputs.patch_radius = [3,2,1]
    at.inputs.search_radius = [1,2,3]
    at.inputs.method = 'Joint[0.1,2]'
    yield assert_equal, at.cmdline, 'jointfusion 3 1' + \
      ' -m Joint[0.1,2]' + \
      ' -rp 3x2x1' + \
      ' -rs 1x2x3' + \
      ' -tg nipype/testing/data/T1.nii' + \
      ' -g nipype/testing/data/im1.nii' + \
      ' -g nipype/testing/data/im2.nii' + \
      ' -l nipype/testing/data/segmentation0.nii.gz' + \
      ' -l nipype/testing/data/segmentation1.nii.gz' + \
      ' fusion_labelimage_output.nii',
    "Command line generation failure", True
    at.inputs.method = 'Joint'
    at.inputs.alpha = 0.5
    at.inputs.beta = 1
    yield assert_equal, at.cmdline, 'jointfusion 3 1' + \
      ' -m Joint[0.5,1]' + \
      ' -rp 3x2x1' + \
      ' -rs 1x2x3' + \
      ' -tg nipype/testing/data/T1.nii' + \
      ' -g nipype/testing/data/im1.nii' + \
      ' -g nipype/testing/data/im2.nii' + \
      ' -l nipype/testing/data/segmentation0.nii.gz' + \
      ' -l nipype/testing/data/segmentation1.nii.gz' + \
      ' fusion_labelimage_output.nii',
    "Command line generation failure", True
