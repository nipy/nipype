# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Package contains interfaces for using existing functionality in other packages

Exaples  FSL, matlab/SPM , afni

Requires Packages to be installed
"""

from __future__ import print_function
from __future__ import division

from copy import deepcopy
import errno
import os
import os.path as op
import platform
from socket import getfqdn
from string import Template
import select
import subprocess
import sys
from datetime import datetime as dt
from dateutil.parser import parse as parseutc

from future import standard_library
standard_library.install_aliases()
from builtins import range
from builtins import object

from configparser import NoOptionError
from ..utils.filemanip import md5, FileNotFoundError
from ..utils.misc import trim, str2bool, is_container

# Make all the traits and spec interfaces available through base
# for backwards compatibility, even though import * is discouraged
# in production environments.
from .traits_extension import *  # pylint: disable=W0611
from .specs import *  # pylint: disable=W0611
#from .traits_extension import isdefined, Undefined
# from .specs import (BaseInterfaceInputSpec, CommandLineInputSpec,
#                     StdOutCommandLineInputSpec, StdOutCommandLineOutputSpec,
#                     MpiCommandLineInputSpec,
#                     SEMLikeCommandLineInputSpec, TraitedSpec)
from ..utils.provenance import write_provenance
from .. import config, logging, LooseVersion
from .. import __version__
from ..external.six import string_types

IFLOGGER = logging.getLogger('interface')
__docformat__ = 'restructuredtext'


def _unlock_display(ndisplay):
    lockf = op.join('/tmp', '.X%d-lock' % ndisplay)
    try:
        os.remove(lockf)
    except:
        return False

    return True


def _exists_in_path(cmd, environ):
    """
    Based on a code snippet from
     http://orip.org/2009/08/python-checking-if-executable-exists-in.html
    """
    # Read environ fron variable, use system's environ as failback
    input_environ = environ.get("PATH", os.environ.get("PATH", ""))
    extensions = os.environ.get("PATHEXT", "").split(os.pathsep)
    for directory in input_environ.split(os.pathsep):
        base = op.join(directory, cmd)
        options = [base] + [(base + ext) for ext in extensions]
        for filename in options:
            if op.exists(filename):
                return True, filename
    return False, None


def load_template(name):
    """Load a template from the script_templates directory

    Parameters
    ----------
    name : str
        The name of the file to load

    Returns
    -------
    template : string.Template

    """

    full_fname = op.join(op.dirname(__file__),
                              'script_templates', name)
    template_file = open(full_fname)
    template = Template(template_file.read())
    template_file.close()
    return template


class Bunch(object):
    """Dictionary-like class that provides attribute-style access to it's items.

    A `Bunch` is a simple container that stores it's items as class
    attributes.  Internally all items are stored in a dictionary and
    the class exposes several of the dictionary methods.

    Examples
    --------
    >>> from nipype.interfaces.specs import Bunch
    >>> inputs = Bunch(infile='subj.nii', fwhm=6.0, register_to_mean=True)
    >>> inputs
    Bunch(fwhm=6.0, infile='subj.nii', register_to_mean=True)
    >>> inputs.register_to_mean = False
    >>> inputs
    Bunch(fwhm=6.0, infile='subj.nii', register_to_mean=False)


    Notes
    -----
    The Bunch pattern came from the Python Cookbook:

    .. [1] A. Martelli, D. Hudgeon, "Collecting a Bunch of Named
           Items", Python Cookbook, 2nd Ed, Chapter 4.18, 2005.

    """

    def __init__(self, *args, **kwargs):
        self.__dict__.update(*args, **kwargs)

    def update(self, *args, **kwargs):
        """update existing attribute, or create new attribute

        Note: update is very much like HasTraits.set"""
        self.__dict__.update(*args, **kwargs)

    def items(self):
        """iterates over bunch attributes as key, value pairs"""
        return list(self.__dict__.items())

    def iteritems(self):
        """iterates over bunch attributes as key, value pairs"""
        IFLOGGER.warn('iteritems is deprecated, use items instead')
        return list(self.items())

    def get(self, *args):
        """Support dictionary get() functionality
        """
        return self.__dict__.get(*args)

    def set(self, **kwargs):
        """Support dictionary get() functionality
        """
        return self.__dict__.update(**kwargs)

    def dictcopy(self):
        """returns a deep copy of existing Bunch as a dictionary"""
        return deepcopy(self.__dict__)

    def __repr__(self):
        """representation of the sorted Bunch as a string

        Currently, this string representation of the `inputs` Bunch of
        interfaces is hashed to determine if the process' dirty-bit
        needs setting or not. Till that mechanism changes, only alter
        this after careful consideration.
        """
        outstr = ['Bunch(']
        first = True
        for k, input_value in sorted(self.items()):
            if not first:
                outstr.append(', ')
            if isinstance(input_value, dict):
                pairs = []
                for key, value in sorted(input_value.items()):
                    pairs.append("'%s': %s" % (key, value))
                input_value = '{' + ', '.join(pairs) + '}'
                outstr.append('%s=%s' % (k, input_value))
            else:
                outstr.append('%s=%r' % (k, input_value))
            first = False
        outstr.append(')')
        return ''.join(outstr)

    def _get_bunch_hash(self):
        """Return a dictionary of our items with hashes for each file.

        Searches through dictionary items and if an item is a file, it
        calculates the md5 hash of the file contents and stores the
        file name and hash value as the new key value.

        However, the overall bunch hash is calculated only on the hash
        value of a file. The path and name of the file are not used in
        the overall hash calculation.

        Returns
        -------
        dict_withhash : dict
            Copy of our dictionary with the new file hashes included
            with each file.
        hashvalue : str
            The md5 hash value of the `dict_withhash`

        """

        infile_list = []
        for key, val in list(self.items()):
            if is_container(val):
                # XXX - SG this probably doesn't catch numpy arrays
                # containing embedded file names either.
                if isinstance(val, dict):
                    # XXX - SG should traverse dicts, but ignoring for now
                    item = None
                else:
                    if len(val) == 0:
                        raise AttributeError('%s attribute is empty' % key)
                    item = val[0]
            else:
                item = val
            try:
                if op.isfile(item):
                    infile_list.append(key)
            except TypeError:
                # `item` is not a file or string.
                continue
        dict_withhash = self.dictcopy()
        dict_nofilename = self.dictcopy()
        for item in infile_list:
            dict_withhash[item] = self._hash_infile(dict_withhash, item)
            dict_nofilename[item] = [val[1] for val in dict_withhash[item]]
        # Sort the items of the dictionary, before hashing the string
        # representation so we get a predictable order of the
        # dictionary.
        sorted_dict = str(sorted(dict_nofilename.items()))
        return dict_withhash, md5(sorted_dict.encode()).hexdigest()

    def _hash_infile(self, adict, key):
        """Compute hashes of files"""
        # Inject file hashes into adict[key]
        stuff = adict[key]
        if not is_container(stuff):
            stuff = [stuff]
        file_list = []
        for fname in stuff:
            if op.isfile(fname):
                md5obj = md5()
                with open(fname, 'rb') as filep:
                    while True:
                        data = filep.read(8192)
                        if not data:
                            break
                        md5obj.update(data)
                md5hex = md5obj.hexdigest()
            else:
                md5hex = None
            file_list.append((fname, md5hex))
        return file_list

    def __pretty__(self, p, cycle):
        """Support for the pretty module

        pretty is included in ipython.externals for ipython > 0.10"""
        if cycle:
            p.text('Bunch(...)')
        else:
            p.begin_group(6, 'Bunch(')
            first = True
            for k, input_value in sorted(self.items()):
                if not first:
                    p.text(',')
                    p.breakable()
                p.text(k + '=')
                p.pretty(input_value)
                first = False
            p.end_group(6, ')')


class InterfaceResult(object):
    """Object that contains the results of running a particular Interface.

    Attributes
    ----------
    version : version of this Interface result object (a readonly property)
    interface : class type
        A copy of the `Interface` class that was run to generate this result.
    inputs :  a traits free representation of the inputs
    outputs : Bunch
        An `Interface` specific Bunch that contains all possible files
        that are generated by the interface.  The `outputs` are used
        as the `inputs` to another node when interfaces are used in
        the pipeline.
    runtime : Bunch

        Contains attributes that describe the runtime environment when
        the `Interface` was run.  Contains the attributes:

        * cmdline : The command line string that was executed
        * cwd : The directory the ``cmdline`` was executed in.
        * stdout : The output of running the ``cmdline``.
        * stderr : Any error messages output from running ``cmdline``.
        * returncode : The code returned from running the ``cmdline``.

    """

    def __init__(self, interface, runtime, inputs=None, outputs=None,
                 provenance=None):
        self._version = 2.0
        self.interface = interface
        self.runtime = runtime
        self.inputs = inputs
        self.outputs = outputs
        self.provenance = provenance

    @property
    def version(self):
        return self._version


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
    def help(cls, returnhelp=False):
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

    @property
    def version(self):
        raise NotImplementedError

    def _pre_run(self, **inputs):
        raise NotImplementedError

    def _post_run(self, **inputs):
        raise NotImplementedError


    def run(self):
        """Execute the command."""
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

    """
    input_spec = BaseInterfaceInputSpec
    output_spec = TraitedSpec
    _version = None
    _additional_metadata = []
    _redirect_x = False

    def __init__(self, **inputs):
        if not self.input_spec:
            raise Exception('No input_spec in class: %s' %
                            self.__class__.__name__)
        self.inputs = self.input_spec(**inputs)
        self.outputs = self.output_spec()

    @classmethod
    def help(cls, returnhelp=False):
        """ Prints class help """

        if cls.__doc__:
            # docstring = cls.__doc__.split('\n')
            # docstring = [trim(line, '') for line in docstring]
            docstring = trim(cls.__doc__).split('\n') + ['']
        else:
            docstring = ['']

        allhelp = '\n'.join(docstring + ['Inputs::'] + cls.input_spec().help() + [''] +
                            ['Outputs::', ''] + cls.output_spec().help() + [''])
        if returnhelp:
            return allhelp
        else:
            print(allhelp)

    def _run_wrapper(self, runtime):
        sysdisplay = os.getenv('DISPLAY')
        if self._redirect_x:
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

        if self._redirect_x:
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

    def _pre_run(self, **inputs):
        self.outputs = self.output_spec()
        self.inputs.set(**inputs)
        self.inputs.check_inputs()
        self.inputs.update_autonames()
        if self.version:
            self.inputs.check_version(LooseVersion(str(self.version)))

    def _post_run(self):
        if self.output_spec is None:
            IFLOGGER.warn('Interface does not have an output specification')
            return None

        ns_outputs = {}
        for ns_input, ns_spec in list(self.inputs.namesource_items()):
            ns_pointer = getattr(ns_spec, 'out_name', None)
            if ns_pointer is not None:
                ns_outputs[ns_pointer] = ns_input

        # Search for inputs with the same name
        for out_name, spec in list(self.outputs.items()):
            if out_name in ns_outputs.keys():
                value = getattr(self.inputs, ns_outputs[out_name], Undefined)
            else:
                value = getattr(self.inputs, out_name, Undefined)

            if isdefined(value):
                setattr(self.outputs, out_name, op.abspath(value))

        # Search for outputs with name source
        for out_name, spec in self.outputs.namesource_items():
            if isdefined(getattr(self.outputs, out_name)):
                continue
            value = self.outputs.format_ns(spec.name_source, out_name, self.inputs)
            setattr(self.outputs, out_name, value)


    def run(self, **inputs):
        """Execute this interface.

        This interface will not raise an exception if runtime.returncode is
        non-zero.

        Parameters
        ----------
        inputs : allows the interface settings to be updated

        Returns
        -------
        results :  an InterfaceResult object containing a copy of the instance
        that was executed, provenance information and, if successful, results
        """
        interface = self.__class__
        self._pre_run(**inputs)
        # initialize provenance tracking
        env = deepcopy(dict(os.environ))
        runtime = Bunch(
            cwd=os.getcwd(), returncode=None, duration=None, environ=env,
            startTime=dt.isoformat(dt.utcnow()), endTime=None, traceback=None,
            platform=platform.platform(), hostname=getfqdn(), version=self.version)

        try:
            runtime = self._run_wrapper(runtime)
        except Exception as e:  # pylint: disable=W0703
            if len(e.args) == 0:
                e.args = ("")

            message = "\nInterface %s failed to run." % self.__class__.__name__

            if config.has_option('logging', 'interface_level') and \
                    config.get('logging', 'interface_level').lower() == 'debug':
                inputs_str = "Inputs:" + str(self.inputs) + "\n"
            else:
                inputs_str = ''

            if len(e.args) == 1 and isinstance(e.args[0], string_types):
                e.args = (e.args[0] + " ".join([message, inputs_str]),)
            else:
                e.args += (message, )
                if inputs_str != '':
                    e.args += (inputs_str, )

            # exception raising inhibition for special cases
            import traceback
            runtime.traceback = traceback.format_exc()
            runtime.traceback_args = e.args  # pylint: disable=W0201

        runtime.endTime = dt.isoformat(dt.utcnow())
        timediff = parseutc(runtime.endTime) - parseutc(runtime.startTime)
        runtime.duration = (timediff.days * 86400 + timediff.seconds +
                            timediff.microseconds / 1e5)
        results = InterfaceResult(interface, runtime,
                                  inputs=self.inputs.get_traitsfree())

        if runtime.traceback is None:
            self._post_run()
            results.outputs = self.outputs

        prov_record = None
        if str2bool(config.get('execution', 'write_provenance')):
            prov_record = write_provenance(results)
        results.provenance = prov_record

        if (runtime.traceback is not None and
            not getattr(self.inputs, 'ignore_exception', False)):
            raise
        return results

    @property
    def version(self):
        if self._version is None:
            if str2bool(config.get('execution', 'stop_on_unknown_version')):
                raise ValueError('Interface %s has no version information' %
                                 self.__class__.__name__)
        return self._version


