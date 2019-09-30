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


def fetch_data(datadir, dicoms):
    """Fetches some test DICOMs using datalad"""
    api.install(path=datadir, source=DICOM_DIR)
    data = os.path.join(datadir, dicoms)
    api.get(path=data)
    return data

@pytest.mark.skipif(no_datalad, reason="Datalad required")
@pytest.mark.skipif(no_dcm2niix, reason="Dcm2niix required")
def test_dcm2niix_dwi(tmpdir):
    tmpdir.chdir()
    datadir = tmpdir.mkdir('data').strpath
    try:
        dicoms = fetch_data(datadir, 'Siemens_Sag_DTI_20160825_145811')
    except IncompleteResultsError as exc:
        pytest.skip("Failed to fetch test data: %s" % str(exc))

    def assert_dwi(eg):
        "Some assertions we will make"
        assert eg.outputs.converted_files
        assert eg.outputs.bvals
        assert eg.outputs.bvecs
        outputs = [y for x,y in eg.outputs.get().items()]
        if eg.inputs.get('bids_format'):
            # ensure all outputs are of equal lengths
            assert len(set(map(len, outputs))) == 1
        else:
            assert not eg.outputs.bids

    dcm = Dcm2niix()
    dcm.inputs.source_dir = dicoms
    dcm.inputs.out_filename = '%u%z'
    assert_dwi(dcm.run())

    # now run specifying output directory and removing BIDS option
    outdir = tmpdir.mkdir('conversion').strpath
    dcm.inputs.output_dir = outdir
    dcm.inputs.bids_format = False
    assert_dwi(dcm.run())
