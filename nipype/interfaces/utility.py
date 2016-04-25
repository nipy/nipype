# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Various utilities

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
   >>> os.chdir(datadir)
"""

from future import standard_library
standard_library.install_aliases()
from builtins import zip
from builtins import range

import os
import re
from pickle import dumps
from textwrap import dedent
import numpy as np
import nibabel as nb

from .base import (traits, TraitedSpec, DynamicTraitedSpec, File,
                   Undefined, isdefined, OutputMultiPath,
                   InputMultiPath, BaseInterface, BaseInterfaceInputSpec)
from .io import IOBase, add_traits
from ..external.six import string_types
from ..testing import assert_equal
from ..utils.filemanip import (filename_to_list, copyfile, split_filename)
from ..utils.misc import getsource, create_function_from_source


class IdentityInterface(IOBase):
    """Basic interface class generates identity mappings

    Examples
    --------

    >>> from nipype.interfaces.utility import IdentityInterface
    >>> ii = IdentityInterface(fields=['a', 'b'], mandatory_inputs=False)
    >>> ii.inputs.a
    <undefined>

    >>> ii.inputs.a = 'foo'
    >>> out = ii._outputs()
    >>> out.a
    <undefined>

    >>> out = ii.run()
    >>> out.outputs.a
    'foo'

    >>> ii2 = IdentityInterface(fields=['a', 'b'], mandatory_inputs=True)
    >>> ii2.inputs.a = 'foo'
    >>> out = ii2.run() # doctest: +SKIP
    ValueError: IdentityInterface requires a value for input 'b' because it was listed in 'fields' Interface IdentityInterface failed to run.
    """
    input_spec = DynamicTraitedSpec
    output_spec = DynamicTraitedSpec

    def __init__(self, fields=None, mandatory_inputs=True, **inputs):
        super(IdentityInterface, self).__init__(**inputs)
        if fields is None or not fields:
            raise ValueError('Identity Interface fields must be a non-empty list')
        # Each input must be in the fields.
        for in_field in inputs:
            if in_field not in fields:
                raise ValueError('Identity Interface input is not in the fields: %s' % in_field)
        self._fields = fields
        self._mandatory_inputs = mandatory_inputs
        add_traits(self.inputs, fields)
        # Adding any traits wipes out all input values set in superclass initialization,
        # even it the trait is not in the add_traits argument. The work-around is to reset
        # the values after adding the traits.
        self.inputs.set(**inputs)

    def _add_output_traits(self, base):
        return add_traits(base, self._fields)

    def _list_outputs(self):
        # manual mandatory inputs check
        if self._fields and self._mandatory_inputs:
            for key in self._fields:
                value = getattr(self.inputs, key)
                if not isdefined(value):
                    msg = "%s requires a value for input '%s' because it was listed in 'fields'. \
                    You can turn off mandatory inputs checking by passing mandatory_inputs = False to the constructor." % \
                        (self.__class__.__name__, key)
                    raise ValueError(msg)

        outputs = self._outputs().get()
        for key in self._fields:
            val = getattr(self.inputs, key)
            if isdefined(val):
                outputs[key] = val
        return outputs


class MergeInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):
    axis = traits.Enum('vstack', 'hstack', usedefault=True,
                       desc='direction in which to merge, hstack requires same number of elements in each input')
    no_flatten = traits.Bool(False, usedefault=True, desc='append to outlist instead of extending in vstack mode')


class MergeOutputSpec(TraitedSpec):
    out = traits.List(desc='Merged output')


class Merge(IOBase):
    """Basic interface class to merge inputs into a single list

    Examples
    --------

    >>> from nipype.interfaces.utility import Merge
    >>> mi = Merge(3)
    >>> mi.inputs.in1 = 1
    >>> mi.inputs.in2 = [2, 5]
    >>> mi.inputs.in3 = 3
    >>> out = mi.run()
    >>> out.outputs.out
    [1, 2, 5, 3]

    """
    input_spec = MergeInputSpec
    output_spec = MergeOutputSpec

    def __init__(self, numinputs=0, **inputs):
        super(Merge, self).__init__(**inputs)
        self._numinputs = numinputs
        add_traits(self.inputs, ['in%d' % (i + 1) for i in range(numinputs)])

    def _list_outputs(self):
        outputs = self._outputs().get()
        out = []
        if self.inputs.axis == 'vstack':
            for idx in range(self._numinputs):
                value = getattr(self.inputs, 'in%d' % (idx + 1))
                if isdefined(value):
                    if isinstance(value, list) and not self.inputs.no_flatten:
                        out.extend(value)
                    else:
                        out.append(value)
        else:
            for i in range(len(filename_to_list(self.inputs.in1))):
                out.insert(i, [])
                for j in range(self._numinputs):
                    out[i].append(filename_to_list(getattr(self.inputs, 'in%d' % (j + 1)))[i])
        if out:
            outputs['out'] = out
        return outputs


class RenameInputSpec(DynamicTraitedSpec):

    in_file = File(exists=True, mandatory=True, desc="file to rename")
    keep_ext = traits.Bool(desc=("Keep in_file extension, replace "
                                 "non-extension component of name"))
    format_string = traits.String(mandatory=True,
                                  desc=("Python formatting string for output "
                                        "template"))
    parse_string = traits.String(desc=("Python regexp parse string to define "
                                       "replacement inputs"))
    use_fullpath = traits.Bool(False, usedefault=True,
                               desc="Use full path as input to regex parser")


class RenameOutputSpec(TraitedSpec):

    out_file = traits.File(exists=True, desc="softlink to original file with new name")


class Rename(IOBase):
    """Change the name of a file based on a mapped format string.

    To use additional inputs that will be defined at run-time, the class
    constructor must be called with the format template, and the fields
    identified will become inputs to the interface.

    Additionally, you may set the parse_string input, which will be run
    over the input filename with a regular expressions search, and will
    fill in additional input fields from matched groups. Fields set with
    inputs have precedence over fields filled in with the regexp match.

    Examples
    --------
    >>> from nipype.interfaces.utility import Rename
    >>> rename1 = Rename()
    >>> rename1.inputs.in_file = "zstat1.nii.gz"
    >>> rename1.inputs.format_string = "Faces-Scenes.nii.gz"
    >>> res = rename1.run()          # doctest: +SKIP
    >>> res.outputs.out_file         # doctest: +SKIP
    'Faces-Scenes.nii.gz"            # doctest: +SKIP

    >>> rename2 = Rename(format_string="%(subject_id)s_func_run%(run)02d")
    >>> rename2.inputs.in_file = "functional.nii"
    >>> rename2.inputs.keep_ext = True
    >>> rename2.inputs.subject_id = "subj_201"
    >>> rename2.inputs.run = 2
    >>> res = rename2.run()          # doctest: +SKIP
    >>> res.outputs.out_file         # doctest: +SKIP
    'subj_201_func_run02.nii'        # doctest: +SKIP

    >>> rename3 = Rename(format_string="%(subject_id)s_%(seq)s_run%(run)02d.nii")
    >>> rename3.inputs.in_file = "func_epi_1_1.nii"
    >>> rename3.inputs.parse_string = "func_(?P<seq>\w*)_.*"
    >>> rename3.inputs.subject_id = "subj_201"
    >>> rename3.inputs.run = 2
    >>> res = rename3.run()          # doctest: +SKIP
    >>> res.outputs.out_file         # doctest: +SKIP
    'subj_201_epi_run02.nii'         # doctest: +SKIP

    """
    input_spec = RenameInputSpec
    output_spec = RenameOutputSpec

    def __init__(self, format_string=None, **inputs):
        super(Rename, self).__init__(**inputs)
        if format_string is not None:
            self.inputs.format_string = format_string
            self.fmt_fields = re.findall(r"%\((.+?)\)", format_string)
            add_traits(self.inputs, self.fmt_fields)
        else:
            self.fmt_fields = []

    def _rename(self):
        fmt_dict = dict()
        if isdefined(self.inputs.parse_string):
            if isdefined(self.inputs.use_fullpath) and self.inputs.use_fullpath:
                m = re.search(self.inputs.parse_string,
                              self.inputs.in_file)
            else:
                m = re.search(self.inputs.parse_string,
                              os.path.split(self.inputs.in_file)[1])
            if m:
                fmt_dict.update(m.groupdict())
        for field in self.fmt_fields:
            val = getattr(self.inputs, field)
            if isdefined(val):
                fmt_dict[field] = getattr(self.inputs, field)
        if self.inputs.keep_ext:
            fmt_string = "".join([self.inputs.format_string,
                                  split_filename(self.inputs.in_file)[2]])
        else:
            fmt_string = self.inputs.format_string
        return fmt_string % fmt_dict

    def _run_interface(self, runtime):
        runtime.returncode = 0
        _ = copyfile(self.inputs.in_file, os.path.join(os.getcwd(),
                                                       self._rename()))
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.join(os.getcwd(), self._rename())
        return outputs


class SplitInputSpec(BaseInterfaceInputSpec):
    inlist = traits.List(traits.Any, mandatory=True,
                         desc='list of values to split')
    splits = traits.List(traits.Int, mandatory=True,
                         desc='Number of outputs in each split - should add to number of inputs')
    squeeze = traits.Bool(False, usedefault=True,
                          desc='unfold one-element splits removing the list')


class Split(IOBase):
    """Basic interface class to split lists into multiple outputs

    Examples
    --------

    >>> from nipype.interfaces.utility import Split
    >>> sp = Split()
    >>> _ = sp.inputs.set(inlist=[1, 2, 3], splits=[2, 1])
    >>> out = sp.run()
    >>> out.outputs.out1
    [1, 2]

    """

    input_spec = SplitInputSpec
    output_spec = DynamicTraitedSpec

    def _add_output_traits(self, base):
        undefined_traits = {}
        for i in range(len(self.inputs.splits)):
            key = 'out%d' % (i + 1)
            base.add_trait(key, traits.Any)
            undefined_traits[key] = Undefined
        base.trait_set(trait_change_notify=False, **undefined_traits)
        return base

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.splits):
            if sum(self.inputs.splits) != len(self.inputs.inlist):
                raise RuntimeError('sum of splits != num of list elements')
            splits = [0]
            splits.extend(self.inputs.splits)
            splits = np.cumsum(splits)
            for i in range(len(splits) - 1):
                val = np.array(self.inputs.inlist)[splits[i]:splits[i + 1]].tolist()
                if self.inputs.squeeze and len(val) == 1:
                    val = val[0]
                outputs['out%d' % (i + 1)] = val
        return outputs


class SelectInputSpec(BaseInterfaceInputSpec):
    inlist = InputMultiPath(traits.Any, mandatory=True,
                            desc='list of values to choose from')
    index = InputMultiPath(traits.Int, mandatory=True,
                           desc='0-based indices of values to choose')


class SelectOutputSpec(TraitedSpec):
    out = OutputMultiPath(traits.Any, desc='list of selected values')


class Select(IOBase):
    """Basic interface class to select specific elements from a list

    Examples
    --------

    >>> from nipype.interfaces.utility import Select
    >>> sl = Select()
    >>> _ = sl.inputs.set(inlist=[1, 2, 3, 4, 5], index=[3])
    >>> out = sl.run()
    >>> out.outputs.out
    4

    >>> _ = sl.inputs.set(inlist=[1, 2, 3, 4, 5], index=[3, 4])
    >>> out = sl.run()
    >>> out.outputs.out
    [4, 5]

    """

    input_spec = SelectInputSpec
    output_spec = SelectOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        out = np.array(self.inputs.inlist)[np.array(self.inputs.index)].tolist()
        outputs['out'] = out
        return outputs


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

    def __init__(self, input_names, output_names, function=None, imports=None,
                 **inputs):
        """

        Parameters
        ----------

        input_names: single str or list
            names corresponding to function inputs
        output_names: single str or list
            names corresponding to function outputs.
            has to match the number of outputs
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
            elif isinstance(function, string_types):
                self.inputs.function_str = function
            else:
                raise Exception('Unknown type of function')
        self.inputs.on_trait_change(self._set_function_string,
                                    'function_str')
        self._input_names = filename_to_list(input_names)
        self._output_names = filename_to_list(output_names)
        add_traits(self.inputs, [name for name in self._input_names])
        self.imports = imports
        self._out = {}
        for name in self._output_names:
            self._out[name] = None

    def _set_function_string(self, obj, name, old, new):
        if name == 'function_str':
            if hasattr(new, '__call__'):
                function_source = getsource(new)
            elif isinstance(new, string_types):
                function_source = new
            self.inputs.trait_set(trait_change_notify=False,
                                  **{'%s' % name: function_source})

    def _add_output_traits(self, base):
        undefined_traits = {}
        for key in self._output_names:
            base.add_trait(key, traits.Any)
            undefined_traits[key] = Undefined
        base.trait_set(trait_change_notify=False, **undefined_traits)
        return base

    def _run_interface(self, runtime):
        # Get workflow logger for runtime profile error reporting
        from nipype import logging
        logger = logging.getLogger('workflow')

        # Create function handle
        function_handle = create_function_from_source(self.inputs.function_str,
                                                      self.imports)

        # Wrapper for running function handle in multiprocessing.Process
        # Can catch exceptions and report output via multiprocessing.Queue
        def _function_handle_wrapper(queue, **kwargs):
            try:
                out = function_handle(**kwargs)
                queue.put(out)
            except Exception as exc:
                queue.put(exc)

        # Get function args
        args = {}
        for name in self._input_names:
            value = getattr(self.inputs, name)
            if isdefined(value):
                args[name] = value

        # Runtime profiler on if dependecies available
        try:
            import psutil
            from nipype.interfaces.base import get_max_resources_used
            import multiprocessing
            runtime_profile = True
        except ImportError as exc:
            logger.info('Unable to import packages needed for runtime profiling. '\
                        'Turning off runtime profiler. Reason: %s' % exc)
            runtime_profile = False

        # Profile resources if set
        #runtime_profile=False
        if runtime_profile:
            # Init communication queue and proc objs
            queue = multiprocessing.Queue()
            proc = multiprocessing.Process(target=_function_handle_wrapper,
                                           args=(queue,), kwargs=args)

            # Init memory and threads before profiling
            mem_mb = 0
            num_threads = 0

            # Start process and profile while it's alive
            proc.start()
            while proc.is_alive():
                mem_mb, num_threads = \
                    get_max_resources_used(proc.pid, mem_mb, num_threads,
                                           pyfunc=True)

            # Get result from process queue
            out = queue.get()
            # If it is an exception, raise it
            if isinstance(out, Exception):
                raise out

            # Function ran successfully, populate runtime stats
            setattr(runtime, 'runtime_memory_gb', mem_mb/1024.0)
            setattr(runtime, 'runtime_threads', num_threads)
        else:
            out = function_handle(**args)

        if len(self._output_names) == 1:
            self._out[self._output_names[0]] = out
        else:
            if isinstance(out, tuple) and (len(out) != len(self._output_names)):
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


