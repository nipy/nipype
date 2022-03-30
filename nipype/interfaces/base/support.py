# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""

Miscellaneous tools to support Interface functionality
......................................................

"""
import os
from contextlib import AbstractContextManager
from copy import deepcopy
from textwrap import wrap
import re
from datetime import datetime as dt
from dateutil.parser import parse as parseutc
import platform

from ... import logging, config
from ...utils.misc import is_container, rgetcwd
from ...utils.filemanip import md5, hash_infile

iflogger = logging.getLogger("nipype.interface")

HELP_LINEWIDTH = 70


class RuntimeContext(AbstractContextManager):
    """A context manager to run NiPype interfaces."""

    __slots__ = ("_runtime", "_resmon", "_ignore_exc")

    def __init__(self, resource_monitor=False, ignore_exception=False):
        """Initialize the context manager object."""
        self._ignore_exc = ignore_exception
        _proc_pid = os.getpid()
        if resource_monitor:
            from ...utils.profiler import ResourceMonitor
        else:
            from ...utils.profiler import ResourceMonitorMock as ResourceMonitor

        self._resmon = ResourceMonitor(
            _proc_pid,
            freq=float(config.get("execution", "resource_monitor_frequency", 1)),
        )

    def __call__(self, interface, cwd=None, redirect_x=False):
        """Generate a new runtime object."""
        # Tear-up: get current and prev directories
        _syscwd = rgetcwd(error=False)  # Recover when wd does not exist
        if cwd is None:
            cwd = _syscwd

        self._runtime = Bunch(
            cwd=str(cwd),
            duration=None,
            endTime=None,
            environ=deepcopy(dict(os.environ)),
            hostname=platform.node(),
            interface=interface.__class__.__name__,
            platform=platform.platform(),
            prevcwd=str(_syscwd),
            redirect_x=redirect_x,
            resmon=self._resmon.fname or "off",
            returncode=None,
            startTime=None,
            version=interface.version,
        )
        return self

    def __enter__(self):
        """Tear-up the execution of an interface."""
        if self._runtime.redirect_x:
            self._runtime.environ["DISPLAY"] = config.get_display()

        self._runtime.startTime = dt.isoformat(dt.utcnow())
        self._resmon.start()
        # TODO: Perhaps clean-up path and ensure it exists?
        os.chdir(self._runtime.cwd)
        return self._runtime

    def __exit__(self, exc_type, exc_value, exc_tb):
        """Tear-down interface execution."""
        self._runtime.endTime = dt.isoformat(dt.utcnow())
        timediff = parseutc(self._runtime.endTime) - parseutc(self._runtime.startTime)
        self._runtime.duration = (
            timediff.days * 86400 + timediff.seconds + timediff.microseconds / 1e6
        )
        # Collect monitored data
        for k, v in self._resmon.stop().items():
            setattr(self._runtime, k, v)

        os.chdir(self._runtime.prevcwd)

        if exc_type is not None or exc_value is not None or exc_tb is not None:
            import traceback

            # Retrieve the maximum info fast
            self._runtime.traceback = "".join(
                traceback.format_exception(exc_type, exc_value, exc_tb)
            )
            # Gather up the exception arguments and append nipype info.
            exc_args = exc_value.args if getattr(exc_value, "args") else tuple()
            exc_args += (
                f"An exception of type {exc_type.__name__} occurred while "
                f"running interface {self._runtime.interface}.",
            )
            self._runtime.traceback_args = ("\n".join([f"{arg}" for arg in exc_args]),)

            if self._ignore_exc:
                return True

        if hasattr(self._runtime, "cmdline"):
            retcode = self._runtime.returncode
            if retcode not in self._runtime.success_codes:
                self._runtime.traceback = (
                    f"RuntimeError: subprocess exited with code {retcode}."
                )

    @property
    def runtime(self):
        return self._runtime


class NipypeInterfaceError(Exception):
    """Custom error for interfaces"""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "{}".format(self.value)


class Bunch(object):
    """
    Dictionary-like class that provides attribute-style access to its items.

    A ``Bunch`` is a simple container that stores its items as class
    attributes [1]_. Internally all items are stored in a dictionary and
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

    References
    ----------
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
        iflogger.warning("iteritems is deprecated, use items instead")
        return list(self.items())

    def get(self, *args):
        """Support dictionary get() functionality"""
        return self.__dict__.get(*args)

    def set(self, **kwargs):
        """Support dictionary get() functionality"""
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
        outstr = ["Bunch("]
        first = True
        for k, v in sorted(self.items()):
            if not first:
                outstr.append(", ")
            if isinstance(v, dict):
                pairs = []
                for key, value in sorted(v.items()):
                    pairs.append("'%s': %s" % (key, value))
                v = "{" + ", ".join(pairs) + "}"
                outstr.append("%s=%s" % (k, v))
            else:
                outstr.append("%s=%r" % (k, v))
            first = False
        outstr.append(")")
        return "".join(outstr)

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
                        raise AttributeError("%s attribute is empty" % key)
                    item = val[0]
            else:
                item = val
            try:
                if isinstance(item, str) and os.path.isfile(item):
                    infile_list.append(key)
            except TypeError:
                # `item` is not a file or string.
                continue
        dict_withhash = self.dictcopy()
        dict_nofilename = self.dictcopy()
        for item in infile_list:
            dict_withhash[item] = _hash_bunch_dict(dict_withhash, item)
            dict_nofilename[item] = [val[1] for val in dict_withhash[item]]
        # Sort the items of the dictionary, before hashing the string
        # representation so we get a predictable order of the
        # dictionary.
        sorted_dict = str(sorted(dict_nofilename.items()))
        return dict_withhash, md5(sorted_dict.encode()).hexdigest()

    def _repr_pretty_(self, p, cycle):
        """Support for the pretty module from ipython.externals"""
        if cycle:
            p.text("Bunch(...)")
        else:
            p.begin_group(6, "Bunch(")
            first = True
            for k, v in sorted(self.items()):
                if not first:
                    p.text(",")
                    p.breakable()
                p.text(k + "=")
                p.pretty(v)
                first = False
            p.end_group(6, ")")


