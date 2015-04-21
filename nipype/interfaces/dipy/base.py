# -*- coding: utf-8 -*-


class DipyBaseInterfaceInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc=('input diffusion data'))
    in_bval = File(exists=True, mandatory=True, desc=('input b-values table'))
    in_bvec = File(exists=True, mandatory=True, desc=('input b-vectors table'))
    out_prefix = traits.Str(desc=('output prefix for file names'))


class DipyBaseInterface(BaseInterface):

    """
    A base interface for py:mod:`dipy` computations
    """
    input_spec = DipyBaseInterfaceInputSpec

    def _get_gradient_table(self):
        gtab = GradientTable(np.loadtxt(self.inputs.in_bvec).T)
        gtab.b0_threshold = 700
        gtab.bvals = np.loadtxt(self.inputs.in_bval)
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
