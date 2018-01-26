"""Test afni deconvolve"""

from ..model import Deconvolve

def test_x1dstop():
    deconv = Deconvolve()
    deconv.inputs.out_file = 'file.nii'
    assert 'out_file' in deconv._list_outputs()
    deconv.inputs.x1D_stop = True
    assert 'out_file' not in deconv._list_outputs()
    assert 'cbucket' not in deconv._list_outputs()
