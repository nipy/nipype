import os

filepath = os.path.abspath(__file__)
basedir = os.path.dirname(filepath)

minc2Dfile = os.path.join(basedir, 'data', 'minc_test_2D_00.mnc')
minc3Dfile = os.path.join(basedir, 'data', 'minc_test_3D_00.mnc')

def nonempty_minc_data(i, shape='2D'):
    return os.path.join(basedir, 'data', 'minc_test_%s_%.2d.mnc' % (shape, i,))