class Stream(object):
    """Function to capture stdout and stderr streams with timestamps

    stackoverflow.com/questions/4984549/merge-and-sync-stdout-and-stderr/5188359
    """

    def __init__(self, name, impl):
        self._name = name
        self._impl = impl
        self._buf = ''
        self._rows = []
        self._lastidx = 0

    def fileno(self):
        "Pass-through for file descriptor."
        return self._impl.fileno()

    def read(self, drain=0):
        "Read from the file descriptor. If 'drain' set, read until EOF."
        while self._read(drain) is not None:
            if not drain:
                break

    def _read(self, drain):
        "Read from the file descriptor"
        fd = self.fileno()
        buf = os.read(fd, 4096).decode()
        if not buf and not self._buf:
            return None
        if '\n' not in buf:
            if not drain:
                self._buf += buf
                return []

        # prepend any data previously read, then split into lines and format
        buf = self._buf + buf
        if '\n' in buf:
            tmp, rest = buf.rsplit('\n', 1)
        else:
            tmp = buf
            rest = None
        self._buf = rest
        now = dt.now().isoformat()
        rows = tmp.split('\n')
        self._rows += [(now, '%s %s:%s' % (self._name, now, r), r)
                       for r in rows]
        for idx in range(self._lastidx, len(self._rows)):
            IFLOGGER.info(self._rows[idx][1])
        self._lastidx = len(self._rows)


