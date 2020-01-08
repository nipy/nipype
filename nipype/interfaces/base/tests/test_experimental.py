"""Proof of concept."""
from ....utils.filemanip import fname_presuffix
from ... import base as nib
from ..experimental import AutoOutputInterface

_TOOL_OUTPUT = r"""\
  _____________
< Nipype rocks! >
  =============
                  \
                   \
                     ^__^
                     (oo)\_______
                     (__)\       )\/\
                         ||----w |
                         ||     ||


"""


def _parse_err_cb(in_text):
    if '3.0' in in_text:
        return 3.0
    raise RuntimeError('Failed Parsing')


class _InputSpec(nib.TraitedSpec):
    foo = nib.traits.Int(desc="a random int")
    moo = nib.traits.Int(desc="a random int", mandatory=False)
    hoo = nib.traits.Int(desc="a random int", usedefault=True)
    zoo = nib.File(desc="a file")
    woo = nib.File(desc="a file")


def test_AutoOutputInterface():
    """Proof of concept."""
    class _OutputSpec(nib.TraitedSpec):
        out_woo = nib.File('{woo}_brain', usedefault=True)
        out_std = nib.Str(stdout=True)
        out_err = nib.traits.Float(stderr=_parse_err_cb)

    class TestInterface(AutoOutputInterface):
        input_spec = _InputSpec
        output_spec = _OutputSpec

        def _run_interface(self, runtime):
            runtime.stdout = _TOOL_OUTPUT
            runtime.stderr = ' '.join(('a', 'b', '1', '2', '3.0'))
            out_fname = fname_presuffix(
                self.inputs.woo, suffix='_brain')
            open(out_fname, 'w').close()
            return runtime

    iface = TestInterface(woo='sub-001_T1w.nii.gz')
    result = iface.run()

    assert result.outputs.out_woo == 'sub-001_T1w_brain.nii.gz'
    assert 'Nipype rocks!' in result.outputs.out_std
    assert result.outputs.out_err == 3.0
