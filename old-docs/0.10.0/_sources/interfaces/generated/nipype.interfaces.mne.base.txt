.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.mne.base
===================


.. _nipype.interfaces.mne.base.WatershedBEM:


.. index:: WatershedBEM

WatershedBEM
------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/interfaces/mne/base.py#L46>`__

Wraps command **mne_watershed_bem**

Uses mne_watershed_bem to get information from dicom directories

Examples
~~~~~~~~

>>> from nipype.interfaces.mne import WatershedBEM
>>> bem = WatershedBEM()
>>> bem.inputs.subject_id = 'subj1'
>>> bem.inputs.subjects_dir = '.'
>>> bem.cmdline
'mne_watershed_bem --overwrite --subject subj1 --volume T1'
>>> bem.run()                               # doctest: +SKIP

Inputs::

        [Mandatory]
        subject_id: (a string)
                Subject ID (must have a complete Freesurfer directory)
                flag: --subject %s
        subjects_dir: (an existing directory name, nipype default value: )
                Path to Freesurfer subjects directory
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal
                immediately, `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        atlas_mode: (a boolean)
                Use atlas mode for registration (default: no rigid alignment)
                flag: --atlas
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        overwrite: (a boolean, nipype default value: True)
                Overwrites the existing files
                flag: --overwrite
        volume: ('T1' or 'aparc+aseg' or 'aseg' or 'brain' or 'orig' or
                 'brainmask' or 'ribbon', nipype default value: T1)
                The volume from the "mri" directory to use (defaults to T1)
                flag: --volume %s

Outputs::

        brain_surface: (an existing file name)
                Brain surface (in Freesurfer format)
        cor_files: (an existing file name)
                "COR" format files
        fif_file: (an existing file name)
                "fif" format file for EEG processing in MNE
        inner_skull_surface: (an existing file name)
                Inner skull surface (in Freesurfer format)
        mesh_files: (an existing file name)
                Paths to the output meshes (brain, inner skull, outer skull, outer
                skin)
        outer_skin_surface: (an existing file name)
                Outer skin surface (in Freesurfer format)
        outer_skull_surface: (an existing file name)
                Outer skull surface (in Freesurfer format)
