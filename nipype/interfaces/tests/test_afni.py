from nipype.interfaces import afni

from nose.tools import assert_equal


def test_To3d():
    cmd = afni.To3d()
    cmd._compile_command()
    yield assert_equal, cmd.cmdline, 'to3d'
    cmd = afni.To3d(anat=True)
    cmd._compile_command()
    yield assert_equal, cmd.cmdline, 'to3d -anat'
    cmd = afni.To3d()
    cmd.inputs.datum = 'float'
    cmd._compile_command()
    yield assert_equal, cmd.cmdline, 'to3d -datum float'
