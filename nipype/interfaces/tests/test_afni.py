from nipype.interfaces import afni

from nose.tools import assert_equal


def test_to3d():
    cmd = afni.to3d()
    cmd._compile_command()
    yield assert_equal, cmd.cmdline, 'to3d'
    cmd = afni.to3d(anat=True)
    cmd._compile_command()
    yield assert_equal, cmd.cmdline, 'to3d -anat'
    cmd = afni.to3d()
    cmd.inputs.datum = 'float'
    cmd._compile_command()
    yield assert_equal, cmd.cmdline, 'to3d -datum float'
