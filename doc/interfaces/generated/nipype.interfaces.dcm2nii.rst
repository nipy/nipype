.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.dcm2nii
==================


.. _nipype.interfaces.dcm2nii.Dcm2nii:


.. index:: Dcm2nii

Dcm2nii
-------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/dcm2nii.py#L50>`__

Wraps command **dcm2nii**

Uses MRICRON's dcm2nii to convert dicom files

Examples
~~~~~~~~

>>> from nipype.interfaces.dcm2nii import Dcm2nii
>>> converter = Dcm2nii()
>>> converter.inputs.source_names = ['functional_1.dcm', 'functional_2.dcm']
>>> converter.inputs.gzip_output = True
>>> converter.inputs.output_dir = '.'
>>> converter.cmdline
'dcm2nii -a y -c y -b config.ini -v y -d y -e y -g y -i n -n y -o . -p y -x n -f n functional_1.dcm'

Inputs::

        [Mandatory]
        source_dir: (an existing directory name)
                flag: %s, position: -1
                mutually_exclusive: source_names
        source_names: (a list of items which are an existing file name)
                flag: %s, position: -1
                mutually_exclusive: source_dir

        [Optional]
        anonymize: (a boolean, nipype default value: True)
                flag: -a
        args: (a string)
                Additional parameters to the command
                flag: %s
        collapse_folders: (a boolean, nipype default value: True)
                flag: -c
        config_file: (an existing file name)
                flag: -b %s
        convert_all_pars: (a boolean, nipype default value: True)
                flag: -v
        date_in_filename: (a boolean, nipype default value: True)
                flag: -d
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        events_in_filename: (a boolean, nipype default value: True)
                flag: -e
        gzip_output: (a boolean, nipype default value: False)
                flag: -g
        id_in_filename: (a boolean, nipype default value: False)
                flag: -i
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        nii_output: (a boolean, nipype default value: True)
                flag: -n
        output_dir: (an existing directory name)
                flag: -o %s
        protocol_in_filename: (a boolean, nipype default value: True)
                flag: -p
        reorient: (a boolean)
                flag: -r
        reorient_and_crop: (a boolean, nipype default value: False)
                flag: -x
        source_in_filename: (a boolean, nipype default value: False)
                flag: -f
        spm_analyze: (a boolean)
                flag: -s
                mutually_exclusive: nii_output
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        bvals: (a list of items which are an existing file name)
        bvecs: (a list of items which are an existing file name)
        converted_files: (a list of items which are an existing file name)
        reoriented_and_cropped_files: (a list of items which are an existing
                 file name)
        reoriented_files: (a list of items which are an existing file name)
