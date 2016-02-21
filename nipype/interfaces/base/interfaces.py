# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Base interfaces that will be implemented with installed packages
with implementation in nipype (:module:`nipype.interfaces`) or
pure python implementations (:module:`nipype.algorithms`).

"""

from __future__ import print_function
from __future__ import division

from copy import deepcopy
import os
import os.path as op
import platform
from socket import getfqdn
import subprocess
from datetime import datetime as dt
from dateutil.parser import parse as parseutc

from future import standard_library
standard_library.install_aliases()
from builtins import range
from builtins import object

from configparser import NoOptionError
from traits.api import Interface, Instance, provides, HasTraits
from .traits_extension import traits
from ...utils.misc import trim, str2bool
from ...utils.provenance import write_provenance
from ... import config, logging, LooseVersion
from ... import __version__
from ...external.six import string_types

# Make all the traits and spec interfaces available through base
# for backwards compatibility, even though import * is discouraged
# in production environments.
from .traits_extension import isdefined, Command
from .specs import (IInputSpec, IOutputSpec, IInputCommandLineSpec,
                    BaseInputSpec, CommandLineInputSpec,
                    StdOutCommandLineInputSpec, StdOutCommandLineOutputSpec,
                    MpiCommandLineInputSpec,
                    SEMLikeCommandLineInputSpec)
from .runtime import (Bunch, InterfaceResult, get_dependencies,
                      run_command, raise_exception)

IFLOGGER = logging.getLogger('interface')
__docformat__ = 'restructuredtext'


class IBase(Interface):
    """This is an abstract definition for Interface objects.

    It provides no functionality.  It defines the necessary attributes
    and methods all Interface objects should have.

    """

    @classmethod
    def help(cls, returnhelp=False):
        """Prints class help"""

    def version(self):
        """Provides the underlying interface version"""

    def pre_run(self, **inputs):
        """Hook executed before running"""

    def run(self, dry_run=False, **inputs):
        """
        The interface runner

        Parameters
        ----------
        inputs : allows the interface settings to be updated

        Returns
        -------
        results :  an InterfaceResult object containing a copy of the instance
        that was executed, provenance information and, if successful, results
        """

    def post_run(self):
        """Hook executed after running"""

    def _aggregate_outputs(self):
        """Fill in ouputs after running interface"""

class ICommandBase(Interface):
    """Abstract class for interfaces wrapping a command line"""

    @property
    def cmdline(self):
        """The command line that is to be executed"""


@provides(IBase)
class BaseInterface(HasTraits):
    """Implements common interface functionality.

    """
    inputs = Instance(IInputSpec)
    outputs = Instance(IOutputSpec)
    _input_spec = BaseInputSpec
    # _output_spec =
    status = traits.Enum('waiting', 'starting', 'running', 'ending',
                         'errored', 'finished')
    version = traits.Str
    redirect_x = traits.Bool
    can_resume = traits.Bool(True)
    always_run = traits.Bool
    ignore_exception = traits.Bool

    def __init__(self, **inputs):
        self.inputs = self._input_spec()
        self.inputs.set(**inputs)

    def _run_wrapper(self, runtime):
        sysdisplay = os.getenv('DISPLAY')
        if self.redirect_x:
            try:
                from xvfbwrapper import Xvfb
            except ImportError:
                IFLOGGER.error('Xvfb wrapper could not be imported')
                raise

            vdisp = Xvfb(nolisten='tcp')
            vdisp.start()
            vdisp_num = vdisp.vdisplay_num

            IFLOGGER.info('Redirecting X to :%d', vdisp_num)
            runtime.environ['DISPLAY'] = ':%d' % vdisp_num

        runtime = self._run_interface(runtime)

        if self.redirect_x:
            if sysdisplay is None:
                os.unsetenv('DISPLAY')
            else:
                os.environ['DISPLAY'] = sysdisplay

            IFLOGGER.info('Freeing X :%d', vdisp_num)
            vdisp.stop()
            _unlock_display(vdisp_num)

        return runtime

    def _run_interface(self, runtime, *kwargs):
        """ Core function that executes interface
        """
        raise NotImplementedError

    def pre_run(self, **inputs):
        """ Implementation of the pre-execution hook"""
        self.inputs.set(**inputs)
        self.inputs.check_inputs()
        if not self.version:
            if str2bool(config.get('execution', 'stop_on_unknown_version')):
                raise ValueError('Interface %s has no version information' %
                                 self.__class__.__name__)
        else:
            self.inputs.check_version(LooseVersion(str(self.version)))

    def post_run(self):
        """ Implementation of the post-execution hook"""
        pass

    def _aggregate_outputs(self):
        # ns_outputs = {}
        # for ns_input, ns_spec in list(self.inputs.namesource_items()):
        #     ns_pointer = getattr(ns_spec, 'out_name', None)
        #     if ns_pointer is not None:
        #         ns_outputs[ns_pointer] = ns_input

        # # Search for inputs with the same name
        # for out_name, spec in list(self.outputs.items()):
        #     if out_name in ns_outputs.keys():
        #         value = getattr(self.inputs, ns_outputs[out_name], Undefined)
        #     else:
        #         value = getattr(self.inputs, out_name, Undefined)

        #     if isdefined(value):
        #         setattr(self.outputs, out_name, op.abspath(value))

        # # Search for outputs with name source
        # for out_name, spec in self.outputs.namesource_items():
        #     if isdefined(getattr(self.outputs, out_name)):
        #         continue
        #     value = self.outputs.format_ns(spec.name_source, out_name, self.inputs)
        #     setattr(self.outputs, out_name, value)
        pass

    def run(self, dry_run=False, **inputs):
        """Basic implementation of the interface runner"""
        self.status = 'starting'
        self.pre_run(**inputs)
        # initialize provenance tracking
        runtime = Bunch(
            cwd=os.getcwd(), returncode=None, duration=None, environ=deepcopy(dict(os.environ)),
            startTime=dt.isoformat(dt.utcnow()), endTime=None, traceback=None,
            platform=platform.platform(), hostname=getfqdn(), version=self.version)

        self.status = 'running'
        exception = None
        try:
            if not dry_run:
                runtime = self._run_wrapper(runtime)
            else:
                runtime = self._dry_run(runtime)
        except Exception as error:  # pylint: disable=W0703
            runtime, exception = self.handle_error(runtime, error)
            if not self.ignore_exception:
                raise
        finally:
            runtime.endTime = dt.isoformat(dt.utcnow())
            timediff = parseutc(runtime.endTime) - parseutc(runtime.startTime)
            runtime.duration = (timediff.days * 86400 + timediff.seconds +
                                timediff.microseconds / 1e5)
            results = InterfaceResult(self.__class__, runtime,
                                      inputs=self.inputs.get_traitsfree())

            if exception is None:
                self.status = 'ending'
                self._aggregate_outputs()
                self.post_run()
                results.outputs = self.outputs

            prov_record = None
            if str2bool(config.get('execution', 'write_provenance')):
                prov_record = write_provenance(results)
            results.provenance = prov_record

        if exception is None:
            self.status = 'finished'
        return results

    def handle_error(self, runtime, exception):
        import traceback
        self.status = 'errored'
        message = ["Interface %s failed to run." % self.__class__.__name__]
        if config.get('logging', 'interface_level', 'info').lower() == 'debug':
            message += ["Inputs:\n%s\n" % str(self.inputs)]

        if len(exception.args) == 1 and isinstance(exception.args[0], string_types):
            message.insert(0, exception.args[0])
        else:
            message += list(exception.args)
        # exception raising inhibition for special cases
        runtime.traceback = traceback.format_exc()
        runtime.traceback_args = message  # pylint: disable=W0201
        return runtime, message

    @classmethod
    def help(cls, returnhelp=False):
        """ Prints class help """

        docstring = ['']
        if cls.__doc__:
            docstring = trim(cls.__doc__).split('\n') + docstring

        allhelp = '\n'.join(docstring + cls._input_spec.help() + cls._output_spec.help())
        if returnhelp:
            return allhelp
        print(allhelp)


@provides(IBase, ICommandBase)
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

    >>> pprint.pprint(cli.inputs.trait_get())  # doctest: +NORMALIZE_WHITESPACE
    {'args': '-al',
     'environ': {'DISPLAY': ':1'},
     'ignore_exception': False,
     'terminal_output': 'stream'}

    >>> cli.inputs.get_hashval()
    ([('args', '-al')], '11c37f97649cd61627f4afe5136af8c0')

    """

    _cmd = None
    _input_spec = CommandLineInputSpec
    #_output_spec = OutputSpec
    inputs = Instance(IInputCommandLineSpec)
    outputs = Instance(IOutputSpec)
    environ = traits.DictStrStr(dict(os.environ), desc='Environment variables')
    command = Command
    terminal_output = traits.Enum(
        'stream', 'allatonce', 'file', 'none',
        desc='Control terminal output: `stream` - displays to terminal immediately (default), '
             '`allatonce` - waits till command is finished to display output, `file` - '
             'writes output to file, `none` - output is ignored')

    def _environ_default(self):
        return dict(os.environ)

    def _redirect_x_changed(self, new):
        if not new:
            try:
                display_var = config.get('execution', 'display_variable')
                self.environ['DISPLAY'] = display_var
            except NoOptionError:
                pass


    def __init__(self, command=None, environ=None, **inputs):
        # Force refresh of the redirect_x trait
        self._redirect_x_changed(self.redirect_x)

        # First modify environment variables if passed
        if environ is not None:
            for k, v in list(environ.items()):
                self.environ[k] = v

        # Set command to force validation
        if command is not None:
            self.command = command
        elif self._cmd is not None:
            self.command = self._cmd
        else:
            raise RuntimeError('CommandLine interfaces require'
                               ' the definition of a command')

        super(CommandLine, self).__init__(**inputs)


    @property
    def cmdline(self):
        """ `command` plus any arguments (args)
        validates arguments and generates command line"""
        self.inputs.check_inputs()
        allargs = self.inputs.parse_args()
        allargs.insert(0, self._cmd)
        return ' '.join(allargs)

    def _run_wrapper(self, runtime):
        runtime = self._run_interface(runtime)
        return runtime

    def _run_interface(self, runtime, **kwargs):
        """Execute command via subprocess

        Parameters
        ----------
        runtime : passed by the run function

        Returns
        -------
        runtime : updated runtime information
            adds stdout, stderr, merged, cmdline, dependencies, command_path

        """
        correct_return_codes = [0]
        if 'correct_return_codes' in kwargs.keys():
            correct_return_codes = kwargs[correct_return_codes]

        runtime.environ.update(self.environ)
        setattr(runtime, 'stdout', None)
        setattr(runtime, 'stderr', None)
        setattr(runtime, 'cmdline', self.cmdline)
        setattr(runtime, 'command_path', self.trait('command').path)
        setattr(runtime, 'dependencies', get_dependencies(
            self.command.split()[0], runtime.environ))
        runtime = run_command(runtime, output=self.terminal_output,
                              redirect_x=self.redirect_x)
        if runtime.returncode is None or \
                runtime.returncode not in correct_return_codes:
            raise_exception(runtime)
        return runtime

    def version_from_command(self, flag='-v'):
        """Call command -v to get version"""
        cmdname = self.command.split()[0]
        proc = subprocess.Popen(
            ' '.join((cmdname, flag)), shell=True, env=self.environ,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,)
        out, _ = proc.communicate()
        return out

    @classmethod
    def help(cls, returnhelp=False):
        allhelp = super(CommandLine, cls).help(returnhelp=True)
        allhelp = "Wraps command ``%s``\n\n" % cls.command + allhelp

        if returnhelp:
            return allhelp
        print(allhelp)

