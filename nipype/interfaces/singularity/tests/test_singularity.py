import nipype.interfaces.singularity as singularity
from mock import patch


@patch('os.path.isfile')
def test_form_command(mock_isfile):
    """Test the generated command is as expected"""
    mock_isfile.return_value = True
    cont = singularity.SingularityTask(container="test_container/test.img",
                                       args='abc',
                                       map_dirs_list=['input:/output'])
    cmd_txt = cont.cmdline
    exp_txt = 'singularity run -B input:/output test_container/test.img abc'
    assert(cmd_txt == exp_txt)
