import os
import pytest
import shutil

from nipype.interfaces.dcm2nii import Dcm2niix
no_dcm2niix = not bool(Dcm2niix().version)
no_datalad = False
try:
    from datalad import api # to pull and grab data
    from datalad.support.exceptions import IncompleteResultsError
except ImportError:
    no_datalad = True

DICOM_DIR = 'http://datasets-tests.datalad.org/dicoms/dcm2niix-tests'


def fetch_data(tmpdir, dicoms):
    """Fetches some test DICOMs using datalad"""
    data = os.path.join(tmpdir, 'data')
    api.install(path=data, source=DICOM_DIR)
    data = os.path.join(data, dicoms)
    api.get(path=data)
    return data

@pytest.mark.skipif(no_datalad, reason="Datalad required")
@pytest.mark.skipif(no_dcm2niix, reason="Dcm2niix required")
def test_dcm2niix_dwi(tmpdir):
    tmpdir.chdir()
    try:
        datadir = fetch_data(tmpdir.strpath, 'Siemens_Sag_DTI_20160825_145811')
    except IncompleteResultsError as exc:
        pytest.skip("Failed to fetch test data: %s" % str(exc))

    def assert_dwi(eg, bids):
        "Some assertions we will make"
        assert eg.outputs.converted_files
        assert eg.outputs.bvals
        assert eg.outputs.bvecs
        outputs = [y for x,y in eg.outputs.get().items()]
        if bids:
            # ensure all outputs are of equal lengths
            assert len(set(map(len, outputs))) == 1
        else:
            assert not eg2.outputs.bids

    dcm = Dcm2niix()
    dcm.inputs.source_dir = datadir
    dcm.inputs.out_filename = '%u%z'
    eg1 = dcm.run()
    assert_dwi(eg1, True)

    # now run specifying output directory and removing BIDS option
    outdir = tmpdir.mkdir('conversion').strpath
    dcm.inputs.output_dir = outdir
    dcm.inputs.bids_format = False
    eg2 = dcm.run()
    assert_dwi(eg2, False)