@provides(IBase, ICommandBase)
class StdOutCommandLine(CommandLine):
    """A command line that writes into the output stream"""
    _input_spec = StdOutCommandLineInputSpec
    _output_spec = StdOutCommandLineOutputSpec


@provides(IBase, ICommandBase)
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
    _input_spec = MpiCommandLineInputSpec

    @property
    def cmdline(self):
        """Adds 'mpiexec' to begining of command"""
        result = []
        if self.inputs.use_mpi:
            result.append('mpiexec')
            if isdefined(self.inputs.n_procs):
                result.append('-n %d' % self.inputs.n_procs)
        result.append(super(MpiCommandLine, self).cmdline)
        return ' '.join(result)


@provides(IBase, ICommandBase)
class SEMLikeCommandLine(CommandLine):
    """In SEM derived interface all outputs have corresponding inputs.
    However, some SEM commands create outputs that are not defined in the XML.
    In those cases one has to create a subclass of the autogenerated one and
    overload the _list_outputs method. _outputs_from_inputs should still be
    used but only for the reduced (by excluding those that do not have
    corresponding inputs list of outputs.
    """
    _input_spec = SEMLikeCommandLineInputSpec

    def post_run(self):
        for name in list(self.outputs.keys()):
            corresponding_input = getattr(self.inputs, name)
            if isdefined(corresponding_input):
                if (isinstance(corresponding_input, bool) and
                        corresponding_input):
                    setattr(self.outputs, name, op.abspath(
                        self._outputs_filenames[name]))
                else:
                    if isinstance(corresponding_input, list):
                        setattr(self.outputs, name,
                                [op.abspath(inp) for inp in corresponding_input])
                    else:
                        setattr(self.outputs, name, op.abspath(corresponding_input))

def _unlock_display(ndisplay):
    lockf = op.join('/tmp', '.X%d-lock' % ndisplay)
    try:
        os.remove(lockf)
    except:
        return False
    return True
