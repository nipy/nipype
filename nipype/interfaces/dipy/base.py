"""Base interfaces for dipy"""

import os.path as op
import inspect
from functools import partial
import numpy as np
from ..base import (
    traits,
    File,
    isdefined,
    LibraryBaseInterface,
    BaseInterfaceInputSpec,
    TraitedSpec,
)

# List of workflows to ignore
SKIP_WORKFLOWS_LIST = ["Workflow", "CombinedWorkflow"]

HAVE_DIPY = True

try:
    import dipy
    from dipy.workflows.base import IntrospectiveArgumentParser
except ImportError:
    HAVE_DIPY = False


def no_dipy():
    """Check if dipy is available."""
    global HAVE_DIPY
    return not HAVE_DIPY


def dipy_version():
    """Check dipy version."""
    if no_dipy():
        return None

    return dipy.__version__


class DipyBaseInterface(LibraryBaseInterface):
    """A base interface for py:mod:`dipy` computations."""

    _pkg = "dipy"


class DipyBaseInterfaceInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc=("input diffusion data"))
    in_bval = File(exists=True, mandatory=True, desc=("input b-values table"))
    in_bvec = File(exists=True, mandatory=True, desc=("input b-vectors table"))
    b0_thres = traits.Int(700, usedefault=True, desc=("b0 threshold"))
    out_prefix = traits.Str(desc=("output prefix for file names"))


class DipyDiffusionInterface(DipyBaseInterface):
    """A base interface for py:mod:`dipy` computations."""

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
        if fext == ".gz":
            fname, fext2 = op.splitext(fname)
            fext = fext2 + fext

        if not isdefined(self.inputs.out_prefix):
            out_prefix = op.abspath(fname)
        else:
            out_prefix = self.inputs.out_prefix

        if ext is None:
            ext = fext

        return out_prefix + "_" + name + ext


def get_default_args(func):
    """Return optional arguments of a function.

    Parameters
    ----------
    func: callable

    Returns
    -------
    dict

    """
    signature = inspect.signature(func)
    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }


def convert_to_traits_type(dipy_type, is_file=False):
    """Convert DIPY type to Traits type."""
    dipy_type = dipy_type.lower()
    is_mandatory = bool("optional" not in dipy_type)
    if "variable" in dipy_type and "str" in dipy_type:
        return partial(traits.List, traits.Str), is_mandatory
    elif "variable" in dipy_type and "int" in dipy_type:
        return partial(traits.List, traits.Int), is_mandatory
    elif "variable" in dipy_type and "float" in dipy_type:
        return partial(traits.List, traits.Float), is_mandatory
    elif "variable" in dipy_type and "bool" in dipy_type:
        return partial(traits.List, traits.Bool), is_mandatory
    elif "variable" in dipy_type and "complex" in dipy_type:
        return partial(traits.List, traits.Complex), is_mandatory
    elif "str" in dipy_type and not is_file:
        return traits.Str, is_mandatory
    elif "str" in dipy_type and is_file:
        return File, is_mandatory
    elif "int" in dipy_type:
        return traits.Int, is_mandatory
    elif "float" in dipy_type:
        return traits.Float, is_mandatory
    elif "bool" in dipy_type:
        return traits.Bool, is_mandatory
    elif "complex" in dipy_type:
        return traits.Complex, is_mandatory
    else:
        msg = f"Error during convert_to_traits_type({dipy_type}). Unknown DIPY type."
        raise OSError(msg)


def create_interface_specs(class_name, params=None, BaseClass=TraitedSpec):
    """Create IN/Out interface specifications dynamically.

    Parameters
    ----------
    class_name: str
        The future class name(e.g, (MyClassInSpec))
    params: list of tuple
        dipy argument list
    BaseClass: TraitedSpec object
        parent class

    Returns
    -------
    newclass: object
        new nipype interface specification class

    """
    attr = {}
    if params is not None:
        for p in params:
            name, dipy_type, desc = p[0], p[1], p[2]
            is_file = bool("files" in name or "out_" in name)
            traits_type, is_mandatory = convert_to_traits_type(dipy_type, is_file)
            # print(name, dipy_type, desc, is_file, traits_type, is_mandatory)
            if BaseClass.__name__ == BaseInterfaceInputSpec.__name__:
                if len(p) > 3 and p[3] is not None:
                    default_value = p[3]
                    if isinstance(traits_type, traits.List) and not isinstance(
                        default_value, list
                    ):
                        default_value = [default_value]
                    attr[name] = traits_type(
                        default_value,
                        desc=desc[-1],
                        usedefault=True,
                        mandatory=is_mandatory,
                    )
                else:
                    attr[name] = traits_type(desc=desc[-1], mandatory=is_mandatory)
            else:
                attr[name] = traits_type(
                    p[3], desc=desc[-1], exists=True, usedefault=True
                )

    newclass = type(str(class_name), (BaseClass,), attr)
    return newclass


def dipy_to_nipype_interface(cls_name, dipy_flow, BaseClass=DipyBaseInterface):
    """Construct a class in order to respect nipype interface specifications.

    This convenient class factory convert a DIPY Workflow to a nipype
    interface.

    Parameters
    ----------
    cls_name: string
        new class name
    dipy_flow: Workflow class type.
        It should be any children class of `dipy.workflows.workflow.Workflow`
    BaseClass: object
        nipype instance object

    Returns
    -------
    newclass: object
        new nipype interface specification class

    """
    parser = IntrospectiveArgumentParser()
    flow = dipy_flow()
    parser.add_workflow(flow)
    default_values = list(get_default_args(flow.run).values())
    optional_params = [
        args + (val,) for args, val in zip(parser.optional_parameters, default_values)
    ]
    start = len(parser.optional_parameters) - len(parser.output_parameters)

    output_parameters = [
        args + (val,)
        for args, val in zip(parser.output_parameters, default_values[start:])
    ]
    input_parameters = parser.positional_parameters + optional_params

    input_spec = create_interface_specs(
        f"{cls_name}InputSpec",
        input_parameters,
        BaseClass=BaseInterfaceInputSpec,
    )

    output_spec = create_interface_specs(
        f"{cls_name}OutputSpec", output_parameters, BaseClass=TraitedSpec
    )

    def _run_interface(self, runtime):
        flow = dipy_flow()
        args = self.inputs.get()
        flow.run(**args)

    def _list_outputs(self):
        outputs = self._outputs().get()
        out_dir = outputs.get("out_dir", ".")
        for key, values in outputs.items():
            outputs[key] = op.join(out_dir, values)

        return outputs

    newclass = type(
        str(cls_name),
        (BaseClass,),
        {
            "input_spec": input_spec,
            "output_spec": output_spec,
            "_run_interface": _run_interface,
            "_list_outputs:": _list_outputs,
        },
    )
    return newclass


def get_dipy_workflows(module):
    """Search for DIPY workflow class.

    Parameters
    ----------
    module : object
        module object

    Returns
    -------
    l_wkflw : list of tuple
        This a list of tuple containing 2 elements:
        Workflow name, Workflow class obj

    Examples
    --------
    >>> from dipy.workflows import align  # doctest: +SKIP
    >>> get_dipy_workflows(align)  # doctest: +SKIP

    """
    return [
        (m, obj)
        for m, obj in inspect.getmembers(module)
        if inspect.isclass(obj)
        and issubclass(obj, module.Workflow)
        and m not in SKIP_WORKFLOWS_LIST
    ]