def run_command(runtime, output=None, timeout=0.01, redirect_x=False):
    """Run a command, read stdout and stderr, prefix with timestamp.

    The returned runtime contains a merged stdout+stderr log with timestamps
    """
    PIPE = subprocess.PIPE

    cmdline = runtime.cmdline
    if redirect_x:
        exist_xvfb, _ = _exists_in_path('xvfb-run', runtime.environ)
        if not exist_xvfb:
            raise RuntimeError('Xvfb was not found, X redirection aborted')
        cmdline = 'xvfb-run -a ' + cmdline

    if output == 'file':
        errfile = op.join(runtime.cwd, 'stderr.nipype')
        outfile = op.join(runtime.cwd, 'stdout.nipype')
        stderr = open(errfile, 'wt')  # t=='text'===default
        stdout = open(outfile, 'wt')

        proc = subprocess.Popen(cmdline,
                                stdout=stdout,
                                stderr=stderr,
                                shell=True,
                                cwd=runtime.cwd,
                                env=runtime.environ)
    else:
        proc = subprocess.Popen(cmdline,
                                stdout=PIPE,
                                stderr=PIPE,
                                shell=True,
                                cwd=runtime.cwd,
                                env=runtime.environ)
    result = {}
    errfile = op.join(runtime.cwd, 'stderr.nipype')
    outfile = op.join(runtime.cwd, 'stdout.nipype')
    if output == 'stream':
        streams = [Stream('stdout', proc.stdout), Stream('stderr', proc.stderr)]

        def _process(drain=0):
            try:
                res = select.select(streams, [], [], timeout)
            except select.error as e:
                IFLOGGER.info(str(e))
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
    if output == 'allatonce':
        stdout, stderr = proc.communicate()
        if stdout and isinstance(stdout, bytes):
            try:
                stdout = stdout.decode()
            except UnicodeDecodeError:
                stdout = stdout.decode("ISO-8859-1")
        if stderr and isinstance(stderr, bytes):
            try:
                stderr = stderr.decode()
            except UnicodeDecodeError:
                stderr = stderr.decode("ISO-8859-1")

        result['stdout'] = str(stdout).split('\n')
        result['stderr'] = str(stderr).split('\n')
        result['merged'] = ''
    if output == 'file':
        ret_code = proc.wait()
        stderr.flush()
        stdout.flush()
        result['stdout'] = [line.strip() for line in open(outfile).readlines()]
        result['stderr'] = [line.strip() for line in open(errfile).readlines()]
        result['merged'] = ''
    if output == 'none':
        proc.communicate()
        result['stdout'] = []
        result['stderr'] = []
        result['merged'] = ''
    runtime.stderr = '\n'.join(result['stderr'])
    runtime.stdout = '\n'.join(result['stdout'])
    runtime.merged = result['merged']
    runtime.returncode = proc.returncode
    return runtime


