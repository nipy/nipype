# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
'''
Miscellaneous algorithms for 2D contours and 3D triangularized meshes handling

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
    >>> os.chdir(datadir)

'''


import numpy as np
from scipy.spatial.distance import euclidean

from .. import logging

from ..interfaces.base import (BaseInterface, traits, TraitedSpec, File,
                               BaseInterfaceInputSpec)
iflogger = logging.getLogger('interface')


class WarpPointsInputSpec(BaseInterfaceInputSpec):
    points = File(exists=True, mandatory=True,
                  desc=('file containing the point set'))
    warp = File(exists=True, mandatory=True,
                desc=('dense deformation field to be applied'))
    interp = traits.Enum('cubic', 'nearest', 'linear', usedefault=True,
                         mandatory=True, desc='interpolation')
    out_points = File(name_source='points', name_template='%s_warped',
                      output_name='out_points', keep_extension=True,
                      desc='the warped point set')

class WarpPointsOutputSpec(TraitedSpec):
    out_points = File(desc='the warped point set')

class WarpPoints(BaseInterface):
    """
    Applies a warp field to a point set in vtk
    """
    input_spec = WarpPointsInputSpec
    output_spec = WarpPointsOutputSpec

    def _overload_extension(self, value, name):
        return value + '.vtk'

    def _run_interface(self, runtime):
        from tvtk.api import tvtk
        import nibabel as nb
        import numpy as np
        from scipy import ndimage

        r = tvtk.PolyDataReader(file_name=self.inputs.points)
        r.update()
        mesh = r.output
        points = np.array(mesh.points)
        warp_dims = nb.funcs.four_to_three(nb.load(self.inputs.warp))

        affine = warp_dims[0].get_affine()
        voxsize = warp_dims[0].get_header().get_zooms()
        R = np.linalg.inv(affine[0:3,0:3])
        origin = affine[0:3,3]
        points = points - origin[np.newaxis,:]
        points = np.array([np.dot(R,p) for p in points])

        warps = []
        for axis in warp_dims:
            wdata = axis.get_data()
            if np.any(wdata!=0):
                warps.append([ndimage.map_coordinates(wdata, points.transpose())])
            else:
                warps.append([np.zeros((points.shape[0],))])
        warps = np.squeeze(np.array(warps)).reshape(-1,3)
        print warps.shape
        print points.shape

        newpoints = [ p + d for p,d in zip(points, warps)]
        mesh.points = newpoints
        w = tvtk.PolyDataWriter(input=mesh)
        w.file_name = self._filename_from_source('out_points')
        w.write()

        return runtime

class P2PDistanceInputSpec(BaseInterfaceInputSpec):
    surface1 = File(exists=True, mandatory=True,
                    desc=("Reference surface (vtk format) to which compute "
                          "distance."))
    surface2 = File(exists=True, mandatory=True,
                    desc=("Test surface (vtk format) from which compute "
                          "distance."))
    weighting = traits.Enum("none", "surface", usedefault=True,
                            desc=('"none": no weighting is performed, '
                                  '"surface": edge distance is weighted by the '
                                  'corresponding surface area'))

class P2PDistanceOutputSpec(TraitedSpec):
    distance = traits.Float(desc="computed distance")

class P2PDistance(BaseInterface):
    """Calculates a point-to-point (p2p) distance between two corresponding
    VTK-readable meshes or contours.

    A point-to-point correspondence between nodes is required

    Example
    -------

    >>> import nipype.algorithms.mesh as mesh
    >>> dist = mesh.P2PDistance()
    >>> dist.inputs.surface1 = 'surf1.vtk'
    >>> dist.inputs.surface2 = 'surf2.vtk'
    >>> res = dist.run() # doctest: +SKIP
    """

    input_spec = P2PDistanceInputSpec
    output_spec = P2PDistanceOutputSpec

    def _triangle_area(self, A, B, C):
        ABxAC = euclidean(A,B) *  euclidean(A,C)
        prod = np.dot(np.array(B)-np.array(A),np.array(C)-np.array(A))
        angle = np.arccos( prod / ABxAC )
        area = 0.5 * ABxAC * np.sin( angle )
        return area

    def _run_interface(self, runtime):
        from tvtk.api import tvtk
        r1 = tvtk.PolyDataReader( file_name=self.inputs.surface1 )
        r2 = tvtk.PolyDataReader( file_name=self.inputs.surface2 )
        vtk1 = r1.output
        vtk2 = r2.output
        r1.update()
        r2.update()
        assert( len(vtk1.points) == len(vtk2.points) )
        d = 0.0
        totalWeight = 0.0

        points = vtk1.points
        faces = vtk1.polys.to_array().reshape(-1,4).astype(int)[:,1:]

        for p1,p2 in zip( points, vtk2.points ):
            weight = 1.0
            if (self.inputs.weighting == 'surface'):
                #compute surfaces, set in weight
                weight = 0.0
                point_faces = faces[ (faces[:,:]==0).any(axis=1) ]

                for idset in point_faces:
                    p1 = points[ int(idset[0]) ]
                    p2 = points[ int(idset[1]) ]
                    p3 = points[ int(idset[2]) ]
                    weight = weight + self._triangle_area(p1, p2, p3)

            d+= weight*euclidean( p1, p2 )
            totalWeight = totalWeight + weight

        self._distance = d / totalWeight
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['distance'] = self._distance
        return outputs

