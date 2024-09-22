import os.path as op
import glob

from ... import logging
from ...utils.filemanip import simplify_list
from ..base import traits, File, Directory, TraitedSpec, OutputMultiPath
from ..freesurfer.base import FSCommand, FSTraitedSpec

iflogger = logging.getLogger("nipype.interface")


class WatershedBEMInputSpec(FSTraitedSpec):
    subject_id = traits.Str(
        argstr="--subject %s",
        mandatory=True,
        desc="Subject ID (must have a complete Freesurfer directory)",
    )
    subjects_dir = Directory(
        exists=True,
        mandatory=True,
        usedefault=True,
        desc="Path to Freesurfer subjects directory",
    )
    volume = traits.Enum(
        "T1",
        "aparc+aseg",
        "aseg",
        "brain",
        "orig",
        "brainmask",
        "ribbon",
        argstr="--volume %s",
        usedefault=True,
        desc='The volume from the "mri" directory to use (defaults to T1)',
    )
    overwrite = traits.Bool(
        True,
        usedefault=True,
        argstr="--overwrite",
        desc="Overwrites the existing files",
    )
    atlas_mode = traits.Bool(
        argstr="--atlas",
        desc="Use atlas mode for registration (default: no rigid alignment)",
    )


class WatershedBEMOutputSpec(TraitedSpec):
    mesh_files = OutputMultiPath(
        File(exists=True),
        desc=(
            "Paths to the output meshes (brain, inner "
            "skull, outer skull, outer skin)"
        ),
    )
    brain_surface = File(
        exists=True, loc="bem/watershed", desc="Brain surface (in Freesurfer format)"
    )
    inner_skull_surface = File(
        exists=True,
        loc="bem/watershed",
        desc="Inner skull surface (in Freesurfer format)",
    )
    outer_skull_surface = File(
        exists=True,
        loc="bem/watershed",
        desc="Outer skull surface (in Freesurfer format)",
    )
    outer_skin_surface = File(
        exists=True,
        loc="bem/watershed",
        desc="Outer skin surface (in Freesurfer format)",
    )
    fif_file = File(
        exists=True,
        loc="bem",
        altkey="fif",
        desc='"fif" format file for EEG processing in MNE',
    )
    cor_files = OutputMultiPath(
        File(exists=True),
        loc="bem/watershed/ws",
        altkey="COR",
        desc='"COR" format files',
    )


class WatershedBEM(FSCommand):
    """Uses mne_watershed_bem to get information from dicom directories

    Examples
    --------

    >>> from nipype.interfaces.mne import WatershedBEM
    >>> bem = WatershedBEM()
    >>> bem.inputs.subject_id = 'subj1'
    >>> bem.inputs.subjects_dir = '.'
    >>> bem.cmdline
    'mne watershed_bem --overwrite --subject subj1 --volume T1'
    >>> bem.run()  # doctest: +SKIP

    """

    _cmd = "mne watershed_bem"
    input_spec = WatershedBEMInputSpec
    output_spec = WatershedBEMOutputSpec
    _additional_metadata = ["loc", "altkey"]

    def _get_files(self, path, key, dirval, altkey=None):
        globsuffix = "*"
        globprefix = "*"
        keydir = op.join(path, dirval)
        if altkey:
            key = altkey
        globpattern = op.join(keydir, f"{globprefix}{key}{globsuffix}")
        return glob.glob(globpattern)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        subjects_dir = self.inputs.subjects_dir
        subject_path = op.join(subjects_dir, self.inputs.subject_id)
        output_traits = self._outputs()
        mesh_paths = []
        for k in list(outputs.keys()):
            if k != "mesh_files":
                val = self._get_files(
                    subject_path,
                    k,
                    output_traits.traits()[k].loc,
                    output_traits.traits()[k].altkey,
                )
                if val:
                    value_list = simplify_list(val)
                    if isinstance(value_list, list):
                        out_files = [op.abspath(value) for value in value_list]
                    elif isinstance(value_list, (str, bytes)):
                        out_files = op.abspath(value_list)
                    else:
                        raise TypeError
                    outputs[k] = out_files
                    if k.rfind("surface") != -1:
                        mesh_paths.append(out_files)
        outputs["mesh_files"] = mesh_paths
        return outputs
