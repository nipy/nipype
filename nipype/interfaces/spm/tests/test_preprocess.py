from nipype.testing import assert_equal
import nipype.interfaces.spm as spm
from nipype.interfaces.base import Bunch

def test_spm_realign_inputs():
    realign = spm.Realign()
    definputs = Bunch(infile=None,
                      jobtype='estwrite',
                      quality=None,
                      fwhm=None,
                      separation=None,
                      register_to_mean=None,
                      weight_img=None,
                      interp=None,
                      wrap=None,
                      write_which=None,
                      write_interp=None,
                      write_wrap=None,
                      write_mask=None)
                      
    yield assert_equal, str(realign.inputs), str(definputs)

def test_spm_get_input_info():
    realign = spm.Realign()
    yield assert_equal, str(realign.get_input_info()[0]), \
        str(Bunch(key='infile',copy=True))
    
def test_spm_parse_inputs():
    realign = spm.Realign(jobtype='estimate')
    updatedopts = realign._parse_inputs()
    yield assert_equal, updatedopts, [{'estimate': {}}]
    yield assert_equal, 'estimate', realign.inputs.jobtype

