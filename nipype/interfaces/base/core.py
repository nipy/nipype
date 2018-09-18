# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Nipype interfaces core
......................


Defines the ``Interface`` API and the body of the
most basic interfaces.
The I/O specifications corresponding to these base
interfaces are found in the ``specs`` module.

"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

from builtins import object, open, str, bytes

import gc
from copy import deepcopy
from datetime import datetime as dt
import errno
import os
import re
import platform
import select
import subprocess as sp
import shlex
import sys
from textwrap import wrap
import simplejson as json
from dateutil.parser import parse as parseutc

from ... import config, logging, LooseVersion
from ...utils.provenance import write_provenance
from ...utils.misc import trim, str2bool, rgetcwd
from ...utils.filemanip import (FileNotFoundError, split_filename, read_stream,
                                which, get_dependencies, canonicalize_env as
                                _canonicalize_env)

from ...external.due import due

from .traits_extension import traits, isdefined, TraitError
from .specs import (BaseInterfaceInputSpec, CommandLineInputSpec,
                    StdOutCommandLineInputSpec, MpiCommandLineInputSpec)
from .support import (Bunch, Stream, InterfaceResult, NipypeInterfaceError)

from future import standard_library
standard_library.install_aliases()

iflogger = logging.getLogger('nipype.interface')

PY35 = sys.version_info >= (3, 5)
PY3 = sys.version_info[0] > 2
VALID_TERMINAL_OUTPUT = [
    'stream', 'allatonce', 'file', 'file_split', 'file_stdout', 'file_stderr',
    'none'
]
__docformat__ = 'restructuredtext'


class Interface(object):
    """This is an abstract definition for Interface objects.

    It provides no functionality.  It defines the necessary attributes
    and methods all Interface objects should have.

    """

    input_spec = None  # A traited input specification
    output_spec = None  # A traited output specification

    # defines if the interface can reuse partial results after interruption
    _can_resume = False

    @property
    def can_resume(self):
        return self._can_resume

    # should the interface be always run even if the inputs were not changed?
    _always_run = False

    @property
    def always_run(self):
        return self._always_run

    def __init__(self, **inputs):
        """Initialize command with given args and inputs."""
        raise NotImplementedError

    @classmethod
    def help(cls):
        """ Prints class help"""
        raise NotImplementedError

    @classmethod
    def _inputs_help(cls):
        """ Prints inputs help"""
        raise NotImplementedError

    @classmethod
    def _outputs_help(cls):
        """ Prints outputs help"""
        raise NotImplementedError

    @classmethod
    def _outputs(cls):
        """ Initializes outputs"""
        raise NotImplementedError

    @property
    def version(self):
        raise NotImplementedError

    def run(self):
        """Execute the command."""
        raise NotImplementedError

    def aggregate_outputs(self, runtime=None, needed_outputs=None):
        """Called to populate outputs"""
        raise NotImplementedError

    def _list_outputs(self):
        """ List expected outputs"""
        raise NotImplementedError

    def _get_filecopy_info(self):
        """ Provides information about file inputs to copy or link to cwd.
            Necessary for pipeline operation
        """
        raise NotImplementedError