def _hash_bunch_dict(adict, key):
    """Inject file hashes into adict[key]"""
    stuff = adict[key]
    if not is_container(stuff):
        stuff = [stuff]
    return [(afile, hash_infile(afile)) for afile in stuff]


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

    def __init__(self, interface, runtime, inputs=None, outputs=None, provenance=None):
        self._version = 2.0
        self.interface = interface
        self.runtime = runtime
        self.inputs = inputs
        self.outputs = outputs
        self.provenance = provenance

    @property
    def version(self):
        return self._version


def format_help(cls):
    """
    Prints help text of a Nipype interface

    >>> from nipype.interfaces.afni import GCOR
    >>> GCOR.help()  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    Wraps the executable command ``@compute_gcor``.
    <BLANKLINE>
    Computes the average correlation between every voxel
    and ever other voxel, over any give mask.
    <BLANKLINE>
    <BLANKLINE>
    For complete details, ...

    """
    from ...utils.misc import trim

    docstring = []
    cmd = getattr(cls, "_cmd", None)
    if cmd:
        docstring += ["Wraps the executable command ``%s``." % cmd, ""]

    if cls.__doc__:
        docstring += trim(cls.__doc__).split("\n") + [""]

    allhelp = "\n".join(
        docstring
        + _inputs_help(cls)
        + [""]
        + _outputs_help(cls)
        + [""]
        + _refs_help(cls)
    )
    return allhelp.expandtabs(8)


def _inputs_help(cls):
    r"""
    Prints description for input parameters

    >>> from nipype.interfaces.afni import GCOR
    >>> _inputs_help(GCOR)  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    ['Inputs::', '', '\t[Mandatory]', '\tin_file: (a pathlike object or string...

    """
    helpstr = ["Inputs::"]
    mandatory_keys = []
    optional_items = []

    if cls.input_spec:
        inputs = cls.input_spec()
        mandatory_items = list(inputs.traits(mandatory=True).items())
        if mandatory_items:
            helpstr += ["", "\t[Mandatory]"]
            for name, spec in mandatory_items:
                helpstr += get_trait_desc(inputs, name, spec)

        mandatory_keys = {item[0] for item in mandatory_items}
        optional_items = [
            "\n".join(get_trait_desc(inputs, name, val))
            for name, val in inputs.traits(transient=None).items()
            if name not in mandatory_keys
        ]
        if optional_items:
            helpstr += ["", "\t[Optional]"] + optional_items

    if not mandatory_keys and not optional_items:
        helpstr += ["", "\tNone"]
    return helpstr


def _outputs_help(cls):
    r"""
    Prints description for output parameters

    >>> from nipype.interfaces.afni import GCOR
    >>> _outputs_help(GCOR)  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    ['Outputs::', '', '\tout: (a float)\n\t\tglobal correlation value']

    """
    helpstr = ["Outputs::", "", "\tNone"]
    if cls.output_spec:
        outputs = cls.output_spec()
        outhelpstr = [
            "\n".join(get_trait_desc(outputs, name, spec))
            for name, spec in outputs.traits(transient=None).items()
        ]
        if outhelpstr:
            helpstr = helpstr[:-1] + outhelpstr
    return helpstr


def _refs_help(cls):
    """Prints interface references."""
    references = getattr(cls, "_references", None)
    if not references:
        return []

    helpstr = ["References:", "-----------"]
    for r in references:
        helpstr += ["{}".format(r["entry"])]

    return helpstr


def get_trait_desc(inputs, name, spec):
    """Parses a HasTraits object into a nipype documentation string"""
    desc = spec.desc
    xor = spec.xor
    requires = spec.requires
    argstr = spec.argstr

    manhelpstr = ["\t%s" % name]

    type_info = spec.full_info(inputs, name, None)

    default = ""
    if spec.usedefault:
        default = ", nipype default value: %s" % str(spec.default_value()[1])
    line = "(%s%s)" % (type_info, default)

    manhelpstr = wrap(
        line,
        HELP_LINEWIDTH,
        initial_indent=manhelpstr[0] + ": ",
        subsequent_indent="\t\t  ",
    )

    if desc:
        for line in desc.split("\n"):
            line = re.sub(r"\s+", " ", line)
            manhelpstr += wrap(
                line, HELP_LINEWIDTH, initial_indent="\t\t", subsequent_indent="\t\t"
            )

    if argstr:
        pos = spec.position
        if pos is not None:
            manhelpstr += wrap(
                "argument: ``%s``, position: %s" % (argstr, pos),
                HELP_LINEWIDTH,
                initial_indent="\t\t",
                subsequent_indent="\t\t",
            )
        else:
            manhelpstr += wrap(
                "argument: ``%s``" % argstr,
                HELP_LINEWIDTH,
                initial_indent="\t\t",
                subsequent_indent="\t\t",
            )

    if xor:
        line = "%s" % ", ".join(xor)
        manhelpstr += wrap(
            line,
            HELP_LINEWIDTH,
            initial_indent="\t\tmutually_exclusive: ",
            subsequent_indent="\t\t  ",
        )

    if requires:
        others = [field for field in requires if field != name]
        line = "%s" % ", ".join(others)
        manhelpstr += wrap(
            line,
            HELP_LINEWIDTH,
            initial_indent="\t\trequires: ",
            subsequent_indent="\t\t  ",
        )
    return manhelpstr
