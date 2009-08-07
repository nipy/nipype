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
    cmd = afni.To3d()
    cmd.inputs.session = '/home/bobama'
    cmd._compile_command()
    yield assert_equal, cmd.cmdline, 'to3d -session /home/bobama'
    cmd = afni.To3d(prefix='foo.nii.gz')
    cmd._compile_command()
    yield assert_equal, cmd.cmdline, 'to3d -prefix foo.nii.gz'
    cmd = afni.To3d(infiles='/data/*.dcm')
    cmd._compile_command()
    yield assert_equal, cmd.cmdline, 'to3d /data/*.dcm'
    cmd = afni.To3d(epan=True)
    cmd._compile_command()
    yield assert_equal, cmd.cmdline, 'to3d -epan'
    cmd = afni.To3d(skip_outliers=True)
    cmd._compile_command()
    yield assert_equal, cmd.cmdline, 'to3d -skip_outliers'
    cmd = afni.To3d(assume_dicom_mosaic=True)
    cmd._compile_command()
    yield assert_equal, cmd.cmdline, 'to3d -assume_dicom_mosaic'
    # Test slice time params
    cmd = afni.To3d()
    cmd.inputs.time = ['zt', 12, 150, 2000, 'alt+z']
    cmd._compile_command()
    yield assert_equal, cmd.cmdline, 'to3d -time:zt 12 150 2000.000000 alt+z'
    cmd = afni.To3d()
    cmd.inputs.time = ['tz', 150, 12, 2000, 'alt+z']
    cmd._compile_command()
    yield assert_equal, cmd.cmdline, 'to3d -time:tz 150 12 2000.000000 alt+z'

