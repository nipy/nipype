# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Implementation for the InterfaceResult type and other requirements
"""
from __future__ import print_function
from __future__ import division

from copy import deepcopy
import os
import os.path as op
import sys
import select
import errno
import subprocess
from datetime import datetime as dt

from string import Template

from future import standard_library
standard_library.install_aliases()
from builtins import range
from builtins import object

from ...utils.misc import is_container
from ...utils.filemanip import md5
from ... import logging


IFLOGGER = logging.getLogger('interface')
__docformat__ = 'restructuredtext'


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
    >>> from nipype.interfaces.base import Bunch
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

def raise_exception(runtime):
    message = "Command:\n" + runtime.cmdline + "\n"
    message += "Standard output:\n" + runtime.stdout + "\n"
    message += "Standard error:\n" + runtime.stderr + "\n"
    message += "Return code: " + str(runtime.returncode)
    raise RuntimeError(message)
