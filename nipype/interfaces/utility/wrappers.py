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
from ..base import (traits, DynamicTraitedSpec, Undefined, SetOnce,
                    BaseInterfaceInputSpec)
from ..io import IOBase, add_traits
from ...utils.filemanip import ensure_list
from ...utils.functions import getsource, create_function_from_source

iflogger = logging.getLogger('nipype.interface')


try:
    from inspect import getfullargspec
except ImportError:
    def getfullargspec(func):
        from collections import namedtuple
        from inspect import getargspec
        args, varargs, keywords, defaults = getargspec(func)
        ret_t = namedtuple('FullArgSpec',
                           ('args', 'varargs', 'varkw', 'defaults',
                            'kwonlyargs', 'kwonlydefaults', 'annotations'))
        return ret_t(args, varargs, keywords, defaults, [], None, {})


def parse_function(func, input_names=None):
    """Collect Function-relevant information from a Python function

    Parameters
    ----------
    func : callable, source code of a function, or Undefined

    Returns
    -------
    arg_names : list of str
        Names of all named arguments
    default_args : dict of (str, object) pairs
        Names and default values of arguments with default values
    kwargs : {True, False}
        Name of keyword argument dictionary, if given
    """
    if isinstance(func, (str, bytes)):
        function_str = func
        func = create_function_from_source(func)
    elif hasattr(func, '__call__'):
        function_str = getsource(func)
    else:
        raise TypeError('Unknown type of function')

    argspec = getfullargspec(func)
    all_args = argspec.args + argspec.kwonlyargs
    # Arguments with defaults must occur at the end of the protocol
    all_defaults = ({} if argspec.defaults is None else
                    dict(zip(argspec.args[-len(argspec.defaults):],
                             argspec.defaults)))
    if argspec.kwonlydefaults is not None:
        all_defaults.update(argspec.kwonlydefaults)

    required_args = set(all_args) - set(all_defaults.keys())
    if input_names is None:
        input_names = all_args
    else:
        missed_args = required_args - set(input_names)
        if missed_args:
            raise ValueError('These positional arguments must be in '
                             'input names: {}'.format(', '.join(missed_args)))

        unknown = set(input_names) - set(all_args)
        if unknown:
            raise ValueError('Input names do not match function arguments: '
                             '{}'.format(', '.join(unknown)))

    banned_names = list(set(all_defaults.keys()) - set(input_names))

    return (function_str, all_args, all_defaults, banned_names,
            argspec.varkw is not None)


class FunctionInputSpec(BaseInterfaceInputSpec):
    function_str = SetOnce(traits.Str, mandatory=True,
                           desc='code for function')


class DynamicFunctionInputSpec(FunctionInputSpec):
    _ = traits.Any()


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

        kwargs = {k: inputs.pop(k) for k in list(inputs.keys())
                  if k in ('from_file', 'resource_monitor',
                           'ignore_exception')}
        super(Function, self).__init__(**kwargs)

        if input_names is not None:
            input_names = ensure_list(input_names)
        if function:
            # Use callback for consistent behavior
            self._input_names = []
            self._set_function(function, input_names)
        else:
            # Set input_names and wait to have function defined
            # Input names will be overridden
            if input_names is None:
                input_names = []
            self._input_names = input_names
            add_traits(self.inputs, [name for name in self._input_names])
            self._allow_kwargs = True
            self.inputs.on_trait_change(self._set_function_str, 'function_str')

        self._output_names = ensure_list(output_names)
        self.imports = imports
        self._out = {}
        for name in self._output_names:
            self._out[name] = None

        # With constraints in place, set inputs
        self.inputs.trait_set(True, **inputs)

    def __deepcopy__(self, memo):
        from copy import deepcopy
        dup = self.__class__(input_names=deepcopy(self._input_names, memo),
                             output_names=deepcopy(self._output_names, memo),
                             function=deepcopy(self.inputs.function_str, memo),
                             imports=deepcopy(self.imports, memo),
                             resource_monitor=self.resource_monitor,
                             ignore_exception=self.ignore_exception)
        dup.inputs.trait_set(**self.inputs.trait_get())
        return dup

    def _set_function_str(self, obj, name, old, new):
        obj.on_trait_change(self._set_function_str, 'function_str',
                            remove=True)
        self._set_function(new)

    def _set_function(self, function, input_names=None):
        fstr, in_names, defaults, ban, allow_kw = parse_function(function,
                                                                 input_names)

        # If `**kwargs` appears in the function signature, permit arbitrary
        # keywords
        if allow_kw:
            # Preserve trait values
            self.inputs = DynamicFunctionInputSpec(
                **self.inputs.get_traitsfree())

        self.inputs.trait_set(False, function_str=fstr)

        # "Banned" names are names with default values missing from the
        # input_names list. Setting as `Enum(x)` will throw an error if
        # a change is attempted.
        for banned_name in ban:
            self.inputs.add_trait(banned_name, SetOnce)

        to_add = set(in_names) - set(self._input_names) - set(ban)
        add_traits(self.inputs, to_add)
        self.inputs.trait_set(**defaults)
        self._input_names = in_names

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
        args = self.inputs.get_traitsfree()
        # Drop non-argument traits
        args.pop('function_str')
        args.pop('ignore_exception')

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
