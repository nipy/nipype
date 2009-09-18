from nipype.testing import assert_equal, assert_false, assert_true

import nipype.interfaces.spm as spm


def test_spm_path():
    spm_path = spm.spm_info.spm_path
    if spm_path is not None:
        yield assert_equal, type(spm_path), type('')
        yield assert_true, 'spm' in spm_path

def test_reformat_dict_for_savemat():
    mlab = spm.SpmMatlabCommandLine()
    out = mlab._reformat_dict_for_savemat({'a':{'b':{'c':[]}}})
    yield assert_equal, out, [{'a': [{'b': [{'c': []}]}]}]
    
def test_generate_job():
    mlab = spm.SpmMatlabCommandLine()
    out = mlab._generate_job()
    yield assert_equal, out, ''
    contents = {'contents':[1,2,3,4]}
    out = mlab._generate_job(contents=contents)
    yield assert_equal, out, '.contents(1) = 1;\n.contents(2) = 2;\n.contents(3) = 3;\n.contents(4) = 4;\n'
    
def test_make_matlab_command():
    mlab = spm.SpmMatlabCommandLine()
    contents = {'contents':[1,2,3,4]}
    cmdline,script = mlab._make_matlab_command('jobtype', 'jobname', [contents])
    yield assert_equal, cmdline, \
        'matlab -nodesktop -nosplash -r "pyscript_jobname;exit" '
    yield assert_true, 'jobs{1}.jobtype{1}.jobname{1}.contents(3) = 3;' \
        in script

def test_spm_realign():
    realign = spm.Realign(write=False)
    updatedopts = realign._parseinputs()
    yield assert_equal, updatedopts, {'data':[],'eoptions':{},'roptions':{}}
    yield assert_false, realign.inputs.write

