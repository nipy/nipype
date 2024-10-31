import pytest


from nipype.interfaces import dcm2nii


@pytest.mark.parametrize(
    "fname, extension, search_crop",
    [
        ("output_1", ".txt", False),
        ("output_w_[]_meta_1", ".json", False),
        ("output_w_**^$?_meta_2", ".txt", False),
        ("output_cropped", ".txt", True),
    ],
)
def test_search_files(tmp_path, fname, extension, search_crop):
    tmp_fname = fname + extension
    test_file = tmp_path / tmp_fname
    test_file.touch()
    if search_crop:
        tmp_cropped_fname = fname + "_Crop_1" + extension
        test_cropped_file = tmp_path / tmp_cropped_fname
        test_cropped_file.touch()

    actual_files_list = dcm2nii.search_files(
        str(tmp_path / fname), [extension], search_crop
    )
    for f in actual_files_list:
        if search_crop:
            assert f in (str(test_cropped_file), str(test_file))
        else:
            assert str(test_file) == f