class BaseInterface(Interface):
    """Implements common interface functionality.

    Implements
    ----------

    * Initializes inputs/outputs from input_spec/output_spec
    * Provides help based on input_spec and output_spec
    * Checks for mandatory inputs before running an interface
    * Runs an interface and returns results
    * Determines which inputs should be copied or linked to cwd

    This class does not implement aggregate_outputs, input_spec or
    output_spec. These should be defined by derived classes.

    This class cannot be instantiated.


    Relevant Interface attributes
    -----------------------------

    ``input_spec`` points to the traited class for the inputs
    ``output_spec`` points to the traited class for the outputs
    ``_redirect_x`` should be set to ``True`` when the interface requires
      connecting to a ``$DISPLAY`` (default is ``False``).
    ``resource_monitor`` if ``False`` prevents resource-monitoring this
      interface, if ``True`` monitoring will be enabled IFF the general
      Nipype config is set on (``resource_monitor = true``).


    """
    input_spec = BaseInterfaceInputSpec
    _version = None
    _additional_metadata = []
    _redirect_x = False
    references_ = []
    resource_monitor = True  # Enabled for this interface IFF enabled in the config

    def __init__(self, from_file=None, resource_monitor=None,
                 ignore_exception=False, **inputs):
        if not self.input_spec:
            raise Exception(
                'No input_spec in class: %s' % self.__class__.__name__)

        self.inputs = self.input_spec(**inputs)
        self.ignore_exception = ignore_exception

        if resource_monitor is not None:
            self.resource_monitor = resource_monitor

        if from_file is not None:
            self.load_inputs_from_json(from_file, overwrite=True)

            for name, value in list(inputs.items()):
                setattr(self.inputs, name, value)

    @classmethod
    def help(cls, returnhelp=False):
        """ Prints class help
        """

        if cls.__doc__:
            # docstring = cls.__doc__.split('\n')
            # docstring = [trim(line, '') for line in docstring]
            docstring = trim(cls.__doc__).split('\n') + ['']
        else:
            docstring = ['']

        allhelp = '\n'.join(docstring + cls._inputs_help(
        ) + [''] + cls._outputs_help() + [''] + cls._refs_help() + [''])
        if returnhelp:
            return allhelp
        else:
            print(allhelp)

    @classmethod
    def _refs_help(cls):
        """ Prints interface references.
        """
        if not cls.references_:
            return []

        helpstr = ['References::']

        for r in cls.references_:
            helpstr += ['{}'.format(r['entry'])]

        return helpstr

    @classmethod
    def _get_trait_desc(self, inputs, name, spec):
        desc = spec.desc
        xor = spec.xor
        requires = spec.requires
        argstr = spec.argstr

        manhelpstr = ['\t%s' % name]

        type_info = spec.full_info(inputs, name, None)

        default = ''
        if spec.usedefault:
            default = ', nipype default value: %s' % str(
                spec.default_value()[1])
        line = "(%s%s)" % (type_info, default)

        manhelpstr = wrap(
            line,
            70,
            initial_indent=manhelpstr[0] + ': ',
            subsequent_indent='\t\t ')

        if desc:
            for line in desc.split('\n'):
                line = re.sub("\s+", " ", line)
                manhelpstr += wrap(
                    line, 70, initial_indent='\t\t', subsequent_indent='\t\t')

        if argstr:
            pos = spec.position
            if pos is not None:
                manhelpstr += wrap(
                    'flag: %s, position: %s' % (argstr, pos),
                    70,
                    initial_indent='\t\t',
                    subsequent_indent='\t\t')
            else:
                manhelpstr += wrap(
                    'flag: %s' % argstr,
                    70,
                    initial_indent='\t\t',
                    subsequent_indent='\t\t')

        if xor:
            line = '%s' % ', '.join(xor)
            manhelpstr += wrap(
                line,
                70,
                initial_indent='\t\tmutually_exclusive: ',
                subsequent_indent='\t\t ')

        if requires:
            others = [field for field in requires if field != name]
            line = '%s' % ', '.join(others)
            manhelpstr += wrap(
                line,
                70,
                initial_indent='\t\trequires: ',
                subsequent_indent='\t\t ')
        return manhelpstr

    @classmethod
    def _inputs_help(cls):
        """ Prints description for input parameters
        """
        helpstr = ['Inputs::']

        inputs = cls.input_spec()
        if len(list(inputs.traits(transient=None).items())) == 0:
            helpstr += ['', '\tNone']
            return helpstr

        manhelpstr = ['', '\t[Mandatory]']
        mandatory_items = inputs.traits(mandatory=True)
        for name, spec in sorted(mandatory_items.items()):
            manhelpstr += cls._get_trait_desc(inputs, name, spec)

        opthelpstr = ['', '\t[Optional]']
        for name, spec in sorted(inputs.traits(transient=None).items()):
            if name in mandatory_items:
                continue
            opthelpstr += cls._get_trait_desc(inputs, name, spec)

        if manhelpstr:
            helpstr += manhelpstr
        if opthelpstr:
            helpstr += opthelpstr
        return helpstr

    @classmethod
    def _outputs_help(cls):
        """ Prints description for output parameters
        """
        helpstr = ['Outputs::', '']
        if cls.output_spec:
            outputs = cls.output_spec()
            for name, spec in sorted(outputs.traits(transient=None).items()):
                helpstr += cls._get_trait_desc(outputs, name, spec)
        if len(helpstr) == 2:
            helpstr += ['\tNone']
        return helpstr

    def _outputs(self):
        """ Returns a bunch containing output fields for the class
        """
        outputs = None
        if self.output_spec:
            outputs = self.output_spec()

        return outputs

    @classmethod
    def _get_filecopy_info(cls):
        """ Provides information about file inputs to copy or link to cwd.
            Necessary for pipeline operation
        """
        info = []
        if cls.input_spec is None:
            return info
        metadata = dict(copyfile=lambda t: t is not None)
        for name, spec in sorted(cls.input_spec().traits(**metadata).items()):
            info.append(dict(key=name, copy=spec.copyfile))
        return info

    def _check_requires(self, spec, name, value):
        """ check if required inputs are satisfied
        """
        if spec.requires:
            values = [
                not isdefined(getattr(self.inputs, field))
                for field in spec.requires
            ]
            if any(values) and isdefined(value):
                msg = ("%s requires a value for input '%s' because one of %s "
                       "is set. For a list of required inputs, see %s.help()" %
                       (self.__class__.__name__, name,
                        ', '.join(spec.requires), self.__class__.__name__))
                raise ValueError(msg)

    def _check_xor(self, spec, name, value):
        """ check if mutually exclusive inputs are satisfied
        """
        if spec.xor:
            values = [
                isdefined(getattr(self.inputs, field)) for field in spec.xor
            ]
            if not any(values) and not isdefined(value):
                msg = ("%s requires a value for one of the inputs '%s'. "
                       "For a list of required inputs, see %s.help()" %
                       (self.__class__.__name__, ', '.join(spec.xor),
                        self.__class__.__name__))
                raise ValueError(msg)

    def _check_mandatory_inputs(self):
        """ Raises an exception if a mandatory input is Undefined
        """
        for name, spec in list(self.inputs.traits(mandatory=True).items()):
            value = getattr(self.inputs, name)
            self._check_xor(spec, name, value)
            if not isdefined(value) and spec.xor is None:
                msg = ("%s requires a value for input '%s'. "
                       "For a list of required inputs, see %s.help()" %
                       (self.__class__.__name__, name,
                        self.__class__.__name__))
                raise ValueError(msg)
            if isdefined(value):
                self._check_requires(spec, name, value)
        for name, spec in list(
                self.inputs.traits(mandatory=None, transient=None).items()):
            self._check_requires(spec, name, getattr(self.inputs, name))

    def _check_version_requirements(self, trait_object, raise_exception=True):
        """ Raises an exception on version mismatch
        """
        unavailable_traits = []
        # check minimum version
        check = dict(min_ver=lambda t: t is not None)
        names = trait_object.trait_names(**check)

        if names and self.version:
            version = LooseVersion(str(self.version))
            for name in names:
                min_ver = LooseVersion(
                    str(trait_object.traits()[name].min_ver))
                if min_ver > version:
                    unavailable_traits.append(name)
                    if not isdefined(getattr(trait_object, name)):
                        continue
                    if raise_exception:
                        raise Exception(
                            'Trait %s (%s) (version %s < required %s)' %
                            (name, self.__class__.__name__, version, min_ver))

        # check maximum version
        check = dict(max_ver=lambda t: t is not None)
        names = trait_object.trait_names(**check)
        if names and self.version:
            version = LooseVersion(str(self.version))
            for name in names:
                max_ver = LooseVersion(
                    str(trait_object.traits()[name].max_ver))
                if max_ver < version:
                    unavailable_traits.append(name)
                    if not isdefined(getattr(trait_object, name)):
                        continue
                    if raise_exception:
                        raise Exception(
                            'Trait %s (%s) (version %s > required %s)' %
                            (name, self.__class__.__name__, version, max_ver))
        return unavailable_traits

    def _run_interface(self, runtime):
        """ Core function that executes interface
        """
        raise NotImplementedError

    def _duecredit_cite(self):
        """ Add the interface references to the duecredit citations
        """
        for r in self.references_:
            r['path'] = self.__module__
            due.cite(**r)

    def run(self, cwd=None, ignore_exception=None, **inputs):
        """Execute this interface.

        This interface will not raise an exception if runtime.returncode is
        non-zero.

        Parameters
        ----------

        cwd : specify a folder where the interface should be run
        inputs : allows the interface settings to be updated

        Returns
        -------
        results :  an InterfaceResult object containing a copy of the instance
        that was executed, provenance information and, if successful, results
        """
        from ...utils.profiler import ResourceMonitor

        # if ignore_exception is not provided, taking self.ignore_exception
        if ignore_exception is None:
            ignore_exception = self.ignore_exception

        # Tear-up: get current and prev directories
        syscwd = rgetcwd(error=False)  # Recover when wd does not exist
        if cwd is None:
            cwd = syscwd

        os.chdir(cwd)  # Change to the interface wd

        enable_rm = config.resource_monitor and self.resource_monitor
        self.inputs.trait_set(**inputs)
        self._check_mandatory_inputs()
        self._check_version_requirements(self.inputs)
        interface = self.__class__
        self._duecredit_cite()

        # initialize provenance tracking
        store_provenance = str2bool(
            config.get('execution', 'write_provenance', 'false'))
        env = deepcopy(dict(os.environ))
        if self._redirect_x:
            env['DISPLAY'] = config.get_display()

        runtime = Bunch(
            cwd=cwd,
            prevcwd=syscwd,
            returncode=None,
            duration=None,
            environ=env,
            startTime=dt.isoformat(dt.utcnow()),
            endTime=None,
            platform=platform.platform(),
            hostname=platform.node(),
            version=self.version)
        runtime_attrs = set(runtime.dictcopy())

        mon_sp = None
        if enable_rm:
            mon_freq = float(
                config.get('execution', 'resource_monitor_frequency', 1))
            proc_pid = os.getpid()
            iflogger.debug(
                'Creating a ResourceMonitor on a %s interface, PID=%d.',
                self.__class__.__name__, proc_pid)
            mon_sp = ResourceMonitor(proc_pid, freq=mon_freq)
            mon_sp.start()

        # Grab inputs now, as they should not change during execution
        inputs = self.inputs.get_traitsfree()
        outputs = None

        try:
            runtime = self._pre_run_hook(runtime)
            runtime = self._run_interface(runtime)
            runtime = self._post_run_hook(runtime)
            outputs = self.aggregate_outputs(runtime)
        except Exception as e:
            import traceback
            # Retrieve the maximum info fast
            runtime.traceback = traceback.format_exc()
            # Gather up the exception arguments and append nipype info.
            exc_args = e.args if getattr(e, 'args') else tuple()
            exc_args += (
                'An exception of type %s occurred while running interface %s.'
                % (type(e).__name__, self.__class__.__name__), )
            if config.get('logging', 'interface_level',
                          'info').lower() == 'debug':
                exc_args += ('Inputs: %s' % str(self.inputs), )

            runtime.traceback_args = ('\n'.join(
                ['%s' % arg for arg in exc_args]), )

            if not ignore_exception:
                raise
        finally:
            if runtime is None or runtime_attrs - set(runtime.dictcopy()):
                raise RuntimeError("{} interface failed to return valid "
                                   "runtime object".format(
                                       interface.__class__.__name__))
            # This needs to be done always
            runtime.endTime = dt.isoformat(dt.utcnow())
            timediff = parseutc(runtime.endTime) - parseutc(runtime.startTime)
            runtime.duration = (timediff.days * 86400 + timediff.seconds +
                                timediff.microseconds / 1e6)
            results = InterfaceResult(
                interface,
                runtime,
                inputs=inputs,
                outputs=outputs,
                provenance=None)

            # Add provenance (if required)
            if store_provenance:
                # Provenance will only throw a warning if something went wrong
                results.provenance = write_provenance(results)

            # Make sure runtime profiler is shut down
            if enable_rm:
                import numpy as np
                mon_sp.stop()

                runtime.mem_peak_gb = None
                runtime.cpu_percent = None

                # Read .prof file in and set runtime values
                vals = np.loadtxt(mon_sp.fname, delimiter=',')
                if vals.size:
                    vals = np.atleast_2d(vals)
                    runtime.mem_peak_gb = vals[:, 1].max() / 1024
                    runtime.cpu_percent = vals[:, 2].max()

                    runtime.prof_dict = {
                        'time': vals[:, 0].tolist(),
                        'cpus': vals[:, 1].tolist(),
                        'rss_GiB': (vals[:, 2] / 1024).tolist(),
                        'vms_GiB': (vals[:, 3] / 1024).tolist(),
                    }
            os.chdir(syscwd)

        return results

    def _list_outputs(self):
        """ List the expected outputs
        """
        if self.output_spec:
            raise NotImplementedError
        else:
            return None

    def aggregate_outputs(self, runtime=None, needed_outputs=None):
        """ Collate expected outputs and check for existence
        """

        predicted_outputs = self._list_outputs()
        outputs = self._outputs()
        if predicted_outputs:
            _unavailable_outputs = []
            if outputs:
                _unavailable_outputs = \
                    self._check_version_requirements(self._outputs())
            for key, val in list(predicted_outputs.items()):
                if needed_outputs and key not in needed_outputs:
                    continue
                if key in _unavailable_outputs:
                    raise KeyError(('Output trait %s not available in version '
                                    '%s of interface %s. Please inform '
                                    'developers.') % (key, self.version,
                                                      self.__class__.__name__))
                try:
                    setattr(outputs, key, val)
                except TraitError as error:
                    if getattr(error, 'info',
                               'default').startswith('an existing'):
                        msg = ("File/Directory '%s' not found for %s output "
                               "'%s'." % (val, self.__class__.__name__, key))
                        raise FileNotFoundError(msg)
                    raise error

        return outputs

    @property
    def version(self):
        if self._version is None:
            if str2bool(config.get('execution', 'stop_on_unknown_version')):
                raise ValueError('Interface %s has no version information' %
                                 self.__class__.__name__)
        return self._version

    def load_inputs_from_json(self, json_file, overwrite=True):
        """
        A convenient way to load pre-set inputs from a JSON file.
        """

        with open(json_file) as fhandle:
            inputs_dict = json.load(fhandle)

        def_inputs = []
        if not overwrite:
            def_inputs = list(self.inputs.get_traitsfree().keys())

        new_inputs = list(set(list(inputs_dict.keys())) - set(def_inputs))
        for key in new_inputs:
            if hasattr(self.inputs, key):
                setattr(self.inputs, key, inputs_dict[key])

    def save_inputs_to_json(self, json_file):
        """
        A convenient way to save current inputs to a JSON file.
        """
        inputs = self.inputs.get_traitsfree()
        iflogger.debug('saving inputs {}', inputs)
        with open(json_file, 'w' if PY3 else 'wb') as fhandle:
            json.dump(inputs, fhandle, indent=4, ensure_ascii=False)

    def _pre_run_hook(self, runtime):
        """
        Perform any pre-_run_interface() processing

        Subclasses may override this function to modify ``runtime`` object or
        interface state

        MUST return runtime object
        """
        return runtime

    def _post_run_hook(self, runtime):
        """
        Perform any post-_run_interface() processing

        Subclasses may override this function to modify ``runtime`` object or
        interface state

        MUST return runtime object
        """
        return runtime


