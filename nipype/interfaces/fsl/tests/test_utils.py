
from nipype.testing import assert_equal, assert_not_equal, assert_raises
import nipype.interfaces.fsl.utils as fsl

def test_fslroi():
    roi = fsl.ExtractROI()

    # make sure command gets called
    yield assert_equal, roi.cmd, 'fslroi'

    # test raising error with mandatory args absent
    yield assert_raises, AttributeError, roi.run

    # .inputs based parameters setting
    roi.inputs.infile = 'foo.nii'
    roi.inputs.outfile = 'foo_roi.nii'
    roi.inputs.tmin = 10
    roi.inputs.tsize = 20
    yield assert_equal, roi.cmdline, 'fslroi foo.nii foo_roi.nii 10 20'

    # .run based parameter setting
    roi2 = fsl.ExtractROI(infile='foo2',
                      outfile='foo2_roi',
                      tmin=20, tsize=40,
                      xmin=3, xsize=30,
                      ymin=40, ysize=10,
                      zmin=5, zsize=20)
    yield assert_equal, roi2.cmdline, \
          'fslroi foo2 foo2_roi 3 30 40 10 5 20 20 40'

    roi3 = fsl.ExtractROI()
    results = roi3.run(infile='foo3',
                     outfile='foo3_roi',
                     xmin=3, xsize=30,
                     ymin=40, ysize=10,
                     zmin=5, zsize=20)

    roi3_dim = [ roi3.inputs.xmin, roi3.inputs.xsize, roi3.inputs.ymin,
                 roi3.inputs.ysize,
                 roi3.inputs.zmin, roi3.inputs.zsize, roi3.inputs.tmin,
                 roi3.inputs.tsize]
    desired_dim = [ 3, 30, 40, 10, 5, 20, None, None ]
    yield assert_equal, roi3_dim, desired_dim

    yield assert_not_equal, results.runtime.returncode, 0
    yield assert_equal, results.interface.inputs.infile, 'foo3'
    yield assert_equal, results.interface.inputs.outfile, 'foo3_roi'
    yield assert_equal, results.runtime.cmdline, \
        'fslroi foo3 foo3_roi 3 30 40 10 5 20'

    # test arguments for opt_map
    # Fslroi class doesn't have a filled opt_map{}


# test fslmath 
def test_fslmaths():
    math = fsl.ImageMaths()

    # make sure command gets called
    yield assert_equal, math.cmd, 'fslmaths'

    # test raising error with mandatory args absent
    yield assert_raises, AttributeError, math.run

    # .inputs based parameters setting
    math.inputs.infile = 'foo.nii'
    math.inputs.optstring = '-add 2.5 -mul input_volume2'
    math.inputs.outfile = 'foo_math.nii'
    yield assert_equal, math.cmdline, \
        'fslmaths foo.nii -add 2.5 -mul input_volume2 foo_math.nii'

    # .run based parameter setting
    math2 = fsl.ImageMaths(infile='foo2', optstring='-add 2.5',
                           outfile='foo2_math')
    yield assert_equal, math2.cmdline, 'fslmaths foo2 -add 2.5 foo2_math'

    math3 = fsl.ImageMaths()
    results = math3.run(infile='foo', outfile='foo_math',
                      optstring='-add input_volume2')
    yield assert_not_equal, results.runtime.returncode, 0
    yield assert_equal, results.interface.inputs.infile, 'foo'
    yield assert_equal, results.interface.inputs.outfile, 'foo_math'
    yield assert_equal, results.runtime.cmdline, \
        'fslmaths foo -add input_volume2 foo_math'

    # test arguments for opt_map
    # Fslmath class doesn't have opt_map{}

