.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.cmtk.convert
=======================


.. _nipype.interfaces.cmtk.convert.CFFConverter:


.. index:: CFFConverter

CFFConverter
------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/interfaces/cmtk/convert.py#L59>`__

Creates a Connectome File Format (CFF) file from input networks, surfaces, volumes, tracts, etcetera....

Example
~~~~~~~

>>> import nipype.interfaces.cmtk as cmtk
>>> cvt = cmtk.CFFConverter()
>>> cvt.inputs.title = 'subject 1'
>>> cvt.inputs.gifti_surfaces = ['lh.pial_converted.gii', 'rh.pial_converted.gii']
>>> cvt.inputs.tract_files = ['streamlines.trk']
>>> cvt.inputs.gpickled_networks = ['network0.gpickle']
>>> cvt.run()                 # doctest: +SKIP

Inputs::

        [Mandatory]

        [Optional]
        creator: (a string)
                Creator
        data_files: (an existing file name)
                list of external data files (i.e. Numpy, HD5, XML)
        description: (a string, nipype default value: Created with the Nipype
                 CFF converter)
                Description
        email: (a string)
                Email address
        gifti_labels: (an existing file name)
                list of GIFTI labels
        gifti_surfaces: (an existing file name)
                list of GIFTI surfaces
        gpickled_networks: (an existing file name)
                list of gpickled Networkx graphs
        graphml_networks: (an existing file name)
                list of graphML networks
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        license: (a string)
                License
        nifti_volumes: (an existing file name)
                list of NIFTI volumes
        out_file: (a file name, nipype default value: connectome.cff)
                Output connectome file
        publisher: (a string)
                Publisher
        references: (a string)
                References
        relation: (a string)
                Relation
        rights: (a string)
                Rights
        script_files: (an existing file name)
                list of script files to include
        species: (a string, nipype default value: Homo sapiens)
                Species
        timeseries_files: (an existing file name)
                list of HDF5 timeseries files
        title: (a string)
                Connectome Title
        tract_files: (an existing file name)
                list of Trackvis fiber files

Outputs::

        connectome_file: (an existing file name)
                Output connectome file

.. _nipype.interfaces.cmtk.convert.MergeCNetworks:


.. index:: MergeCNetworks

MergeCNetworks
--------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/interfaces/cmtk/convert.py#L212>`__

Merges networks from multiple CFF files into one new CFF file.

Example
~~~~~~~

>>> import nipype.interfaces.cmtk as cmtk
>>> mrg = cmtk.MergeCNetworks()
>>> mrg.inputs.in_files = ['subj1.cff','subj2.cff']
>>> mrg.run()                  # doctest: +SKIP

Inputs::

        [Mandatory]
        in_files: (an existing file name)
                List of CFF files to extract networks from

        [Optional]
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        out_file: (a file name, nipype default value:
                 merged_network_connectome.cff)
                Output CFF file with all the networks added

Outputs::

        connectome_file: (an existing file name)
                Output CFF file with all the networks added
