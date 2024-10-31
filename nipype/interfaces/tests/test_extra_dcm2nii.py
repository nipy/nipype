import os
import pytest

from nipype.interfaces.dcm2nii import Dcm2niix

no_dcm2niix = not bool(Dcm2niix().version)
no_datalad = False
try:
    from datalad import api  # to pull and grab data
    from datalad.support.exceptions import IncompleteResultsError
except ImportError:
    no_datalad = True

DICOM_DIR = "http://datasets-tests.datalad.org/dicoms/dcm2niix-tests"


@pytest.fixture
def fetch_data():
    def _fetch_data(datadir, dicoms):
        try:
            """Fetches some test DICOMs using datalad"""
            api.install(path=datadir, source=DICOM_DIR)
            data = os.path.join(datadir, dicoms)
            api.get(path=data, dataset=datadir)
        except IncompleteResultsError as exc:
            pytest.skip("Failed to fetch test data: %s" % str(exc))
        return data

    return _fetch_data


@pytest.mark.skipif(no_datalad, reason="Datalad required")
@pytest.mark.skipif(no_dcm2niix, reason="Dcm2niix required")
def test_dcm2niix_dti(fetch_data, tmpdir):
    tmpdir.chdir()
    datadir = tmpdir.mkdir("data").strpath
    dicoms = fetch_data(datadir, "Siemens_Sag_DTI_20160825_145811")

    def assert_dti(res):
        "Some assertions we will make"
        assert res.outputs.converted_files
        assert res.outputs.bvals
        assert res.outputs.bvecs
        outputs = [y for x, y in res.outputs.get().items()]
        if res.inputs.get("bids_format"):
            # ensure all outputs are of equal lengths
            assert len(set(map(len, outputs))) == 1
        else:
            assert not res.outputs.bids

    dcm = Dcm2niix()
    dcm.inputs.source_dir = dicoms
    dcm.inputs.out_filename = "%u%z"
    assert_dti(dcm.run())

    # now run specifying output directory and removing BIDS option
    outdir = tmpdir.mkdir("conversion").strpath
    dcm.inputs.output_dir = outdir
    dcm.inputs.bids_format = False
    assert_dti(dcm.run())
