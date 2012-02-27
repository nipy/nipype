# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
import nipype.algorithms.misc as misc
from nipype.interfaces.utility import Function
from nipype.workflows.utils import region_list_from_volume, id_list_from_lookup_table
import os, os.path as op
   
def create_tessellation_flow(name='tessellate'):
    """Tessellates the input subject's aseg.mgz volume and returns
    the surfaces for each region in stereolithic (.stl) format

    Example
    -------
    >>> from nipype.workflows.freesurfer.mne import create_tessellation_flow
    >>> tessflow = create_tessellation_flow()
    >>> tessflow.inputs.inputspec.subject_id = 'subj1'
    >>> tessflow.inputs.inputspec.subjects_dir = '.'
    >>> tessflow.inputs.inputspec.lookup_file = 'FreeSurferColorLUT.txt' # doctest: +SKIP
    >>> tessflow.run()  # doctest: +SKIP


    Inputs::

           inputspec.subject_id : freesurfer subject id
           inputspec.subjects_dir : freesurfer subjects directory
           inputspec.lookup_file : lookup file from freesurfer directory

    Outputs::

           outputspec.mask_file : binary mask file in reference image space
    """

    """
    Initialize the workflow
    """
        
    tessflow = pe.Workflow(name=name)

    """
    Define the inputs to the workflow.
    """

    inputnode = pe.Node(niu.IdentityInterface(fields=['subject_id',
                                                      'subjects_dir',
                                                      'lookup_file']),
                        name='inputspec')

    """
    Define all the nodes of the workflow:

      fssource: used to retrieve aseg.mgz
      mri_convert : converts aseg.mgz to aseg.nii
      tessellate : tessellates regions in aseg.mgz
      surfconvert : converts regions to stereolithographic (.stl) format

    """

    fssource = pe.Node(nio.FreeSurferSource(),
                       name = 'fssource')
    volconvert = pe.Node(fs.MRIConvert(out_type='nii'),
                       name = 'volconvert')
    tessellate = pe.MapNode(fs.MRITessellate(),
                        iterfield=['label_value','out_file'],
                        name='tessellate')
    surfconvert = pe.MapNode(fs.MRIsConvert(out_datatype='stl'),
                          iterfield=['in_file'],
                          name='surfconvert')

    region_list_from_volume_interface = Function(input_names=["in_file"],
                             output_names=["region_list"],
                             function=region_list_from_volume)
                             
    id_list_from_lookup_table_interface = Function(input_names=["lookup_file", "region_list"],
                             output_names=["id_list"],
                             function=id_list_from_lookup_table)

    region_list_from_volume_node = pe.Node(interface=region_list_from_volume_interface, name='region_list_from_volume_node')
    id_list_from_lookup_table_node = pe.Node(interface=id_list_from_lookup_table_interface, name='id_list_from_lookup_table_node')

    """
    Connect the nodes
    """

    tessflow.connect([
            (inputnode, fssource, [('subject_id','subject_id'),
                                   ('subjects_dir','subjects_dir')]),
            (fssource, volconvert, [('aseg', 'in_file')]),
            (volconvert, region_list_from_volume_node, [('out_file', 'in_file')]),
            (region_list_from_volume_node, tessellate, [('region_list', 'label_value')]),
            (region_list_from_volume_node, id_list_from_lookup_table_node, [('region_list', 'region_list')]),
            (inputnode, id_list_from_lookup_table_node, [('lookup_file', 'lookup_file')]),
            (id_list_from_lookup_table_node, tessellate, [('id_list', 'out_file')]),
            (fssource, tessellate, [('aseg', 'in_file')]),
            (tessellate, surfconvert, [('surface','in_file')]),
            ])

    """
    Setup an outputnode that defines relevant inputs of the workflow.
    """

    outputnode = pe.Node(niu.IdentityInterface(fields=["meshes"]),
                         name="outputspec")
    tessflow.connect([
            (surfconvert, outputnode, [("converted", "meshes")]),
            ])
    return tessflow
