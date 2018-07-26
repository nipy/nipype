# -*- coding: utf-8 -*-
"""
Provides interfaces to various commands provided by Camino-Trackvis
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import os

from ...utils.filemanip import split_filename
from ..base import CommandLineInputSpec, CommandLine, traits, TraitedSpec, File


class Camino2TrackvisInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr='-i %s',
        mandatory=True,
        position=1,
        desc='The input .Bfloat (camino) file.')

    out_file = File(
        argstr='-o %s',
        genfile=True,
        position=2,
        desc='The filename to which to write the .trk (trackvis) file.')

    min_length = traits.Float(
        argstr='-l %d',
        position=3,
        units='mm',
        desc='The minimum length of tracts to output')

    data_dims = traits.List(
        traits.Int,
        argstr='-d %s',
        sep=',',
        mandatory=True,
        position=4,
        minlen=3,
        maxlen=3,
        desc=
        'Three comma-separated integers giving the number of voxels along each dimension of the source scans.'
    )

    voxel_dims = traits.List(
        traits.Float,
        argstr='-x %s',
        sep=',',
        mandatory=True,
        position=5,
        minlen=3,
        maxlen=3,
        desc=
        'Three comma-separated numbers giving the size of each voxel in mm.')

    # Change to enum with all combinations? i.e. LAS, LPI, RAS, etc..
    voxel_order = File(
        argstr='--voxel-order %s',
        mandatory=True,
        position=6,
        desc='Set the order in which various directions were stored.\
        Specify with three letters consisting of one each  \
        from the pairs LR, AP, and SI. These stand for Left-Right, \
        Anterior-Posterior, and Superior-Inferior.  \
        Whichever is specified in each position will  \
        be the direction of increasing order.  \
        Read coordinate system from a NIfTI file.')

    nifti_file = File(
        argstr='--nifti %s',
        exists=True,
        position=7,
        desc='Read coordinate system from a NIfTI file.')


class Camino2TrackvisOutputSpec(TraitedSpec):
    trackvis = File(
        exists=True,
        desc='The filename to which to write the .trk (trackvis) file.')


class Camino2Trackvis(CommandLine):
    """ Wraps camino_to_trackvis from Camino-Trackvis

    Convert files from camino .Bfloat format to trackvis .trk format.

    Example
    -------

    >>> import nipype.interfaces.camino2trackvis as cam2trk
    >>> c2t = cam2trk.Camino2Trackvis()
    >>> c2t.inputs.in_file = 'data.Bfloat'
    >>> c2t.inputs.out_file = 'streamlines.trk'
    >>> c2t.inputs.min_length = 30
    >>> c2t.inputs.data_dims = [128, 104, 64]
    >>> c2t.inputs.voxel_dims = [2.0, 2.0, 2.0]
    >>> c2t.inputs.voxel_order = 'LAS'
    >>> c2t.run()                  # doctest: +SKIP
    """

    _cmd = 'camino_to_trackvis'
    input_spec = Camino2TrackvisInputSpec
    output_spec = Camino2TrackvisOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['trackvis'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + '.trk'


class Trackvis2CaminoInputSpec(CommandLineInputSpec):
    """ Wraps trackvis_to_camino from Camino-Trackvis

    Convert files from camino .Bfloat format to trackvis .trk format.

    Example
    -------

    >>> import nipype.interfaces.camino2trackvis as cam2trk
    >>> t2c = cam2trk.Trackvis2Camino()
    >>> t2c.inputs.in_file = 'streamlines.trk'
    >>> t2c.inputs.out_file = 'streamlines.Bfloat'
    >>> t2c.run()                  # doctest: +SKIP
    """

    in_file = File(
        exists=True,
        argstr='-i %s',
        mandatory=True,
        position=1,
        desc='The input .trk (trackvis) file.')

    out_file = File(
        argstr='-o %s',
        genfile=True,
        position=2,
        desc='The filename to which to write the .Bfloat (camino).')

    append_file = File(
        exists=True,
        argstr='-a %s',
        position=2,
        desc='A file to which the append the .Bfloat data. ')


class Trackvis2CaminoOutputSpec(TraitedSpec):
    camino = File(
        exists=True,
        desc='The filename to which to write the .Bfloat (camino).')


class Trackvis2Camino(CommandLine):
    _cmd = 'trackvis_to_camino'
    input_spec = Trackvis2CaminoInputSpec
    output_spec = Trackvis2CaminoOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['camino'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + '.Bfloat'
