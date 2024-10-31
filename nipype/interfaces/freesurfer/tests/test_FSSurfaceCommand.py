# Modified 2017.04.21 by Chris Markiewicz
import pytest

from ..base import FSSurfaceCommand
from ... import freesurfer as fs
from ...io import FreeSurferSource


def test_FSSurfaceCommand_inputs():
    input_map = dict(
        args=dict(argstr="%s"),
        environ=dict(nohash=True, usedefault=True),
        subjects_dir=dict(),
    )
    inputs = FSSurfaceCommand.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


@pytest.mark.skipif(fs.no_freesurfer(), reason="freesurfer is not installed")
def test_associated_file(tmpdir):
    fssrc = FreeSurferSource(
        subjects_dir=fs.Info.subjectsdir(), subject_id="fsaverage", hemi="lh"
    )
    fssrc.base_dir = tmpdir.strpath
    fssrc.resource_monitor = False

    fsavginfo = fssrc.run().outputs.get()

    # Pairs of white/pial files in the same directories
    for white, pial in [
        ("lh.white", "lh.pial"),
        ("./lh.white", "./lh.pial"),
        (fsavginfo["white"], fsavginfo["pial"]),
    ]:
        # Unspecified paths, possibly with missing hemisphere information,
        # are equivalent to using the same directory and hemisphere
        for name in ("pial", "lh.pial", pial):
            assert FSSurfaceCommand._associated_file(white, name) == pial

        # With path information, no changes are made
        for name in ("./pial", "./lh.pial", fsavginfo["pial"]):
            assert FSSurfaceCommand._associated_file(white, name) == name
