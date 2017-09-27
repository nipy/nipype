.. AUTO-GENERATED FILE -- DO NOT EDIT!

algorithms.mesh
===============


.. _nipype.algorithms.mesh.P2PDistance:


.. index:: P2PDistance

P2PDistance
-----------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/algorithms/mesh.py#L42>`__

Calculates a point-to-point (p2p) distance between two corresponding
VTK-readable meshes or contours.

A point-to-point correspondence between nodes is required

Example
~~~~~~~

>>> import nipype.algorithms.mesh as mesh
>>> dist = mesh.P2PDistance()
>>> dist.inputs.surface1 = 'surf1.vtk'
>>> dist.inputs.surface2 = 'surf2.vtk'
>>> res = dist.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        surface1: (an existing file name)
                Reference surface (vtk format) to which compute distance.
        surface2: (an existing file name)
                Test surface (vtk format) from which compute distance.

        [Optional]
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        weighting: ('none' or 'surface', nipype default value: none)
                "none": no weighting is performed, "surface": edge distance is
                weighted by the corresponding surface area

Outputs::

        distance: (a float)
                computed distance