class SimpleInterface(BaseInterface):
    """ An interface pattern that allows outputs to be set in a dictionary
    called ``_results`` that is automatically interpreted by
    ``_list_outputs()`` to find the outputs.

    When implementing ``_run_interface``, set outputs with::

        self._results[out_name] = out_value

    This can be a way to upgrade a ``Function`` interface to do type checking.

    Examples
    --------

    >>> from nipype.interfaces.base import (
    ...     SimpleInterface, BaseInterfaceInputSpec, TraitedSpec)

    >>> def double(x):
    ...    return 2 * x
    ...
    >>> class DoubleInputSpec(BaseInterfaceInputSpec):
    ...     x = traits.Float(mandatory=True)
    ...
    >>> class DoubleOutputSpec(TraitedSpec):
    ...     doubled = traits.Float()
    ...
    >>> class Double(SimpleInterface):
    ...     input_spec = DoubleInputSpec
    ...     output_spec = DoubleOutputSpec
    ...
    ...     def _run_interface(self, runtime):
    ...          self._results['doubled'] = double(self.inputs.x)
    ...          return runtime

    >>> dbl = Double()
    >>> dbl.inputs.x = 2
    >>> dbl.run().outputs.doubled
    4.0
    """

    def __init__(self, from_file=None, resource_monitor=None, **inputs):
        super(SimpleInterface, self).__init__(
            from_file=from_file, resource_monitor=resource_monitor, **inputs)
        self._results = {}

    def _list_outputs(self):
        return self._results


