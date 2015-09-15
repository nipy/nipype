.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.camino2trackvis.convert
==================================


.. _nipype.interfaces.camino2trackvis.convert.Camino2Trackvis:


.. index:: Camino2Trackvis

Camino2Trackvis
---------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/camino2trackvis/convert.py#L50>`__

Wraps command **camino_to_trackvis**

Wraps camino_to_trackvis from Camino-Trackvis

Convert files from camino .Bfloat format to trackvis .trk format.

Example
~~~~~~~

>>> import nipype.interfaces.camino2trackvis as cam2trk
>>> c2t = cam2trk.Camino2Trackvis()
>>> c2t.inputs.in_file = 'data.Bfloat'
>>> c2t.inputs.out_file = 'streamlines.trk'
>>> c2t.inputs.min_length = 30
>>> c2t.inputs.data_dims = [128, 104, 64]
>>> c2t.inputs.voxel_dims = [2.0, 2.0, 2.0]
>>> c2t.inputs.voxel_order = 'LAS'
>>> c2t.run()                  # doctest: +SKIP

Inputs::

        [Mandatory]
        data_dims: (a list of from 3 to 3 items which are an integer (int or
                 long))
                Three comma-separated integers giving the number of voxels along
                each dimension of the source scans.
                flag: -d %s, position: 4
        in_file: (an existing file name)
                The input .Bfloat (camino) file.
                flag: -i %s, position: 1
        voxel_dims: (a list of from 3 to 3 items which are a float)
                Three comma-separated numbers giving the size of each voxel in mm.
                flag: -x %s, position: 5
        voxel_order: (a file name)
                Set the order in which various directions were stored. Specify with
                three letters consisting of one each from the pairs LR, AP, and SI.
                These stand for Left-Right, Anterior-Posterior, and Superior-
                Inferior. Whichever is specified in each position will be the
                direction of increasing order. Read coordinate system from a NIfTI
                file.
                flag: --voxel-order %s, position: 6

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        min_length: (a float)
                The minimum length of tracts to output
                flag: -l %d, position: 3
        nifti_file: (an existing file name)
                Read coordinate system from a NIfTI file.
                flag: --nifti %s, position: 7
        out_file: (a file name)
                The filename to which to write the .trk (trackvis) file.
                flag: -o %s, position: 2
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        trackvis: (an existing file name)
                The filename to which to write the .trk (trackvis) file.

.. _nipype.interfaces.camino2trackvis.convert.Trackvis2Camino:


.. index:: Trackvis2Camino

Trackvis2Camino
---------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/camino2trackvis/convert.py#L115>`__

Wraps command **trackvis_to_camino**


Inputs::

        [Mandatory]
        in_file: (an existing file name)
                The input .trk (trackvis) file.
                flag: -i %s, position: 1

        [Optional]
        append_file: (an existing file name)
                A file to which the append the .Bfloat data.
                flag: -a %s, position: 2
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        out_file: (a file name)
                The filename to which to write the .Bfloat (camino).
                flag: -o %s, position: 2
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        camino: (an existing file name)
                The filename to which to write the .Bfloat (camino).
