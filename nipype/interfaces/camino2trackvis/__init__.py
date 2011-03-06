# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Camino2Trackvis top level namespace
"""

from nipype.interfaces.camino2trackvis.base import Camino2TrackvisCommand, Camino2TrackvisCommandInputSpec
from nipype.interfaces.camino2trackvis.convert import Camino2Trackvis, Trackvis2Camino
import nose


def setup():
    print 'camino2trackvis setup test'

def teardown():
    print 'camino2trackvis teardown test'