def run_command(runtime, output=None, timeout=0.01):
    """Run a command, read stdout and stderr, prefix with timestamp.

    The returned runtime contains a merged stdout+stderr log with timestamps
    """

    # Init variables
    cmdline = runtime.cmdline
    env = _canonicalize_env(runtime.environ)

    errfile = None
    outfile = None
    stdout = sp.PIPE
    stderr = sp.PIPE

    if output == 'file':
        outfile = os.path.join(runtime.cwd, 'output.nipype')
        stdout = open(outfile, 'wb')  # t=='text'===default
        stderr = sp.STDOUT
    elif output == 'file_split':
        outfile = os.path.join(runtime.cwd, 'stdout.nipype')
        stdout = open(outfile, 'wb')
        errfile = os.path.join(runtime.cwd, 'stderr.nipype')
        stderr = open(errfile, 'wb')
    elif output == 'file_stdout':
        outfile = os.path.join(runtime.cwd, 'stdout.nipype')
        stdout = open(outfile, 'wb')
    elif output == 'file_stderr':
        errfile = os.path.join(runtime.cwd, 'stderr.nipype')
        stderr = open(errfile, 'wb')

    proc = sp.Popen(
        cmdline,
        stdout=stdout,
        stderr=stderr,
        shell=True,
        cwd=runtime.cwd,
        env=env,
        close_fds=(not sys.platform.startswith('win')),
    )

    result = {
        'stdout': [],
        'stderr': [],
        'merged': [],
    }

    if output == 'stream':
        streams = [
            Stream('stdout', proc.stdout),
            Stream('stderr', proc.stderr)
        ]

        def _process(drain=0):
            try:
                res = select.select(streams, [], [], timeout)
            except select.error as e:
                iflogger.info(e)
                if e[0] == errno.EINTR:
                    return
                else:
                    raise
            else:
                for stream in res[0]:
                    stream.read(drain)

        while proc.returncode is None:
            proc.poll()
            _process()

        _process(drain=1)

        # collect results, merge and return
        result = {}
        temp = []
        for stream in streams:
            rows = stream._rows
            temp += rows
            result[stream._name] = [r[2] for r in rows]
        temp.sort()
        result['merged'] = [r[1] for r in temp]

    if output.startswith('file'):
        proc.wait()
        if outfile is not None:
            stdout.flush()
            stdout.close()
            with open(outfile, 'rb') as ofh:
                stdoutstr = ofh.read()
            result['stdout'] = read_stream(stdoutstr, logger=iflogger)
            del stdoutstr

        if errfile is not None:
            stderr.flush()
            stderr.close()
            with open(errfile, 'rb') as efh:
                stderrstr = efh.read()
            result['stderr'] = read_stream(stderrstr, logger=iflogger)
            del stderrstr

        if output == 'file':
            result['merged'] = result['stdout']
            result['stdout'] = []
    else:
        stdout, stderr = proc.communicate()
        if output == 'allatonce':  # Discard stdout and stderr otherwise
            result['stdout'] = read_stream(stdout, logger=iflogger)
            result['stderr'] = read_stream(stderr, logger=iflogger)

    runtime.returncode = proc.returncode
    try:
        proc.terminate()  # Ensure we are done
    except OSError as error:
        # Python 2 raises when the process is already gone
        if error.errno != errno.ESRCH:
            raise

    # Dereference & force GC for a cleanup
    del proc
    del stdout
    del stderr
    gc.collect()

    runtime.stderr = '\n'.join(result['stderr'])
    runtime.stdout = '\n'.join(result['stdout'])
    runtime.merged = '\n'.join(result['merged'])
    return runtime


