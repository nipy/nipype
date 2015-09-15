.. AUTO-GENERATED FILE -- DO NOT EDIT!

workflows.dmri.camino.group_connectivity
========================================


.. module:: nipype.workflows.dmri.camino.group_connectivity


.. _nipype.workflows.dmri.camino.group_connectivity.create_group_connectivity_pipeline:

:func:`create_group_connectivity_pipeline`
------------------------------------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/workflows/dmri/camino/group_connectivity.py#L9>`__



Creates a pipeline that performs basic Camino structural connectivity processing
on groups of subjects. Given a diffusion-weighted image, and text files containing
the associated b-values and b-vectors, the workflow will return each subjects' connectomes
in a Connectome File Format (CFF) file, for use in Connectome Viewer (http://www.cmtk.org).

Example
~~~~~~~

>>> import nipype.interfaces.freesurfer as fs
>>> import nipype.workflows.dmri.camino.group_connectivity as groupwork
>>> subjects_dir = '.'
>>> data_dir = '.'
>>> output_dir = '.'
>>> fs.FSCommand.set_default_subjects_dir(subjects_dir)
>>> group_list = {}
>>> group_list['group1'] = ['subj1', 'subj2']
>>> group_list['group2'] = ['subj3', 'subj4']
>>> template_args = dict(dwi=[['subject_id', 'dwi']], bvecs=[['subject_id', 'bvecs']], bvals=[['subject_id', 'bvals']])
>>> group_id = 'group1'
>>> l1pipeline = groupwork.create_group_connectivity_pipeline(group_list, group_id, data_dir, subjects_dir, output_dir, template_args)
>>> l1pipeline.run()                 # doctest: +SKIP

Inputs::

    group_list: Dictionary of subject lists, keyed by group name
    group_id: String containing the group name
    data_dir: Path to the data directory
    subjects_dir: Path to the Freesurfer 'subjects' directory
    output_dir: Path for the output files
    template_args_dict: Dictionary of template arguments for the connectivity pipeline datasource
                            e.g.    info = dict(dwi=[['subject_id', 'dwi']],
                                            bvecs=[['subject_id','bvecs']],
                                            bvals=[['subject_id','bvals']])

