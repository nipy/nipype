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
from ...utils.filemanip import filename_to_list
from ...utils.functions import getsource, create_function_from_source

iflogger = logging.getLogger('interface')


class FunctionInputSpec2(DynamicTraitedSpec, BaseInterfaceInputSpec):
    function_str = traits.Str(mandatory=True, desc='code for function')

class FunctionInputSpec(BaseInterfaceInputSpec):
    function_str = traits.Str(mandatory=True, desc='code for function')

from inspect import getfullargspec, getsource

def parse_function(function, input_names=None, imports=None):
    if hasattr(function, '__call__'):
        function_str = getsource(function)
        argspec = getfullargspec(function)
    elif isinstance(function, (str, bytes)):
        fninfo = create_function_from_source(function,
                                             imports)
        function_str = function
        argspec = getfullargspec(fninfo)
    else:
        raise TypeError('Unknown type of function')
    all_args = argspec.args + argspec.kwonlyargs
    required_args = set(all_args) - set(argspec.kwonlydefaults.keys())
    if input_names is None:
        input_names = all_args
    else:
        missed_args = required_args - set(input_names)
        if missed_args:
            raise ValueError('These positional args must be in '
                             'input_names: {}'.format(missed_args))
        unknown = set(input_names) - set(all_args)
        if unknown:
            raise ValueError('Unknown arguments: {} '
                             'for function'.format(unknown))
    banned_names = list(set(argspec.kwonlydefaults.keys()) - set(input_names))
    return function_str, filename_to_list(input_names), \
           banned_names, argspec.varkw is not None


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
                 function=None,
                 input_names=None,
                 output_names='out',
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
        self._input_names = None
        self._kwargs_allowed = None
        if function is not None:
            function_str,\
            self._input_names,\
            self._banned_names,\
            self._kwargs_allowed = parse_function(function, input_names, imports)
        if self._kwargs_allowed:
            self.inputs = FunctionInputSpec2()
        self.inputs.on_trait_change(self._set_function_string, 'function_str')
        self._output_names = filename_to_list(output_names)
        add_traits(self.inputs, [name for name in self._input_names])
        for name in self._banned_names:
            self.inputs.add_trait(name, traits.Any)
            self.inputs.on_trait_change(self._cannot_modify, name)
        self.imports = imports
        self._out = {}
        for name in self._output_names:
            self._out[name] = None

    def _cannot_modify(self, obj, name, old, new):
        if name in self._banned_names:
            raise traits.TraitError('The function does not allow modifying ' 
                                    'input: {}'.format(name))

    def _set_function_string(self, obj, name, old, new):
        if name == 'function_str':
            function_str,\
            input_names,\
            self._banned_names,\
            self._kwargs_allowed = parse_function(new, None, self.imports)
            self.inputs.trait_set(
                trait_change_notify=False, **{
                    '%s' % name: function_str
                })
            for name in self._input_names:
                self.inputs.remove_trait(name)
            self._input_names = input_names
            add_traits(self.inputs, input_names)
        else:
            print(2, name, self._banned_names, obj, old)
            if name not in self._banned_names and (self._kwargs_allowed or
                                                   (self._input_names and
                                                    name in self._input_names)):
                self.inputs.trait_set(
                    trait_change_notify=False, **{
                        '%s' % name: new
                    })
            else:
                raise ValueError('{} not an allowed argument'.format(name))

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