class CommandLine(BaseInterface):
    """Implements functionality to interact with command line programs
    class must be instantiated with a command argument

    Parameters
    ----------

    command : string
        define base immutable `command` you wish to run

    args : string, optional
        optional arguments passed to base `command`


    Examples
    --------
    >>> import pprint
    >>> from nipype.interfaces.base import CommandLine
    >>> cli = CommandLine(command='ls', environ={'DISPLAY': ':1'})
    >>> cli.inputs.args = '-al'
    >>> cli.cmdline
    'ls -al'

    # Use get_traitsfree() to check all inputs set
    >>> pprint.pprint(cli.inputs.get_traitsfree())  # doctest:
    {'args': '-al',
     'environ': {'DISPLAY': ':1'}}

    >>> cli.inputs.get_hashval()[0][0]
    ('args', '-al')
    >>> cli.inputs.get_hashval()[1]
    '11c37f97649cd61627f4afe5136af8c0'

    """
    input_spec = CommandLineInputSpec
    _cmd_prefix = ''
    _cmd = None
    _version = None
    _terminal_output = 'stream'

    @classmethod
    def set_default_terminal_output(cls, output_type):
        """Set the default terminal output for CommandLine Interfaces.

        This method is used to set default terminal output for
        CommandLine Interfaces.  However, setting this will not
        update the output type for any existing instances.  For these,
        assign the <instance>.terminal_output.
        """

        if output_type in VALID_TERMINAL_OUTPUT:
            cls._terminal_output = output_type
        else:
            raise AttributeError(
                'Invalid terminal output_type: %s' % output_type)

    @classmethod
    def help(cls, returnhelp=False):
        allhelp = 'Wraps command **{cmd}**\n\n{help}'.format(
            cmd=cls._cmd, help=super(CommandLine, cls).help(returnhelp=True))
        if returnhelp:
            return allhelp
        print(allhelp)

    def __init__(self, command=None, terminal_output=None, **inputs):
        super(CommandLine, self).__init__(**inputs)
        self._environ = None
        # Set command. Input argument takes precedence
        self._cmd = command or getattr(self, '_cmd', None)

        # Store dependencies in runtime object
        self._ldd = str2bool(
            config.get('execution', 'get_linked_libs', 'true'))

        if self._cmd is None:
            raise Exception("Missing command")

        if terminal_output is not None:
            self.terminal_output = terminal_output

    @property
    def cmd(self):
        """sets base command, immutable"""
        return self._cmd

    @property
    def cmdline(self):
        """ `command` plus any arguments (args)
        validates arguments and generates command line"""
        self._check_mandatory_inputs()
        allargs = [self._cmd_prefix + self.cmd] + self._parse_inputs()
        return ' '.join(allargs)

    @property
    def terminal_output(self):
        return self._terminal_output

    @terminal_output.setter
    def terminal_output(self, value):
        if value not in VALID_TERMINAL_OUTPUT:
            raise RuntimeError(
                'Setting invalid value "%s" for terminal_output. Valid values are '
                '%s.' % (value,
                         ', '.join(['"%s"' % v
                                    for v in VALID_TERMINAL_OUTPUT])))
        self._terminal_output = value

    def raise_exception(self, runtime):
        raise RuntimeError(
            ('Command:\n{cmdline}\nStandard output:\n{stdout}\n'
             'Standard error:\n{stderr}\nReturn code: {returncode}'
             ).format(**runtime.dictcopy()))

    def _get_environ(self):
        return getattr(self.inputs, 'environ', {})

    def version_from_command(self, flag='-v', cmd=None):
        iflogger.warning('version_from_command member of CommandLine was '
                         'Deprecated in nipype-1.0.0 and deleted in 1.1.0')
        if cmd is None:
            cmd = self.cmd.split()[0]

        env = dict(os.environ)
        if which(cmd, env=env):
            out_environ = self._get_environ()
            env.update(out_environ)
            proc = sp.Popen(
                ' '.join((cmd, flag)),
                shell=True,
                env=env,
                stdout=sp.PIPE,
                stderr=sp.PIPE,
            )
            o, e = proc.communicate()
            return o

    def _run_interface(self, runtime, correct_return_codes=(0, )):
        """Execute command via subprocess

        Parameters
        ----------
        runtime : passed by the run function

        Returns
        -------
        runtime : updated runtime information
            adds stdout, stderr, merged, cmdline, dependencies, command_path

        """

        out_environ = self._get_environ()
        # Initialize runtime Bunch
        runtime.stdout = None
        runtime.stderr = None
        runtime.cmdline = self.cmdline
        runtime.environ.update(out_environ)

        # which $cmd
        executable_name = shlex.split(self._cmd_prefix + self.cmd)[0]
        cmd_path = which(executable_name, env=runtime.environ)

        if cmd_path is None:
            raise IOError(
                'No command "%s" found on host %s. Please check that the '
                'corresponding package is installed.' % (executable_name,
                                                         runtime.hostname))

        runtime.command_path = cmd_path
        runtime.dependencies = (get_dependencies(executable_name,
                                                 runtime.environ)
                                if self._ldd else '<skipped>')
        runtime = run_command(runtime, output=self.terminal_output)
        if runtime.returncode is None or \
                runtime.returncode not in correct_return_codes:
            self.raise_exception(runtime)

        return runtime

    def _format_arg(self, name, trait_spec, value):
        """A helper function for _parse_inputs

        Formats a trait containing argstr metadata
        """
        argstr = trait_spec.argstr
        iflogger.debug('%s_%s', name, value)
        if trait_spec.is_trait_type(traits.Bool) and "%" not in argstr:
            # Boolean options have no format string. Just append options if True.
            return argstr if value else None
        # traits.Either turns into traits.TraitCompound and does not have any
        # inner_traits
        elif trait_spec.is_trait_type(traits.List) \
            or (trait_spec.is_trait_type(traits.TraitCompound) and
                isinstance(value, list)):
            # This is a bit simple-minded at present, and should be
            # construed as the default. If more sophisticated behavior
            # is needed, it can be accomplished with metadata (e.g.
            # format string for list member str'ification, specifying
            # the separator, etc.)

            # Depending on whether we stick with traitlets, and whether or
            # not we beef up traitlets.List, we may want to put some
            # type-checking code here as well
            sep = trait_spec.sep if trait_spec.sep is not None else ' '

            if argstr.endswith('...'):
                # repeatable option
                # --id %d... will expand to
                # --id 1 --id 2 --id 3 etc.,.
                argstr = argstr.replace('...', '')
                return sep.join([argstr % elt for elt in value])
            else:
                return argstr % sep.join(str(elt) for elt in value)
        else:
            # Append options using format string.
            return argstr % value

    def _filename_from_source(self, name, chain=None):
        if chain is None:
            chain = []

        trait_spec = self.inputs.trait(name)
        retval = getattr(self.inputs, name)
        source_ext = None
        if not isdefined(retval) or "%s" in retval:
            if not trait_spec.name_source:
                return retval

            # Do not generate filename when excluded by other inputs
            if any(isdefined(getattr(self.inputs, field))
                   for field in trait_spec.xor or ()):
                return retval

            # Do not generate filename when required fields are missing
            if not all(isdefined(getattr(self.inputs, field))
                       for field in trait_spec.requires or ()):
                return retval

            if isdefined(retval) and "%s" in retval:
                name_template = retval
            else:
                name_template = trait_spec.name_template
            if not name_template:
                name_template = "%s_generated"

            ns = trait_spec.name_source
            while isinstance(ns, (list, tuple)):
                if len(ns) > 1:
                    iflogger.warning(
                        'Only one name_source per trait is allowed')
                ns = ns[0]

            if not isinstance(ns, (str, bytes)):
                raise ValueError(
                    'name_source of \'{}\' trait should be an input trait '
                    'name, but a type {} object was found'.format(
                        name, type(ns)))

            if isdefined(getattr(self.inputs, ns)):
                name_source = ns
                source = getattr(self.inputs, name_source)
                while isinstance(source, list):
                    source = source[0]

                # special treatment for files
                try:
                    _, base, source_ext = split_filename(source)
                except (AttributeError, TypeError):
                    base = source
            else:
                if name in chain:
                    raise NipypeInterfaceError(
                        'Mutually pointing name_sources')

                chain.append(name)
                base = self._filename_from_source(ns, chain)
                if isdefined(base):
                    _, _, source_ext = split_filename(base)
                else:
                    # Do not generate filename when required fields are missing
                    return retval

            chain = None
            retval = name_template % base
            _, _, ext = split_filename(retval)
            if trait_spec.keep_extension and (ext or source_ext):
                if (ext is None or not ext) and source_ext:
                    retval = retval + source_ext
            else:
                retval = self._overload_extension(retval, name)
        return retval

    def _gen_filename(self, name):
        raise NotImplementedError

    def _overload_extension(self, value, name=None):
        return value

    def _list_outputs(self):
        metadata = dict(name_source=lambda t: t is not None)
        traits = self.inputs.traits(**metadata)
        if traits:
            outputs = self.output_spec().trait_get()
            for name, trait_spec in list(traits.items()):
                out_name = name
                if trait_spec.output_name is not None:
                    out_name = trait_spec.output_name
                fname = self._filename_from_source(name)
                if isdefined(fname):
                    outputs[out_name] = os.path.abspath(fname)
            return outputs

    def _parse_inputs(self, skip=None):
        """Parse all inputs using the ``argstr`` format string in the Trait.

        Any inputs that are assigned (not the default_value) are formatted
        to be added to the command line.

        Returns
        -------
        all_args : list
            A list of all inputs formatted for the command line.

        """
        all_args = []
        initial_args = {}
        final_args = {}
        metadata = dict(argstr=lambda t: t is not None)
        for name, spec in sorted(self.inputs.traits(**metadata).items()):
            if skip and name in skip:
                continue
            value = getattr(self.inputs, name)
            if spec.name_source:
                value = self._filename_from_source(name)
            elif spec.genfile:
                if not isdefined(value) or value is None:
                    value = self._gen_filename(name)

            if not isdefined(value):
                continue
            arg = self._format_arg(name, spec, value)
            if arg is None:
                continue
            pos = spec.position
            if pos is not None:
                if int(pos) >= 0:
                    initial_args[pos] = arg
                else:
                    final_args[pos] = arg
            else:
                all_args.append(arg)
        first_args = [el for _, el in sorted(initial_args.items())]
        last_args = [el for _, el in sorted(final_args.items())]
        return first_args + all_args + last_args


