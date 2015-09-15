.. AUTO-GENERATED FILE -- DO NOT EDIT!

algorithms.mesh
===============


.. _nipype.algorithms.mesh.ComputeMeshWarp:


.. index:: ComputeMeshWarp

ComputeMeshWarp
---------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/algorithms/mesh.py#L185>`__

Calculates a the vertex-wise warping to get surface2 from surface1.
It also reports the average distance of vertices, using the norm specified
as input.

.. warning:

  A point-to-point correspondence between surfaces is required


Example
~~~~~~~

>>> import nipype.algorithms.mesh as m
>>> dist = m.ComputeMeshWarp()
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
        metric: ('euclidean' or 'sqeuclidean', nipype default value:
                 euclidean)
                norm used to report distance
        out_file: (a file name, nipype default value: distance.npy)
                numpy file keeping computed distances and weights
        out_warp: (a file name, nipype default value: surfwarp.vtk)
                vtk file based on surface1 and warpings mapping it to surface2
        weighting: ('none' or 'area', nipype default value: none)
                "none": no weighting is performed, surface": edge distance is
                weighted by the corresponding surface area

Outputs::

        distance: (a float)
                computed distance
        out_file: (an existing file name)
                numpy file keeping computed distances and weights
        out_warp: (an existing file name)
                vtk file with the vertex-wise mapping of surface1 to surface2

.. _nipype.algorithms.mesh.MeshWarpMaths:


.. index:: MeshWarpMaths

MeshWarpMaths
-------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/algorithms/mesh.py#L325>`__

Performs the most basic mathematical operations on the warping field
defined at each vertex of the input surface. A surface with scalar
or vector data can be used as operator for non-uniform operations.

.. warning:

  A point-to-point correspondence between surfaces is required


Example
~~~~~~~

>>> import nipype.algorithms.mesh as m
>>> mmath = m.MeshWarpMaths()
>>> mmath.inputs.in_surf = 'surf1.vtk'
>>> mmath.inputs.operator = 'surf2.vtk'
>>> mmath.inputs.operation = 'mul'
>>> res = mmath.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        in_surf: (an existing file name)
                Input surface in vtk format, with associated warp field as point
                data (ie. from ComputeMeshWarp
        operator: (a float or a tuple of the form: (a float, a float, a
                 float) or an existing file name)
                image, float or tuple of floats to act as operator

        [Optional]
        float_trait: (a float or a tuple of the form: (a float, a float, a
                 float))
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        operation: ('sum' or 'sub' or 'mul' or 'div', nipype default value:
                 sum)
                operation to be performed
        out_file: (a file name, nipype default value: warped_surf.vtk)
                vtk with surface warped
        out_warp: (a file name, nipype default value: warp_maths.vtk)
                vtk file based on in_surf and warpings mapping it to out_file

Outputs::

        out_file: (an existing file name)
                vtk with surface warped
        out_warp: (an existing file name)
                vtk file with the vertex-wise mapping of surface1 to surface2

.. _nipype.algorithms.mesh.P2PDistance:


.. index:: P2PDistance

P2PDistance
-----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/algorithms/mesh.py#L434>`__

Calculates a point-to-point (p2p) distance between two corresponding
VTK-readable meshes or contours.

A point-to-point correspondence between nodes is required

.. deprecated:: 1.0-dev
   Use :py:class:`ComputeMeshWarp` instead.

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
        metric: ('euclidean' or 'sqeuclidean', nipype default value:
                 euclidean)
                norm used to report distance
        out_file: (a file name, nipype default value: distance.npy)
                numpy file keeping computed distances and weights
        out_warp: (a file name, nipype default value: surfwarp.vtk)
                vtk file based on surface1 and warpings mapping it to surface2
        weighting: ('none' or 'area', nipype default value: none)
                "none": no weighting is performed, surface": edge distance is
                weighted by the corresponding surface area

Outputs::

        distance: (a float)
                computed distance
        out_file: (an existing file name)
                numpy file keeping computed distances and weights
        out_warp: (an existing file name)
                vtk file with the vertex-wise mapping of surface1 to surface2

.. _nipype.algorithms.mesh.WarpPoints:


.. index:: WarpPoints

WarpPoints
----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/algorithms/mesh.py#L44>`__

Applies a displacement field to a point set given in vtk format.
Any discrete deformation field, given in physical coordinates and
which volume covers the extent of the vtk point set, is a valid
``warp`` file. FSL interfaces are compatible, for instance any
field computed with :class:`nipype.interfaces.fsl.utils.ConvertWarp`.

Example
~~~~~~~

>>> from nipype.algorithms.mesh import WarpPoints
>>> wp = WarpPoints()
>>> wp.inputs.points = 'surf1.vtk'
>>> wp.inputs.warp = 'warpfield.nii'
>>> res = wp.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        interp: ('cubic' or 'nearest' or 'linear', nipype default value:
                 cubic)
                interpolation
        points: (an existing file name)
                file containing the point set
        warp: (an existing file name)
                dense deformation field to be applied

        [Optional]
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        out_points: (a file name)
                the warped point set

Outputs::

        out_points: (a file name)
                the warped point set
