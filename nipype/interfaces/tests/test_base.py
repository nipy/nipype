import nipype.interfaces.base as nii
from nipype.testing import *
import os

#test Bunch
def test_bunch():
    b = nii.Bunch()
    yield assert_equal, b.__dict__,{}
    b = nii.Bunch(a=1,b=[2,3])
    yield assert_equal, b.__dict__,{'a': 1, 'b': [2,3]}

def test_bunch_attribute():
    b = nii.Bunch(a=1,b=[2,3],c=None)
    yield assert_equal, b.a ,1
    yield assert_equal, b.b, [2,3]
    yield assert_equal, b.c, None

def test_bunch_repr():
    b = nii.Bunch(b=2,c=3,a=dict(n=1,m=2))
    yield assert_equal, repr(b), "Bunch(a={'m': 2, 'n': 1}, b=2, c=3)"

def test_bunch_methods():
    b = nii.Bunch(a=2)
    b.update(a=3)
    newb = b.dictcopy()
    yield assert_equal, b.a, 3
    yield assert_equal, b.get('a'), 3
    yield assert_equal, b.get('badkey', 'otherthing'), 'otherthing'
    yield assert_not_equal, b, newb
    yield assert_equal, type(dict()), type(newb)
    yield assert_equal, newb['a'], 3

def test_bunch_hash():
    # NOTE: Since the path to the json file is included in the Bunch,
    # the hash will be unique to each machine.
    pth = os.path.split(os.path.abspath(__file__))[0]
    json_pth = os.path.join(pth, 'realign_json.json')
    b = nii.Bunch(infile = json_pth, 
                  otherthing = 'blue',
                  yat = True)
    newbdict, bhash = b._get_bunch_hash()
    newbhash = nii.md5()
    # Be sure to sort the dictionary before generating the hash.
    newbhash.update(str(sorted(newbdict.items())))
    yield assert_equal, bhash, newbhash.hexdigest()
    # Make sure the hash stored in the json file for `infile` is correct.
    jshash = nii.md5()
    fp = file(json_pth)
    jshash.update(fp.read())
    fp.close()
    yield assert_equal, newbdict['infile'][0][1], jshash.hexdigest()
    yield assert_equal, newbdict['yat'], True

#test CommandLine
def test_commandline():
    cl = nii.CommandLine('echo', 'foo')
    yield assert_equal, cl.inputs.args, ['echo', 'foo']
    yield assert_equal, cl.cmdline, 'echo foo'
    yield assert_not_equal, cl, cl.run()
    
    yield assert_equal, nii.CommandLine('echo foo').cmdline,\
        nii.CommandLine(args='echo foo').cmdline
    yield assert_equal, nii.CommandLine('ls','-l').cmdline,\
        nii.CommandLine('ls -l').cmdline
    clout = cl.run()
    yield assert_equal, clout.runtime.returncode, 0
    yield assert_equal, clout.runtime.stderr,  ''
    yield assert_equal, clout.runtime.stdout, 'foo\n'
    yield assert_equal, clout.interface.cmdline, cl.cmdline
    yield assert_not_equal, clout.interface, cl

"""
stuff =CommandLine('this is what I want to run')

better = Bet(frac=0.5, input='anotherfile', flags = ['-R', '-k'])

betted = better.run(input='filea', output='ssfilea')

def f(a='', *args, **kwargs):
    whateve

f(file1, file2, a=Something, b='this')


cl = COmmandLine('ls')

d1 = cl.run('/path/to/d1')

d2 = cl.run('/path/to/d2')

d3 = CommandLine().run('ls /path/to/d3')
or
d3 = CommandLine('ls /path/to/d3').run()
or
d3 = CommandLine('ls').run('/path/to/d3')


stuff = CommandLine(flags={'-f':0.5, 'otherthing': 2, '-c':[100,87,92], '-R':None})

stuff = CommandLine('ls',flags=['-R', '--thingy', '100 87 90'])


cmd1 = CommandLine('ls -l *')
cmd2 = CommandLine.update('-a -h').remove('-l')
"""