class StdOutCommandLine(CommandLine):
    input_spec = StdOutCommandLineInputSpec

    def _gen_filename(self, name):
        return self._gen_outfilename() if name == 'out_file' else None

    def _gen_outfilename(self):
        raise NotImplementedError


class MpiCommandLine(CommandLine):
    """Implements functionality to interact with command line programs
    that can be run with MPI (i.e. using 'mpiexec').

    Examples
    --------
    >>> from nipype.interfaces.base import MpiCommandLine
    >>> mpi_cli = MpiCommandLine(command='my_mpi_prog')
    >>> mpi_cli.inputs.args = '-v'
    >>> mpi_cli.cmdline
    'my_mpi_prog -v'

    >>> mpi_cli.inputs.use_mpi = True
    >>> mpi_cli.inputs.n_procs = 8
    >>> mpi_cli.cmdline
    'mpiexec -n 8 my_mpi_prog -v'
    """
    input_spec = MpiCommandLineInputSpec

    @property
    def cmdline(self):
        """Adds 'mpiexec' to begining of command"""
        result = []
        if self.inputs.use_mpi:
            result.append('mpiexec')
            if self.inputs.n_procs:
                result.append('-n %d' % self.inputs.n_procs)
        result.append(super(MpiCommandLine, self).cmdline)
        return ' '.join(result)