def get_dependencies(name, environ):
    """Return library dependencies of a dynamically linked executable

    Uses otool on darwin, ldd on linux. Currently doesn't support windows.

    """
    PIPE = subprocess.PIPE
    if sys.platform == 'darwin':
        proc = subprocess.Popen(
            'otool -L `which %s`' % name, stdout=PIPE, stderr=PIPE, shell=True, env=environ)
    elif 'linux' in sys.platform:
        proc = subprocess.Popen(
            'ldd `which %s`' % name, stdout=PIPE, stderr=PIPE, shell=True, env=environ)
    else:
        return 'Platform %s not supported' % sys.platform
    o, _ = proc.communicate()
    return o.rstrip()


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

    input_spec = CommandLineInputSpec
    _cmd = None
    _version = None
    _terminal_output = 'stream'

    def __init__(self, command=None, **inputs):
        super(CommandLine, self).__init__(**inputs)
        self._environ = None
        if not hasattr(self, '_cmd'):
            self._cmd = None
        if self.cmd is None and command is None:
            raise Exception("Missing command")
        if command:
            self._cmd = command
        self.inputs.on_trait_change(self._terminal_output_update,
                                    'terminal_output')
        if not isdefined(self.inputs.terminal_output):
            self.inputs.terminal_output = self._terminal_output
        else:
            self._terminal_output_update()

    def _terminal_output_update(self):
        self._terminal_output = self.inputs.terminal_output

    @classmethod
    def set_default_terminal_output(cls, output_type):
        """Set the default terminal output for CommandLine Interfaces.

        This method is used to set default terminal output for
        CommandLine Interfaces.  However, setting this will not
        update the output type for any existing instances.  For these,
        assign the <instance>.inputs.terminal_output.
        """

        if output_type in ['stream', 'allatonce', 'file', 'none']:
            cls._terminal_output = output_type
        else:
            raise AttributeError('Invalid terminal output_type: %s' %
                                 output_type)

    @property
    def cmd(self):
        """sets base command, immutable"""
        return self._cmd

    @property
    def cmdline(self):
        """ `command` plus any arguments (args)
        validates arguments and generates command line"""
        self.outputs = self.output_spec()
        self.inputs.check_inputs()
        self.inputs.update_autonames()
        allargs = self.inputs.parse_args()
        allargs.insert(0, self.cmd)
        return ' '.join(allargs)

    def raise_exception(self, runtime):
        message = "Command:\n" + runtime.cmdline + "\n"
        message += "Standard output:\n" + runtime.stdout + "\n"
        message += "Standard error:\n" + runtime.stderr + "\n"
        message += "Return code: " + str(runtime.returncode)
        raise RuntimeError(message)

    @classmethod
    def help(cls, returnhelp=False):
        allhelp = super(CommandLine, cls).help(returnhelp=True)
        allhelp = "Wraps command ``%s``\n\n" % cls._cmd + allhelp

        if returnhelp:
            return allhelp
        print(allhelp)

    def _get_environ(self):
        out_environ = {}
        if not self._redirect_x:
            try:
                display_var = config.get('execution', 'display_variable')
                out_environ = {'DISPLAY': display_var}
            except NoOptionError:
                pass
        IFLOGGER.debug(out_environ)
        if isdefined(self.inputs.environ):
            out_environ.update(self.inputs.environ)
        return out_environ

    def version_from_command(self, flag='-v'):
        cmdname = self.cmd.split()[0]
        env = dict(os.environ)
        if _exists_in_path(cmdname, env):
            out_environ = self._get_environ()
            env.update(out_environ)
            proc = subprocess.Popen(' '.join((cmdname, flag)), shell=True, env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,)
            out, _ = proc.communicate()
            return out

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

        setattr(runtime, 'stdout', None)
        setattr(runtime, 'stderr', None)
        setattr(runtime, 'cmdline', self.cmdline)
        out_environ = self._get_environ()
        runtime.environ.update(out_environ)
        executable_name = self.cmd.split()[0]
        exist_val, cmd_path = _exists_in_path(executable_name,
                                              runtime.environ)
        if not exist_val:
            raise IOError("command '%s' could not be found on host %s" %
                          (self.cmd.split()[0], runtime.hostname))
        setattr(runtime, 'command_path', cmd_path)
        setattr(runtime, 'dependencies', get_dependencies(executable_name,
                                                          runtime.environ))
        runtime = run_command(runtime, output=self.inputs.terminal_output,
                              redirect_x=self._redirect_x)
        if runtime.returncode is None or \
                runtime.returncode not in correct_return_codes:
            self.raise_exception(runtime)

        return runtime


class StdOutCommandLine(CommandLine):
    """A command line that writes into the output stream"""
    input_spec = StdOutCommandLineInputSpec
    output_spec = StdOutCommandLineOutputSpec


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
            if isdefined(self.inputs.n_procs):
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
    input_spec = SEMLikeCommandLineInputSpec

    def _post_run(self):
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
