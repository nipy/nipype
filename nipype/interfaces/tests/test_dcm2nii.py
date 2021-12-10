import pytest


from nipype.interfaces import dcm2nii


@pytest.mark.parametrize(
    "fname, extension",
    [
        ("output_1", ".txt"),
        ("output_w_[]_meta_1", ".json"),
        ("output_w_**^$?_meta_2", ".txt"),
    ],
)
def test_search_files(tmp_path, fname, extension):
    tmp_fname = fname + extension
    test_file = tmp_path / tmp_fname
    test_file.touch()
    actual_files_list = dcm2nii.search_files(str(tmp_path / fname), [extension])
    for f in actual_files_list:
        assert str(test_file) == f