class SEMLikeCommandLine(CommandLine):
    """In SEM derived interface all outputs have corresponding inputs.
    However, some SEM commands create outputs that are not defined in the XML.
    In those cases one has to create a subclass of the autogenerated one and
    overload the _list_outputs method. _outputs_from_inputs should still be
    used but only for the reduced (by excluding those that do not have
    corresponding inputs list of outputs.
    """

    def _list_outputs(self):
        outputs = self.output_spec().trait_get()
        return self._outputs_from_inputs(outputs)

    def _outputs_from_inputs(self, outputs):
        for name in list(outputs.keys()):
            corresponding_input = getattr(self.inputs, name)
            if isdefined(corresponding_input):
                if (isinstance(corresponding_input, bool)
                        and corresponding_input):
                    outputs[name] = \
                        os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(corresponding_input, list):
                        outputs[name] = [
                            os.path.abspath(inp) for inp in corresponding_input
                        ]
                    else:
                        outputs[name] = os.path.abspath(corresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in list(self._outputs_filenames.keys()):
            if isinstance(value, bool):
                if value:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(SEMLikeCommandLine, self)._format_arg(name, spec, value)


class LibraryBaseInterface(BaseInterface):
    _pkg = None
    imports = ()

    def __init__(self, check_import=True, *args, **kwargs):
        super(LibraryBaseInterface, self).__init__(*args, **kwargs)
        if check_import:
            import importlib
            failed_imports = []
            for pkg in (self._pkg,) + tuple(self.imports):
                try:
                    importlib.import_module(pkg)
                except ImportError:
                    failed_imports.append(pkg)
            if failed_imports:
                iflogger.warn('Unable to import %s; %s interface may fail to '
                              'run', failed_imports, self.__class__.__name__)

    @property
    def version(self):
        if self._version is None:
            import importlib
            try:
                self._version = importlib.import_module(self._pkg).__version__
            except (ImportError, AttributeError):
                pass
        return super(LibraryBaseInterface, self).version


class PackageInfo(object):
    _version = None
    version_cmd = None
    version_file = None

    @classmethod
    def version(klass):
        if klass._version is None:
            if klass.version_cmd is not None:
                try:
                    clout = CommandLine(
                        command=klass.version_cmd,
                        resource_monitor=False,
                        terminal_output='allatonce').run()
                except IOError:
                    return None

                raw_info = clout.runtime.stdout
            elif klass.version_file is not None:
                try:
                    with open(klass.version_file, 'rt') as fobj:
                        raw_info = fobj.read()
                except OSError:
                    return None
            else:
                return None

            klass._version = klass.parse_version(raw_info)

        return klass._version

    @staticmethod
    def parse_version(raw_info):
        raise NotImplementedError
