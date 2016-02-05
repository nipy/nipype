# -*- coding: utf-8 -*-
"""
Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)
"""
import os.path as op
import warnings

import nibabel as nb
import nibabel.trackvis as nbt

from ..base import (TraitedSpec, BaseInterface, BaseInterfaceInputSpec,
                    File, isdefined, traits)
from ...utils.filemanip import split_filename
from ...utils.misc import package_check
from ... import logging
iflogger = logging.getLogger('interface')

have_dipy = True
try:
    package_check('dipy', version='0.6.0')
except Exception as e:
    have_dipy = False
else:
    from dipy.tracking.utils import density_map


class TrackDensityMapInputSpec(TraitedSpec):
    in_file = File(exists=True, mandatory=True,
                   desc='The input TrackVis track file')
    reference = File(exists=True,
                     desc='A reference file to define RAS coordinates space')
    points_space = traits.Enum('rasmm', 'voxel', None, usedefault=True,
                               desc='coordinates of trk file')

    voxel_dims = traits.List(traits.Float, minlen=3, maxlen=3,
                             desc='The size of each voxel in mm.')
    data_dims = traits.List(traits.Int, minlen=3, maxlen=3,
                            desc='The size of the image in voxels.')
    out_filename = File('tdi.nii', usedefault=True,
                        desc=('The output filename for the tracks in TrackVis '
                              '(.trk) format'))


class TrackDensityMapOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class TrackDensityMap(BaseInterface):

    """
    Creates a tract density image from a TrackVis track file using functions
    from dipy


    Example
    -------

    >>> import nipype.interfaces.dipy as dipy
    >>> trk2tdi = dipy.TrackDensityMap()
    >>> trk2tdi.inputs.in_file = 'converted.trk'
    >>> trk2tdi.run()                                   # doctest: +SKIP

    """
    input_spec = TrackDensityMapInputSpec
    output_spec = TrackDensityMapOutputSpec

    def _run_interface(self, runtime):
        from numpy import min_scalar_type
        tracks, header = nbt.read(self.inputs.in_file)
        streams = ((ii[0]) for ii in tracks)

        if isdefined(self.inputs.reference):
            refnii = nb.load(self.inputs.reference)
            affine = refnii.affine
            data_dims = refnii.shape[:3]
            kwargs = dict(affine=affine)
        else:
            iflogger.warn(('voxel_dims and data_dims are deprecated'
                           'as of dipy 0.7.1. Please use reference '
                           'input instead'))

            if not isdefined(self.inputs.data_dims):
                data_dims = header['dim']
            else:
                data_dims = self.inputs.data_dims
            if not isdefined(self.inputs.voxel_dims):
                voxel_size = header['voxel_size']
            else:
                voxel_size = self.inputs.voxel_dims

            affine = header['vox_to_ras']
            kwargs = dict(voxel_size=voxel_size)

        data = density_map(streams, data_dims, **kwargs)
        data = data.astype(min_scalar_type(data.max()))
        img = nb.Nifti1Image(data, affine)
        out_file = op.abspath(self.inputs.out_filename)
        nb.save(img, out_file)

        iflogger.info(
            ('Track density map saved as {i}, size={d}, '
             'dimensions={v}').format(i=out_file, d=img.shape,
                                      v=img.header.get_zooms()))
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = op.abspath(self.inputs.out_filename)
        return outputs
