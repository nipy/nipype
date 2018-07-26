# -*- coding: utf-8 -*-
""" Base interfaces for dipy """
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import os.path as op
import numpy as np
from ... import logging
from ..base import (traits, File, isdefined, LibraryBaseInterface,
                    BaseInterfaceInputSpec)

HAVE_DIPY = True
try:
    import dipy
except ImportError:
    HAVE_DIPY = False


def no_dipy():
    """ Check if dipy is available """
    global HAVE_DIPY
    return not HAVE_DIPY


def dipy_version():
    """ Check dipy version """
    if no_dipy():
        return None

    return dipy.__version__


class DipyBaseInterface(LibraryBaseInterface):
    """
    A base interface for py:mod:`dipy` computations
    """
    _pkg = 'dipy'


class DipyBaseInterfaceInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc=('input diffusion data'))
    in_bval = File(exists=True, mandatory=True, desc=('input b-values table'))
    in_bvec = File(exists=True, mandatory=True, desc=('input b-vectors table'))
    b0_thres = traits.Int(700, usedefault=True, desc=('b0 threshold'))
    out_prefix = traits.Str(desc=('output prefix for file names'))


class DipyDiffusionInterface(DipyBaseInterface):
    """
    A base interface for py:mod:`dipy` computations
    """
    input_spec = DipyBaseInterfaceInputSpec

    def _get_gradient_table(self):
        bval = np.loadtxt(self.inputs.in_bval)
        bvec = np.loadtxt(self.inputs.in_bvec).T
        from dipy.core.gradients import gradient_table
        gtab = gradient_table(bval, bvec)

        gtab.b0_threshold = self.inputs.b0_thres
        return gtab

    def _gen_filename(self, name, ext=None):
        fname, fext = op.splitext(op.basename(self.inputs.in_file))
        if fext == '.gz':
            fname, fext2 = op.splitext(fname)
            fext = fext2 + fext

        if not isdefined(self.inputs.out_prefix):
            out_prefix = op.abspath(fname)
        else:
            out_prefix = self.inputs.out_prefix

        if ext is None:
            ext = fext

        return out_prefix + '_' + name + ext