class AssertEqualInputSpec(BaseInterfaceInputSpec):
    volume1 = File(exists=True, mandatory=True)
    volume2 = File(exists=True, mandatory=True)


class AssertEqual(BaseInterface):
    input_spec = AssertEqualInputSpec

    def _run_interface(self, runtime):

        data1 = nb.load(self.inputs.volume1).get_data()
        data2 = nb.load(self.inputs.volume2).get_data()

        assert_equal(data1, data2)

        return runtime


class CSVReaderInputSpec(DynamicTraitedSpec, TraitedSpec):
    in_file = File(exists=True, mandatory=True, desc='Input comma-seperated value (CSV) file')
    header = traits.Bool(False, usedefault=True, desc='True if the first line is a column header')


class CSVReader(BaseInterface):
    """
    Examples
    --------

    >>> reader = CSVReader()  # doctest: +SKIP
    >>> reader.inputs.in_file = 'noHeader.csv'  # doctest: +SKIP
    >>> out = reader.run()  # doctest: +SKIP
    >>> out.outputs.column_0 == ['foo', 'bar', 'baz']  # doctest: +SKIP
    True
    >>> out.outputs.column_1 == ['hello', 'world', 'goodbye']  # doctest: +SKIP
    True
    >>> out.outputs.column_2 == ['300.1', '5', '0.3']  # doctest: +SKIP
    True

    >>> reader = CSVReader()  # doctest: +SKIP
    >>> reader.inputs.in_file = 'header.csv'  # doctest: +SKIP
    >>> reader.inputs.header = True  # doctest: +SKIP
    >>> out = reader.run()  # doctest: +SKIP
    >>> out.outputs.files == ['foo', 'bar', 'baz']  # doctest: +SKIP
    True
    >>> out.outputs.labels == ['hello', 'world', 'goodbye']  # doctest: +SKIP
    True
    >>> out.outputs.erosion == ['300.1', '5', '0.3']  # doctest: +SKIP
    True

    """
    input_spec = CSVReaderInputSpec
    output_spec = DynamicTraitedSpec
    _always_run = True

    def _append_entry(self, outputs, entry):
        for key, value in zip(self._outfields, entry):
            outputs[key].append(value)
        return outputs

    def _parse_line(self, line):
        line = line.replace('\n', '')
        entry = [x.strip() for x in line.split(',')]
        return entry

    def _get_outfields(self):
        with open(self.inputs.in_file, 'r') as fid:
            entry = self._parse_line(fid.readline())
            if self.inputs.header:
                self._outfields = tuple(entry)
            else:
                self._outfields = tuple(['column_' + str(x) for x in range(len(entry))])
        return self._outfields

    def _run_interface(self, runtime):
        self._get_outfields()
        return runtime

    def _outputs(self):
        return self._add_output_traits(super(CSVReader, self)._outputs())

    def _add_output_traits(self, base):
        return add_traits(base, self._get_outfields())

    def _list_outputs(self):
        outputs = self.output_spec().get()
        isHeader = True
        for key in self._outfields:
            outputs[key] = []  # initialize outfields
        with open(self.inputs.in_file, 'r') as fid:
            for line in fid.readlines():
                if self.inputs.header and isHeader:  # skip header line
                    isHeader = False
                    continue
                entry = self._parse_line(line)
                outputs = self._append_entry(outputs, entry)
        return outputs
