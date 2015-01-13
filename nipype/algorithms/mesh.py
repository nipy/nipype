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
import os.path as op
from scipy.spatial.distance import euclidean

from .. import logging

from ..interfaces.base import (BaseInterface, traits, TraitedSpec, File,
                               BaseInterfaceInputSpec)
iflogger = logging.getLogger('interface')


class P2PDistanceInputSpec(BaseInterfaceInputSpec):
    surface1 = File(exists=True, mandatory=True,
                    desc=("Reference surface (vtk format) to which compute "
                          "distance."))
    surface2 = File(exists=True, mandatory=True,
                    desc=("Test surface (vtk format) from which compute "
                          "distance."))
    weighting = traits.Enum(
        "none", "area", usedefault=True,
        desc=('"none": no weighting is performed, "area": vertex distances are'
              'weighted by the total area of faces corresponding to the '
              'vertex'))
    out_file = File('distance.npy', usedefault=True,
                    desc='numpy file keeping computed distances and weights')


class P2PDistanceOutputSpec(TraitedSpec):
    distance = traits.Float(desc="computed distance")
    out_file = File(exists=True,
                    desc='numpy file keeping computed distances and weights')


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
        ABxAC = euclidean(A, B) * euclidean(A, C)
        prod = np.dot(np.array(B) - np.array(A), np.array(C) - np.array(A))
        angle = np.arccos(prod / ABxAC)
        area = 0.5 * ABxAC * np.sin(angle)
        return area

    def _run_interface(self, runtime):
        try:
            from tvtk.api import tvtk
        except ImportError:
            raise ImportError('Interface P2PDistance requires tvtk')

        try:
            from enthought.etsconfig.api import ETSConfig
            ETSConfig.toolkit = 'null'
        except ImportError:
            iflogger.warn(('ETS toolkit could not be imported'))
            pass
        except ValueError:
            iflogger.warn(('ETS toolkit is already set'))
            pass

        r1 = tvtk.PolyDataReader(file_name=self.inputs.surface1)
        r2 = tvtk.PolyDataReader(file_name=self.inputs.surface2)
        vtk1 = r1.output
        vtk2 = r2.output
        r1.update()
        r2.update()
        assert(len(vtk1.points) == len(vtk2.points))

        points1 = np.array(vtk1.points)
        points2 = np.array(vtk2.points)

        diff = np.linalg.norm(points1 - points2, axis=1)
        weights = np.ones(len(diff))

        if (self.inputs.weighting == 'area'):
            faces = vtk1.polys.to_array().reshape(-1, 4).astype(int)[:, 1:]

            for i, p1 in enumerate(points2):
                # compute surfaces, set in weight
                w = 0.0
                point_faces = faces[(faces[:, :] == i).any(axis=1)]

                for idset in point_faces:
                    fp1 = points1[int(idset[0])]
                    fp2 = points1[int(idset[1])]
                    fp3 = points1[int(idset[2])]
                    w += self._triangle_area(fp1, fp2, fp3)
                weights[i] = w

        result = np.vstack([diff, weights])
        np.save(op.abspath(self.inputs.out_file), result.transpose())

        self._distance = np.average(diff, weights=weights)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        outputs['distance'] = self._distance
        return outputs
