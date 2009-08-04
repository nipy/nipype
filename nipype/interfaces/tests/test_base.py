import nipype.interfaces.base as nii
from nose.tools import assert_true, assert_false, assert_raises, assert_equal, assert_not_equal

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

#test CommandLine
def test_commandline():
    cl = nii.CommandLine('echo', 'foo')
    yield assert_equal, cl.inputs.args, ('echo', 'foo')
    yield assert_equal, cl._compile_command(), None
    yield assert_not_equal, cl, cl.run()
    """
    yield assert_not_equal, cl, cl.update()
    yield assert_not_equal, cl.run(), cl.update()
    cl2 = cl.run('-l')
    cl3 = cl.update('-l')
    yield assert_not_equal, cl.args, cl2.args
    yield assert_not_equal, cl.args, cl3.args
    yield assert_equal, cl2.args, cl3.args
    yield assert_equal, cl2._compile_command(), cl3._compile_command()
    yield assert_equal, nii.CommandLine('ls','-l')._compile_command(),\
        nii.CommandLine('ls -l')._compile_command()
    yield assert_not_equal, nii.CommandLine('ls','-l').args, nii.CommandLine('ls -l').args
    """
    clout = cl.run()
    yield assert_equal, clout.runtime.returncode, 0
    yield assert_equal, clout.runtime.errmessages,  ''
    yield assert_equal, clout.runtime.messages, 'foo\n'


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
