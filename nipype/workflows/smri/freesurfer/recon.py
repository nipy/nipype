from ....pipeline import engine as pe
from ....interfaces import freesurfer as fs
from ....interfaces import utility as niu


def create_skullstripped_recon_flow(name="skullstripped_recon_all"):
    """Performs recon-all on voulmes that are already skull stripped.
    FreeSurfer failes to perform skullstrippig on some volumes (especially
    MP2RAGE). This can be avoided by doing skullstripping before runnig recon-all
    (using for example SPECTRE algorithm)

    Example
    -------
    >>> from nipype.workflows.smri.freesurfer import create_skullstripped_recon_flow
    >>> recon_flow = create_skullstripped_recon_flow()
    >>> recon_flow.inputs.inputspec.subject_id = 'subj1'
    >>> recon_flow.inputs.inputspec.T1_files = 'T1.nii.gz'
    >>> recon_flow.run()  # doctest: +SKIP


    Inputs::
           inputspec.T1_files : skullstripped T1_files (mandatory)
           inputspec.subject_id : freesurfer subject id (optional)
           inputspec.subjects_dir : freesurfer subjects directory (optional)

    Outputs::

           outputspec.subject_id : freesurfer subject id
           outputspec.subjects_dir : freesurfer subjects directory
    """
    wf = pe.Workflow(name=name)

    inputnode = pe.Node(niu.IdentityInterface(fields=['subject_id',
                                                      'subjects_dir',
                                                      'T1_files']),
                        name='inputspec')

    autorecon1 = pe.Node(fs.ReconAll(), name="autorecon1")
    autorecon1.plugin_args = {'submit_specs': 'request_memory = 2500'}
    autorecon1.inputs.directive = "autorecon1"
    autorecon1.inputs.args = "-noskullstrip"
    autorecon1._interface._can_resume = False

    wf.connect(inputnode, "T1_files", autorecon1, "T1_files")
    wf.connect(inputnode, "subjects_dir", autorecon1, "subjects_dir")
    wf.connect(inputnode, "subject_id", autorecon1, "subject_id")

    def link_masks(subjects_dir, subject_id):
        import os
        os.symlink(os.path.join(subjects_dir, subject_id, "mri", "T1.mgz"),
                   os.path.join(subjects_dir, subject_id, "mri", "brainmask.auto.mgz"))
        os.symlink(os.path.join(subjects_dir, subject_id, "mri", "brainmask.auto.mgz"),
                   os.path.join(subjects_dir, subject_id, "mri", "brainmask.mgz"))
        return subjects_dir, subject_id

    masks = pe.Node(niu.Function(input_names=['subjects_dir', 'subject_id'],
                                 output_names=['subjects_dir', 'subject_id'],
                                 function=link_masks), name="link_masks")

    wf.connect(autorecon1, "subjects_dir", masks, "subjects_dir")
    wf.connect(autorecon1, "subject_id", masks, "subject_id")

    autorecon_resume = pe.Node(fs.ReconAll(), name="autorecon_resume")
    autorecon_resume.plugin_args = {'submit_specs': 'request_memory = 2500'}
    autorecon_resume.inputs.args = "-no-isrunning"
    wf.connect(masks, "subjects_dir", autorecon_resume, "subjects_dir")
    wf.connect(masks, "subject_id", autorecon_resume, "subject_id")

    outputnode = pe.Node(niu.IdentityInterface(fields=['subject_id',
                                                       'subjects_dir']),
                         name='outputspec')

    wf.connect(autorecon_resume, "subjects_dir", outputnode, "subjects_dir")
    wf.connect(autorecon_resume, "subject_id", outputnode, "subject_id")
    return wf
