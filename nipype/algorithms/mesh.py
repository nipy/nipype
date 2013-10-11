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


import os
import os.path as op
import warnings
import nibabel as nb
import numpy as np
from scipy.spatial.distance import euclidean
from nipype.utils.misc import package_check

try:
    package_check('tvtk')
except Exception, e:
    warnings.warn('tvtk or vtk not installed')
else:
    from tvtk.api import tvtk


from .. import logging

from ..interfaces.base import (BaseInterface, traits, TraitedSpec, File,
                               InputMultiPath, OutputMultiPath,
                               BaseInterfaceInputSpec, isdefined)
from ..utils.filemanip import fname_presuffix, split_filename
iflogger = logging.getLogger('interface')


class P2PDistanceInputSpec(BaseInterfaceInputSpec):
    surface1 = File(exists=True, mandatory=True,
                    desc="Reference surface (vtk format) to which compute distance.")
    surface2 = File(exists=True, mandatory=True,
                    desc="Test surface (vtk format) from which compute distance.")
    weighting = traits.Enum("none", "surface", desc='""none": no weighting is performed\
                            "surface": edge distance is weighted by the corresponding surface area',usedefault=True)

class P2PDistanceOutputSpec(TraitedSpec):
    distance = traits.Float(desc="computed distance")

class P2PDistance(BaseInterface):
    """
    Calculates a point-to-point (p2p) distance between two corresponding meshes or contours.
    Therefore, a point-to-point correspondence between nodes is required

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
    
