# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
# changing to temporary directories
    >>> tmp = getfixture('tmpdir')
    >>> old = tmp.chdir()
"""

from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

from future import standard_library
standard_library.install_aliases()

from builtins import str, bytes

from ... import logging
from ..base import (traits, DynamicTraitedSpec, Undefined, isdefined,
                    BaseInterfaceInputSpec)
from ..io import IOBase, add_traits
from ...utils.filemanip import ensure_list
from ...utils.functions import getsource, create_function_from_source

iflogger = logging.getLogger('interface')


def _get_varnames(func):
    """Return list of names of arguments to a function

    Parameters
    ----------
    func: callable, string or Undefined
        Function or source code of function to query

    Returns
    -------
    varnames: list of str
        Names of arguments to passed function (empty if undefined)
    """
    if not isdefined(func):
        return []
    if isinstance(func, (str, bytes)):
        func = create_function_from_source(func)
    fninfo = func.__code__
    return fninfo.co_varnames[:fninfo.co_argcount]


class CheckHidden(traits.TraitType):
    """Trait that allows a class to decide whether it may be set"""
    def __init__(self, interface):
        super(CheckHidden, self).__init__()
        self._interface = interface

    def validate(self, obj, name, value):
        msg = self._interface.check_hidden(name)
        if msg is not None:
            raise traits.TraitError(msg)
        return value


class FunctionInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):
    function_str = traits.Str(mandatory=True, desc='code for function')


class Function(IOBase):
    """Runs arbitrary function as an interface

    Examples
    --------

    >>> func = 'def func(arg1, arg2=5): return arg1 + arg2'
    >>> fi = Function(input_names=['arg1', 'arg2'], output_names=['out'])
    >>> fi.inputs.function_str = func
    >>> res = fi.run(arg1=1)
    >>> res.outputs.out
    6

    """

    input_spec = FunctionInputSpec
    output_spec = DynamicTraitedSpec

    def __init__(self,
                 input_names=None,
                 output_names='out',
                 function=None,
                 imports=None,
                 **inputs):
        """

        Parameters
        ----------

        input_names: single str or list or None
            names corresponding to function inputs
            if ``None``, derive input names from function argument names
        output_names: single str or list
            names corresponding to function outputs (default: 'out').
            if list of length > 1, has to match the number of outputs
        function : callable
            callable python object. must be able to execute in an
            isolated namespace (possibly in concert with the ``imports``
            parameter)
        imports : list of strings
            list of import statements that allow the function to execute
            in an otherwise empty namespace
        """

        super(Function, self).__init__(**inputs)
        if function:
            if hasattr(function, '__call__'):
                try:
                    self.inputs.function_str = getsource(function)
                except IOError:
                    raise Exception('Interface Function does not accept '
                                    'function objects defined interactively '
                                    'in a python session')
            elif isinstance(function, (str, bytes)):
                self.inputs.function_str = function
            else:
                raise Exception('Unknown type of function')
        self.inputs.on_trait_change(self._set_function_string, 'function_str')

        if input_names is None:
            input_names = _get_varnames(self.inputs.function_str)
        self._input_names = ensure_list(input_names)
        self._output_names = ensure_list(output_names)
        add_traits(self.inputs, [name for name in self._input_names])
        self.imports = imports
        self._out = {}
        for name in self._output_names:
            self._out[name] = None

        # If parameters with default values are not listed in input_names,
        # they are not passed to the function.
        # This preempts their setting, inserting a trait just in time that
        # will warn users that it cannot be set.
        # A dynamically-validating trait is used to ensure that changes to
        # the function string can re-enable fields
        self.inputs.on_trait_change(self._disallow_hidden, 'trait_added')

    def _disallow_hidden(self, obj, name, new):
        obj.add_trait(new, CheckHidden(self))

    def check_hidden(self, name):
        all_vars = _get_varnames(self.inputs.function_str)
        hidden = set(all_vars) - set(self._input_names)
        if name in hidden:
            return ("The '{name}' trait cannot be set on this {cls} because "
                    "the '{name}' argument was not included in 'input_names'."
                    "".format(name=name, cls=self.inputs.__class__.__name__))

    def _set_function_string(self, obj, name, old, new):
        if name == 'function_str':
            if hasattr(new, '__call__'):
                function_source = getsource(new)
            elif isinstance(new, (str, bytes)):
                function_source = new
            self.inputs.trait_set(
                trait_change_notify=False, **{
                    '%s' % name: function_source
                })
            # Update input traits
            input_names = _get_varnames(new)
            new_names = set(input_names) - set(self._input_names)
            add_traits(self.inputs, list(new_names))
            self._input_names.extend(new_names)

    def _add_output_traits(self, base):
        undefined_traits = {}
        for key in self._output_names:
            base.add_trait(key, traits.Any)
            undefined_traits[key] = Undefined
        base.trait_set(trait_change_notify=False, **undefined_traits)
        return base

    def _run_interface(self, runtime):
        # Create function handle
        function_handle = create_function_from_source(self.inputs.function_str,
                                                      self.imports)
        # Get function args
        args = {}
        for name in self._input_names:
            value = getattr(self.inputs, name)
            if isdefined(value):
                args[name] = value

        out = function_handle(**args)
        if len(self._output_names) == 1:
            self._out[self._output_names[0]] = out
        else:
            if isinstance(out, tuple) and \
                    (len(out) != len(self._output_names)):
                raise RuntimeError('Mismatch in number of expected outputs')

            else:
                for idx, name in enumerate(self._output_names):
                    self._out[name] = out[idx]

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        for key in self._output_names:
            outputs[key] = self._out[key]
        return outputs
