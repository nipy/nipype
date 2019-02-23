import pytest
from collections import namedtuple
from ...base import traits, TraitedSpec, BaseInterfaceInputSpec
from ..base import (convert_to_traits_type, create_interface_specs,
                    dipy_to_nipype_interface, DipyBaseInterface, no_dipy)


def test_convert_to_traits_type():
    Params = namedtuple("Params", "traits_type is_file")
    Res = namedtuple("Res", "traits_type is_mandatory")
    l_entries = [Params('variable string', False),
                 Params('variable int', False),
                 Params('variable float', False),
                 Params('variable bool', False),
                 Params('variable complex', False),
                 Params('variable int, optional', False),
                 Params('variable string, optional', False),
                 Params('variable float, optional', False),
                 Params('variable bool, optional', False),
                 Params('variable complex, optional', False),
                 Params('string', False), Params('int', False),
                 Params('string', True), Params('float', False),
                 Params('bool', False), Params('complex', False),
                 Params('string, optional', False),
                 Params('int, optional', False),
                 Params('string, optional', True),
                 Params('float, optional', False),
                 Params('bool, optional', False),
                 Params('complex, optional', False),
                 ]
    l_expected = [Res(traits.ListStr, True), Res(traits.ListInt, True),
                  Res(traits.ListFloat, True), Res(traits.ListBool, True),
                  Res(traits.ListComplex, True), Res(traits.ListInt, False),
                  Res(traits.ListStr, False), Res(traits.ListFloat, False),
                  Res(traits.ListBool, False), Res(traits.ListComplex, False),
                  Res(traits.Str, True), Res(traits.Int, True),
                  Res(traits.File, True), Res(traits.Float, True),
                  Res(traits.Bool, True), Res(traits.Complex, True),
                  Res(traits.Str, False), Res(traits.Int, False),
                  Res(traits.File, False), Res(traits.Float, False),
                  Res(traits.Bool, False), Res(traits.Complex, False),
                  ]

    for entry, res in zip(l_entries, l_expected):
        traits_type, is_mandatory = convert_to_traits_type(entry.traits_type,
                                                           entry.is_file)
        assert traits_type == res.traits_type
        assert is_mandatory == res.is_mandatory

    with pytest.raises(IOError):
        convert_to_traits_type("file, optional")


def test_create_interface_specs():
    new_interface = create_interface_specs("MyInterface")

    assert new_interface.__base__ == TraitedSpec
    assert isinstance(new_interface(), TraitedSpec)
    assert new_interface.__name__ == "MyInterface"
    assert not new_interface().get()

    new_interface = create_interface_specs("MyInterface",
                                           BaseClass=BaseInterfaceInputSpec)
    assert new_interface.__base__ == BaseInterfaceInputSpec
    assert isinstance(new_interface(), BaseInterfaceInputSpec)
    assert new_interface.__name__ == "MyInterface"
    assert not new_interface().get()

    params = [("params1", "string", ["my description"]), ("params2_files", "string", ["my description @"]),
              ("params3", "int, optional", ["useful option"]), ("out_params", "string", ["my out description"])]

    new_interface = create_interface_specs("MyInterface", params=params,
                                           BaseClass=BaseInterfaceInputSpec)

    assert new_interface.__base__ == BaseInterfaceInputSpec
    assert isinstance(new_interface(), BaseInterfaceInputSpec)
    assert new_interface.__name__ == "MyInterface"
    current_params = new_interface().get()
    assert len(current_params) == 4
    assert 'params1' in current_params.keys()
    assert 'params2_files' in current_params.keys()
    assert 'params3' in current_params.keys()
    assert 'out_params' in current_params.keys()


@pytest.mark.skipif(no_dipy(), reason="DIPY is not installed")
def test_dipy_to_nipype_interface():
    from dipy.workflows.workflow import Workflow

    class DummyWorkflow(Workflow):

        @classmethod
        def get_short_name(cls):
            return 'dwf1'

        def run(self, in_files, param1=1, out_dir='', out_ref='out1.txt'):
            """Workflow used to test basic workflows.

            Parameters
            ----------
            in_files : string
                fake input string param
            param1 : int, optional
                fake positional param (default 1)
            out_dir : string, optional
                fake output directory (default '')
            out_ref : string, optional
                fake out file (default out1.txt)

            References
            -----------
            dummy references

            """
            return param1

    new_specs = dipy_to_nipype_interface("MyModelSpec", DummyWorkflow)
    assert new_specs.__base__ == DipyBaseInterface
    assert isinstance(new_specs(), DipyBaseInterface)
    assert new_specs.__name__ == "MyModelSpec"
    assert hasattr(new_specs, 'input_spec')
    assert new_specs().input_spec.__base__ == BaseInterfaceInputSpec
    assert hasattr(new_specs, 'output_spec')
    assert new_specs().output_spec.__base__ == TraitedSpec
    assert hasattr(new_specs, '_run_interface')
    assert hasattr(new_specs, '_list_outputs')
    params_in = new_specs().inputs.get()
    params_out = new_specs()._outputs().get()
    assert len(params_in) == 4
    assert 'in_files' in params_in.keys()
    assert 'param1' in params_in.keys()
    assert 'out_dir' in params_out.keys()
    assert 'out_ref' in params_out.keys()

    with pytest.raises(ValueError):
        new_specs().run()


if __name__ == "__main__":
    test_convert_to_traits_type()
    test_create_interface_specs()
    test_dipy_to_nipype_interface()
