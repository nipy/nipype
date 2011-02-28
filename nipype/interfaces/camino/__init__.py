# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Camino top level namespace
"""

from nipype.interfaces.camino.base import CaminoCommand, CaminoCommandInputSpec
from nipype.interfaces.camino.pythome import fsl2scheme, image2voxel, dtfit, track, procstreamlines, vtkstreamlines, conmap
import nose


def setup():
    print 'camino setup test'

def teardown():
    print 'camino teardown test'
