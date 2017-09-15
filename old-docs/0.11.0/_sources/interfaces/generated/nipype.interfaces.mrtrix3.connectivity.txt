.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.mrtrix3.connectivity
===============================


.. _nipype.interfaces.mrtrix3.connectivity.BuildConnectome:


.. index:: BuildConnectome

BuildConnectome
---------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mrtrix3/connectivity.py#L87>`__

Wraps command **tck2connectome**

Generate a connectome matrix from a streamlines file and a node
parcellation image

Example
~~~~~~~

>>> import nipype.interfaces.mrtrix3 as mrt
>>> mat = mrt.BuildConnectome()
>>> mat.inputs.in_file = 'tracks.tck'
>>> mat.inputs.in_parc = 'aparc+aseg.nii'
>>> mat.cmdline                               # doctest: +ELLIPSIS
'tck2connectome tracks.tck aparc+aseg.nii connectome.csv'
>>> mat.run()                                 # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                input tractography
                flag: %s, position: -3
        out_file: (a file name, nipype default value: connectome.csv)
                output file after processing
                flag: %s, position: -1

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
        in_parc: (an existing file name)
                parcellation file
                flag: %s, position: -2
        in_scalar: (an existing file name)
                provide the associated image for the mean_scalar metric
                flag: -image %s
        in_weights: (an existing file name)
                specify a text scalar file containing the streamline weights
                flag: -tck_weights_in %s
        keep_unassigned: (a boolean)
                By default, the program discards the information regarding those
                streamlines that are not successfully assigned to a node pair. Set
                this option to keep these values (will be the first row/column in
                the output matrix)
                flag: -keep_unassigned
        metric: ('count' or 'meanlength' or 'invlength' or 'invnodevolume' or
                 'mean_scalar' or 'invlength_invnodevolume')
                specify the edge weight metric
                flag: -metric %s
        nthreads: (an integer (int or long))
                number of threads. if zero, the number of available cpus will be
                used
                flag: -nthreads %d
        search_forward: (a float)
                project the streamline forwards from the endpoint in search of
                aparcellation node voxel. Argument is the maximum traversal length
                in mm.
                flag: -assignment_forward_search %f
        search_radius: (a float)
                perform a radial search from each streamline endpoint to locate the
                nearest node. Argument is the maximum radius in mm; if no node is
                found within this radius, the streamline endpoint is not assigned to
                any node.
                flag: -assignment_radial_search %f
        search_reverse: (a float)
                traverse from each streamline endpoint inwards along the streamline,
                in search of the last node traversed by the streamline. Argument is
                the maximum traversal length in mm (set to 0 to allow search to
                continue to the streamline midpoint).
                flag: -assignment_reverse_search %f
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        vox_lookup: (a boolean)
                use a simple voxel lookup value at each streamline endpoint
                flag: -assignment_voxel_lookup
        zero_diagonal: (a boolean)
                set all diagonal entries in the matrix to zero (these represent
                streamlines that connect to the same node at both ends)
                flag: -zero_diagonal

Outputs::

        out_file: (an existing file name)
                the output response file

.. _nipype.interfaces.mrtrix3.connectivity.LabelConfig:


.. index:: LabelConfig

LabelConfig
-----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mrtrix3/connectivity.py#L147>`__

Wraps command **labelconfig**

Re-configure parcellation to be incrementally defined.

Example
~~~~~~~

>>> import nipype.interfaces.mrtrix3 as mrt
>>> labels = mrt.LabelConfig()
>>> labels.inputs.in_file = 'aparc+aseg.nii'
>>> labels.inputs.in_config = 'mrtrix3_labelconfig.txt'
>>> labels.cmdline                               # doctest: +ELLIPSIS
'labelconfig aparc+aseg.nii mrtrix3_labelconfig.txt parcellation.mif'
>>> labels.run()                                 # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                input anatomical image
                flag: %s, position: -3
        out_file: (a file name, nipype default value: parcellation.mif)
                output file after processing
                flag: %s, position: -1

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
        in_config: (an existing file name)
                connectome configuration file
                flag: %s, position: -2
        lut_aal: (a file name)
                get information from the AAL lookup table (typically
                "ROI_MNI_V4.txt")
                flag: -lut_aal %s
        lut_basic: (a file name)
                get information from a basic lookup table consisting of index / name
                pairs
                flag: -lut_basic %s
        lut_fs: (a file name)
                get information from a FreeSurfer lookup table(typically
                "FreeSurferColorLUT.txt")
                flag: -lut_freesurfer %s
        lut_itksnap: (a file name)
                get information from an ITK - SNAP lookup table(this includes the
                IIT atlas file "LUT_GM.txt")
                flag: -lut_itksnap %s
        nthreads: (an integer (int or long))
                number of threads. if zero, the number of available cpus will be
                used
                flag: -nthreads %d
        spine: (a file name)
                provide a manually-defined segmentation of the base of the spine
                where the streamlines terminate, so that this can become a node in
                the connection matrix.
                flag: -spine %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        out_file: (an existing file name)
                the output response file
