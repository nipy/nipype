import nipype.interfaces.spm as spm
from nose.tools import assert_true, assert_false, assert_raises, assert_equal, assert_not_equal


def test_make_job():
    contents = {'contents':[1,2,3,4]}
    job = spm.make_job('jobtype','jobname',contents)
    yield assert_equal, job.keys()[0],'jobs'
    yield assert_equal, job, {'jobs': [{'jobtype': [{'jobname': {'contents': [1, 2, 3, 4]}}]}]}

def test_spm_realign():
    realign = spm.Realign(write=False)
    updatedopts = realign._parseopts()
    yield assert_equal, updatedopts, {'eoptions':{},'roptions':{}}
    yield assert_equal, realign.opts.write, False

