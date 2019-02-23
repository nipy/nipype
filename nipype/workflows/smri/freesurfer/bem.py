# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from ....pipeline import engine as pe
from ....interfaces import mne as mne
from ....interfaces import freesurfer as fs
from ....interfaces import utility as niu


def create_bem_flow(name='bem', out_format='stl'):
    """Uses MNE's Watershed algorithm to create Boundary Element Meshes (BEM)
     for a subject's brain, inner/outer skull, and skin. The surfaces are
     returned in the desired (by default, stereolithic .stl) format.

    Example
    -------
    >>> from nipype.workflows.smri.freesurfer import create_bem_flow
    >>> bemflow = create_bem_flow()
    >>> bemflow.inputs.inputspec.subject_id = 'subj1'
    >>> bemflow.inputs.inputspec.subjects_dir = '.'
    >>> bemflow.run()  # doctest: +SKIP


    Inputs::

           inputspec.subject_id : freesurfer subject id
           inputspec.subjects_dir : freesurfer subjects directory

    Outputs::

           outputspec.meshes : output boundary element meshes in (by default)
                               stereolithographic (.stl) format
    """
    """
    Initialize the workflow
    """

    bemflow = pe.Workflow(name=name)
    """
    Define the inputs to the workflow.
    """

    inputnode = pe.Node(
        niu.IdentityInterface(fields=['subject_id', 'subjects_dir']),
        name='inputspec')
    """
    Define all the nodes of the workflow:

      fssource: used to retrieve aseg.mgz
      mri_convert : converts aseg.mgz to aseg.nii
      tessellate : tessellates regions in aseg.mgz
      surfconvert : converts regions to stereolithographic (.stl) format

    """

    watershed_bem = pe.Node(interface=mne.WatershedBEM(), name='WatershedBEM')

    surfconvert = pe.MapNode(
        fs.MRIsConvert(out_datatype=out_format),
        iterfield=['in_file'],
        name='surfconvert')
    """
    Connect the nodes
    """

    bemflow.connect([
        (inputnode, watershed_bem, [('subject_id', 'subject_id'),
                                    ('subjects_dir', 'subjects_dir')]),
        (watershed_bem, surfconvert, [('mesh_files', 'in_file')]),
    ])
    """
    Setup an outputnode that defines relevant inputs of the workflow.
    """

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["meshes"]), name="outputspec")
    bemflow.connect([
        (surfconvert, outputnode, [("converted", "meshes")]),
    ])
    return bemflow
