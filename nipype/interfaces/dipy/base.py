# -*- coding: utf-8 -*-
import numpy as np
import os.path as op
from nipype.interfaces.base import (traits, File, isdefined,
                                    BaseInterface, BaseInterfaceInputSpec)


class DipyBaseInterfaceInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc=('input diffusion data'))
    in_bval = File(exists=True, mandatory=True, desc=('input b-values table'))
    in_bvec = File(exists=True, mandatory=True, desc=('input b-vectors table'))
    b0_thres = traits.Int(700, usedefault=True, desc=('b0 threshold'))
    out_prefix = traits.Str(desc=('output prefix for file names'))


class DipyBaseInterface(BaseInterface):

    """
    A base interface for py:mod:`dipy` computations
    """
    input_spec = DipyBaseInterfaceInputSpec

    def _get_gradient_table(self):
        bval = np.loadtxt(self.inputs.in_bval)
        bvec = np.loadtxt(self.inputs.in_bvec).T
        try:
            from dipy.data import GradientTable
            gtab = GradientTable(bvec)
            gtab.bvals = bval
        except NameError:
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
