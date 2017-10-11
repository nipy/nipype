# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Package contains interfaces for using existing functionality in other packages

Exaples  FSL, matlab/SPM , afni

Requires Packages to be installed
"""
from __future__ import print_function, division, unicode_literals, absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import range, object, open, str, bytes

from configparser import NoOptionError
from copy import deepcopy
import datetime
from datetime import datetime as dt
import errno
import locale
import os
import re
import platform
from string import Template
import select
import subprocess as sp
import sys
import time
from textwrap import wrap
from warnings import warn
import simplejson as json
from dateutil.parser import parse as parseutc
from packaging.version import Version
import collections

from .. import config, logging, LooseVersion, __version__
from ..utils.provenance import write_provenance
from ..utils.misc import is_container, trim, str2bool
from ..utils.filemanip import (md5, hash_infile, FileNotFoundError, hash_timestamp,
                               split_filename, to_str)
from .traits_extension import (
    traits, Undefined, TraitDictObject, TraitListObject, TraitError, isdefined,
    File, Directory, DictStrStr, has_metadata, ImageFile)
from ..external.due import due

nipype_version = Version(__version__)
iflogger = logging.getLogger('interface')

FLOAT_FORMAT = '{:.10f}'.format
PY35 = sys.version_info >= (3, 5)
PY3 = sys.version_info[0] > 2
VALID_TERMINAL_OUTPUT = ['stream', 'allatonce', 'file', 'file_split',
                         'file_stdout', 'file_stderr', 'none']
__docformat__ = 'restructuredtext'


class Str(traits.Unicode):
    """Replacement for the default traits.Str based in bytes"""

traits.Str = Str


class NipypeInterfaceError(Exception):
    """Custom error for interfaces"""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return '{}'.format(self.value)


def _exists_in_path(cmd, environ):
    """
    Based on a code snippet from
     http://orip.org/2009/08/python-checking-if-executable-exists-in.html
    """

    if 'PATH' in environ:
        input_environ = environ.get("PATH")
    else:
        input_environ = os.environ.get("PATH", "")
    extensions = os.environ.get("PATHEXT", "").split(os.pathsep)
    for directory in input_environ.split(os.pathsep):
        base = os.path.join(directory, cmd)
        options = [base] + [(base + ext) for ext in extensions]
        for filename in options:
            if os.path.exists(filename):
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
    full_fname = os.path.join(os.path.dirname(__file__),
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
    >>> inputs # doctest: +ALLOW_UNICODE
    Bunch(fwhm=6.0, infile='subj.nii', register_to_mean=True)
    >>> inputs.register_to_mean = False
    >>> inputs # doctest: +ALLOW_UNICODE
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
        warn('iteritems is deprecated, use items instead')
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
        for k, v in sorted(self.items()):
            if not first:
                outstr.append(', ')
            if isinstance(v, dict):
                pairs = []
                for key, value in sorted(v.items()):
                    pairs.append("'%s': %s" % (key, value))
                v = '{' + ', '.join(pairs) + '}'
                outstr.append('%s=%s' % (k, v))
            else:
                outstr.append('%s=%r' % (k, v))
            first = False
        outstr.append(')')
        return ''.join(outstr)

    def _hash_infile(self, adict, key):
        # Inject file hashes into adict[key]
        stuff = adict[key]
        if not is_container(stuff):
            stuff = [stuff]
        file_list = []
        for afile in stuff:
            if os.path.isfile(afile):
                md5obj = md5()
                with open(afile, 'rb') as fp:
                    while True:
                        data = fp.read(8192)
                        if not data:
                            break
                        md5obj.update(data)
                md5hex = md5obj.hexdigest()
            else:
                md5hex = None
            file_list.append((afile, md5hex))
        return file_list

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
                if isinstance(item, str) and os.path.isfile(item):
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
        sorted_dict = to_str(sorted(dict_nofilename.items()))
        return dict_withhash, md5(sorted_dict.encode()).hexdigest()

    def __pretty__(self, p, cycle):
        """Support for the pretty module

        pretty is included in ipython.externals for ipython > 0.10"""
        if cycle:
            p.text('Bunch(...)')
        else:
            p.begin_group(6, 'Bunch(')
            first = True
            for k, v in sorted(self.items()):
                if not first:
                    p.text(',')
                    p.breakable()
                p.text(k + '=')
                p.pretty(v)
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


class BaseTraitedSpec(traits.HasTraits):
    """Provide a few methods necessary to support nipype interface api

    The inputs attribute of interfaces call certain methods that are not
    available in traits.HasTraits. These are provided here.

    new metadata:

    * usedefault : set this to True if the default value of the trait should be
      used. Unless this is set, the attributes are set to traits.Undefined

    new attribute:

    * get_hashval : returns a tuple containing the state of the trait as a dict
      and hashvalue corresponding to dict.

    XXX Reconsider this in the long run, but it seems like the best
    solution to move forward on the refactoring.
    """
    package_version = nipype_version

    def __init__(self, **kwargs):
        """ Initialize handlers and inputs"""
        # NOTE: In python 2.6, object.__init__ no longer accepts input
        # arguments.  HasTraits does not define an __init__ and
        # therefore these args were being ignored.
        # super(TraitedSpec, self).__init__(*args, **kwargs)
        super(BaseTraitedSpec, self).__init__(**kwargs)
        traits.push_exception_handler(reraise_exceptions=True)
        undefined_traits = {}
        for trait in self.copyable_trait_names():
            if not self.traits()[trait].usedefault:
                undefined_traits[trait] = Undefined
        self.trait_set(trait_change_notify=False, **undefined_traits)
        self._generate_handlers()
        self.trait_set(**kwargs)

    def items(self):
        """ Name, trait generator for user modifiable traits
        """
        for name in sorted(self.copyable_trait_names()):
            yield name, self.traits()[name]

    def __repr__(self):
        """ Return a well-formatted representation of the traits """
        outstr = []
        for name, value in sorted(self.trait_get().items()):
            outstr.append('%s = %s' % (name, value))
        return '\n{}\n'.format('\n'.join(outstr))

    def _generate_handlers(self):
        """Find all traits with the 'xor' metadata and attach an event
        handler to them.
        """
        has_xor = dict(xor=lambda t: t is not None)
        xors = self.trait_names(**has_xor)
        for elem in xors:
            self.on_trait_change(self._xor_warn, elem)
        has_deprecation = dict(deprecated=lambda t: t is not None)
        deprecated = self.trait_names(**has_deprecation)
        for elem in deprecated:
            self.on_trait_change(self._deprecated_warn, elem)

    def _xor_warn(self, obj, name, old, new):
        """ Generates warnings for xor traits
        """
        if isdefined(new):
            trait_spec = self.traits()[name]
            # for each xor, set to default_value
            for trait_name in trait_spec.xor:
                if trait_name == name:
                    # skip ourself
                    continue
                if isdefined(getattr(self, trait_name)):
                    self.trait_set(trait_change_notify=False,
                                   **{'%s' % name: Undefined})
                    msg = ('Input "%s" is mutually exclusive with input "%s", '
                           'which is already set') % (name, trait_name)
                    raise IOError(msg)

    def _requires_warn(self, obj, name, old, new):
        """Part of the xor behavior
        """
        if isdefined(new):
            trait_spec = self.traits()[name]
            msg = None
            for trait_name in trait_spec.requires:
                if not isdefined(getattr(self, trait_name)):
                    if not msg:
                        msg = 'Input %s requires inputs: %s' \
                            % (name, ', '.join(trait_spec.requires))
            if msg:  # only one requires warning at a time.
                warn(msg)

    def _deprecated_warn(self, obj, name, old, new):
        """Checks if a user assigns a value to a deprecated trait
        """
        if isdefined(new):
            trait_spec = self.traits()[name]
            msg1 = ('Input %s in interface %s is deprecated.' %
                    (name,
                     self.__class__.__name__.split('InputSpec')[0]))
            msg2 = ('Will be removed or raise an error as of release %s'
                    % trait_spec.deprecated)
            if trait_spec.new_name:
                if trait_spec.new_name not in self.copyable_trait_names():
                    raise TraitError(msg1 + ' Replacement trait %s not found' %
                                     trait_spec.new_name)
                msg3 = 'It has been replaced by %s.' % trait_spec.new_name
            else:
                msg3 = ''
            msg = ' '.join((msg1, msg2, msg3))
            if Version(str(trait_spec.deprecated)) < self.package_version:
                raise TraitError(msg)
            else:
                if trait_spec.new_name:
                    msg += 'Unsetting old value %s; setting new value %s.' % (
                        name, trait_spec.new_name)
                warn(msg)
                if trait_spec.new_name:
                    self.trait_set(trait_change_notify=False,
                                   **{'%s' % name: Undefined,
                                      '%s' % trait_spec.new_name: new})

    def _hash_infile(self, adict, key):
        """ Inject file hashes into adict[key]"""
        stuff = adict[key]
        if not is_container(stuff):
            stuff = [stuff]
        file_list = []
        for afile in stuff:
            if is_container(afile):
                hashlist = self._hash_infile({'infiles': afile}, 'infiles')
                hash = [val[1] for val in hashlist]
            else:
                if config.get('execution',
                              'hash_method').lower() == 'timestamp':
                    hash = hash_timestamp(afile)
                elif config.get('execution',
                                'hash_method').lower() == 'content':
                    hash = hash_infile(afile)
                else:
                    raise Exception("Unknown hash method: %s" %
                                    config.get('execution', 'hash_method'))
            file_list.append((afile, hash))
        return file_list

    def get(self, **kwargs):
        """ Returns traited class as a dict

        Augments the trait get function to return a dictionary without
        notification handles
        """
        out = super(BaseTraitedSpec, self).get(**kwargs)
        out = self._clean_container(out, Undefined)
        return out

    def get_traitsfree(self, **kwargs):
        """ Returns traited class as a dict

        Augments the trait get function to return a dictionary without
        any traits. The dictionary does not contain any attributes that
        were Undefined
        """
        out = super(BaseTraitedSpec, self).get(**kwargs)
        out = self._clean_container(out, skipundefined=True)
        return out

    def _clean_container(self, object, undefinedval=None, skipundefined=False):
        """Convert a traited obejct into a pure python representation.
        """
        if isinstance(object, TraitDictObject) or isinstance(object, dict):
            out = {}
            for key, val in list(object.items()):
                if isdefined(val):
                    out[key] = self._clean_container(val, undefinedval)
                else:
                    if not skipundefined:
                        out[key] = undefinedval
        elif (isinstance(object, TraitListObject) or
                isinstance(object, list) or isinstance(object, tuple)):
            out = []
            for val in object:
                if isdefined(val):
                    out.append(self._clean_container(val, undefinedval))
                else:
                    if not skipundefined:
                        out.append(undefinedval)
                    else:
                        out.append(None)
            if isinstance(object, tuple):
                out = tuple(out)
        else:
            if isdefined(object):
                out = object
            else:
                if not skipundefined:
                    out = undefinedval
        return out

    def has_metadata(self, name, metadata, value=None, recursive=True):
        """
        Return has_metadata for the requested trait name in this
        interface
        """
        return has_metadata(self.trait(name).trait_type, metadata, value,
                            recursive)

    def get_hashval(self, hash_method=None):
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
            The md5 hash value of the traited spec

        """

        dict_withhash = []
        dict_nofilename = []
        for name, val in sorted(self.get().items()):
            if not isdefined(val) or self.has_metadata(name, "nohash", True):
                # skip undefined traits and traits with nohash=True
                continue

            hash_files = (not self.has_metadata(name, "hash_files", False) and not
                          self.has_metadata(name, "name_source"))
            dict_nofilename.append((name,
                                    self._get_sorteddict(val, hash_method=hash_method,
                                                         hash_files=hash_files)))
            dict_withhash.append((name,
                                  self._get_sorteddict(val, True, hash_method=hash_method,
                                                       hash_files=hash_files)))
        return dict_withhash, md5(to_str(dict_nofilename).encode()).hexdigest()

    def _get_sorteddict(self, objekt, dictwithhash=False, hash_method=None,
                        hash_files=True):
        if isinstance(objekt, dict):
            out = []
            for key, val in sorted(objekt.items()):
                if isdefined(val):
                    out.append((key,
                                self._get_sorteddict(val, dictwithhash,
                                                     hash_method=hash_method,
                                                     hash_files=hash_files)))
        elif isinstance(objekt, (list, tuple)):
            out = []
            for val in objekt:
                if isdefined(val):
                    out.append(self._get_sorteddict(val, dictwithhash,
                                                    hash_method=hash_method,
                                                    hash_files=hash_files))
            if isinstance(objekt, tuple):
                out = tuple(out)
        else:
            if isdefined(objekt):
                if (hash_files and isinstance(objekt, (str, bytes)) and
                        os.path.isfile(objekt)):
                    if hash_method is None:
                        hash_method = config.get('execution', 'hash_method')

                    if hash_method.lower() == 'timestamp':
                        hash = hash_timestamp(objekt)
                    elif hash_method.lower() == 'content':
                        hash = hash_infile(objekt)
                    else:
                        raise Exception("Unknown hash method: %s" % hash_method)
                    if dictwithhash:
                        out = (objekt, hash)
                    else:
                        out = hash
                elif isinstance(objekt, float):
                    out = FLOAT_FORMAT(objekt)
                else:
                    out = objekt
        return out


class DynamicTraitedSpec(BaseTraitedSpec):
    """ A subclass to handle dynamic traits

    This class is a workaround for add_traits and clone_traits not
    functioning well together.
    """

    def __deepcopy__(self, memo):
        """ bug in deepcopy for HasTraits results in weird cloning behavior for
        added traits
        """
        id_self = id(self)
        if id_self in memo:
            return memo[id_self]
        dup_dict = deepcopy(self.get(), memo)
        # access all keys
        for key in self.copyable_trait_names():
            if key in self.__dict__.keys():
                _ = getattr(self, key)
        # clone once
        dup = self.clone_traits(memo=memo)
        for key in self.copyable_trait_names():
            try:
                _ = getattr(dup, key)
            except:
                pass
        # clone twice
        dup = self.clone_traits(memo=memo)
        dup.trait_set(**dup_dict)
        return dup


class TraitedSpec(BaseTraitedSpec):
    """ Create a subclass with strict traits.

    This is used in 90% of the cases.
    """
    _ = traits.Disallow


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


class BaseInterfaceInputSpec(TraitedSpec):
    ignore_exception = traits.Bool(False, usedefault=True, nohash=True,
                                   desc='Print an error message instead of throwing an exception '
                                        'in case the interface fails to run')


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

    def __init__(self, from_file=None, resource_monitor=None, **inputs):
        if not self.input_spec:
            raise Exception('No input_spec in class: %s' %
                            self.__class__.__name__)

        self.inputs = self.input_spec(**inputs)

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

        allhelp = '\n'.join(docstring + cls._inputs_help() + [''] +
                            cls._outputs_help() + [''] +
                            cls._refs_help() + [''])
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
            default = ', nipype default value: %s' % str(spec.default_value()[1])
        line = "(%s%s)" % (type_info, default)

        manhelpstr = wrap(line, 70,
                          initial_indent=manhelpstr[0] + ': ',
                          subsequent_indent='\t\t ')

        if desc:
            for line in desc.split('\n'):
                line = re.sub("\s+", " ", line)
                manhelpstr += wrap(line, 70,
                                   initial_indent='\t\t',
                                   subsequent_indent='\t\t')

        if argstr:
            pos = spec.position
            if pos is not None:
                manhelpstr += wrap('flag: %s, position: %s' % (argstr, pos), 70,
                                   initial_indent='\t\t',
                                   subsequent_indent='\t\t')
            else:
                manhelpstr += wrap('flag: %s' % argstr, 70,
                                   initial_indent='\t\t',
                                   subsequent_indent='\t\t')

        if xor:
            line = '%s' % ', '.join(xor)
            manhelpstr += wrap(line, 70,
                               initial_indent='\t\tmutually_exclusive: ',
                               subsequent_indent='\t\t ')

        if requires:
            others = [field for field in requires if field != name]
            line = '%s' % ', '.join(others)
            manhelpstr += wrap(line, 70,
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
            outputs = cls.output_spec()  # pylint: disable=E1102
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
            outputs = self.output_spec()  # pylint: disable=E1102

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
            info.append(dict(key=name,
                             copy=spec.copyfile))
        return info

    def _check_requires(self, spec, name, value):
        """ check if required inputs are satisfied
        """
        if spec.requires:
            values = [not isdefined(getattr(self.inputs, field))
                      for field in spec.requires]
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
            values = [isdefined(getattr(self.inputs, field))
                      for field in spec.xor]
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
                       (self.__class__.__name__, name, self.__class__.__name__))
                raise ValueError(msg)
            if isdefined(value):
                self._check_requires(spec, name, value)
        for name, spec in list(self.inputs.traits(mandatory=None,
                                                  transient=None).items()):
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
                min_ver = LooseVersion(str(trait_object.traits()[name].min_ver))
                if min_ver > version:
                    unavailable_traits.append(name)
                    if not isdefined(getattr(trait_object, name)):
                        continue
                    if raise_exception:
                        raise Exception('Trait %s (%s) (version %s < required %s)' %
                                        (name, self.__class__.__name__,
                                         version, min_ver))
            check = dict(max_ver=lambda t: t is not None)
            names = trait_object.trait_names(**check)
            for name in names:
                max_ver = LooseVersion(str(trait_object.traits()[name].max_ver))
                if max_ver < version:
                    unavailable_traits.append(name)
                    if not isdefined(getattr(trait_object, name)):
                        continue
                    if raise_exception:
                        raise Exception('Trait %s (%s) (version %s > required %s)' %
                                        (name, self.__class__.__name__,
                                         version, max_ver))
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
        from ..utils.profiler import ResourceMonitor

        enable_rm = config.resource_monitor and self.resource_monitor
        force_raise = not getattr(self.inputs, 'ignore_exception', False)
        self.inputs.trait_set(**inputs)
        self._check_mandatory_inputs()
        self._check_version_requirements(self.inputs)
        interface = self.__class__
        self._duecredit_cite()

        # initialize provenance tracking
        store_provenance = str2bool(config.get(
            'execution', 'write_provenance', 'false'))
        env = deepcopy(dict(os.environ))
        if self._redirect_x:
            env['DISPLAY'] = config.get_display()

        runtime = Bunch(cwd=os.getcwd(),
                        returncode=None,
                        duration=None,
                        environ=env,
                        startTime=dt.isoformat(dt.utcnow()),
                        endTime=None,
                        platform=platform.platform(),
                        hostname=platform.node(),
                        version=self.version)

        mon_sp = None
        if enable_rm:
            mon_freq = float(config.get('execution', 'resource_monitor_frequency', 1))
            proc_pid = os.getpid()
            iflogger.debug('Creating a ResourceMonitor on a %s interface, PID=%d.',
                           self.__class__.__name__, proc_pid)
            mon_sp = ResourceMonitor(proc_pid, freq=mon_freq)
            mon_sp.start()

        # Grab inputs now, as they should not change during execution
        inputs = self.inputs.get_traitsfree()
        outputs = None

        try:
            runtime = self._run_interface(runtime)
            outputs = self.aggregate_outputs(runtime)
        except Exception as e:
            import traceback
            # Retrieve the maximum info fast
            runtime.traceback = traceback.format_exc()
            # Gather up the exception arguments and append nipype info.
            exc_args = e.args if getattr(e, 'args') else tuple()
            exc_args += ('An exception of type %s occurred while running interface %s.' %
                         (type(e).__name__, self.__class__.__name__), )
            if config.get('logging', 'interface_level', 'info').lower() == 'debug':
                exc_args += ('Inputs: %s' % str(self.inputs),)

            runtime.traceback_args = ('\n'.join(['%s' % arg for arg in exc_args]),)

            if force_raise:
                raise
        finally:
            # This needs to be done always
            runtime.endTime = dt.isoformat(dt.utcnow())
            timediff = parseutc(runtime.endTime) - parseutc(runtime.startTime)
            runtime.duration = (timediff.days * 86400 + timediff.seconds +
                                timediff.microseconds / 1e6)
            results = InterfaceResult(interface, runtime, inputs=inputs, outputs=outputs,
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
                        'mem_gb': (vals[:, 1] / 1024).tolist(),
                        'cpus': vals[:, 2].tolist(),
                    }

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
                    if getattr(error, 'info', 'default').startswith('an existing'):
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


class SimpleInterface(BaseInterface):
    """ An interface pattern that allows outputs to be set in a dictionary
    called ``_results`` that is automatically interpreted by
    ``_list_outputs()`` to find the outputs.

    When implementing ``_run_interface``, set outputs with::

        self._results[out_name] = out_value

    This can be a way to upgrade a ``Function`` interface to do type checking.

    Examples
    --------
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
        self.default_encoding = locale.getdefaultlocale()[1]
        if self.default_encoding is None:
            self.default_encoding = 'UTF-8'

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
        buf = os.read(fd, 4096).decode(self.default_encoding)
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
        now = datetime.datetime.now().isoformat()
        rows = tmp.split('\n')
        self._rows += [(now, '%s %s:%s' % (self._name, now, r), r)
                       for r in rows]
        for idx in range(self._lastidx, len(self._rows)):
            iflogger.info(self._rows[idx][1])
        self._lastidx = len(self._rows)


def _canonicalize_env(env):
    """Windows requires that environment be dicts with bytes as keys and values
    This function converts any unicode entries for Windows only, returning the
    dictionary untouched in other environments.

    Parameters
    ----------
    env : dict
        environment dictionary with unicode or bytes keys and values

    Returns
    -------
    env : dict
        Windows: environment dictionary with bytes keys and values
        Other: untouched input ``env``
    """
    if os.name != 'nt':
        return env

    out_env = {}
    for key, val in env:
        if not isinstance(key, bytes):
            key = key.encode('utf-8')
        if not isinstance(val, bytes):
            val = key.encode('utf-8')
        out_env[key] = val
    return out_env


def run_command(runtime, output=None, timeout=0.01):
    """Run a command, read stdout and stderr, prefix with timestamp.

    The returned runtime contains a merged stdout+stderr log with timestamps
    """

    # Init variables
    cmdline = runtime.cmdline
    env = _canonicalize_env(runtime.environ)

    default_encoding = locale.getdefaultlocale()[1]
    if default_encoding is None:
        default_encoding = 'UTF-8'

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

    proc = sp.Popen(cmdline,
                    stdout=stdout,
                    stderr=stderr,
                    shell=True,
                    cwd=runtime.cwd,
                    env=env)
    result = {
        'stdout': [],
        'stderr': [],
        'merged': [],
    }

    if output == 'stream':
        streams = [Stream('stdout', proc.stdout), Stream('stderr', proc.stderr)]

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

    if output == 'allatonce':
        stdout, stderr = proc.communicate()
        result['stdout'] = stdout.decode(default_encoding).split('\n')
        result['stderr'] = stderr.decode(default_encoding).split('\n')

    elif output.startswith('file'):
        proc.wait()
        if outfile is not None:
            stdout.flush()
            result['stdout'] = [line.decode(default_encoding).strip()
                                for line in open(outfile, 'rb').readlines()]
        if errfile is not None:
            stderr.flush()
            result['stderr'] = [line.decode(default_encoding).strip()
                                for line in open(errfile, 'rb').readlines()]

        if output == 'file':
            result['merged'] = result['stdout']
            result['stdout'] = []
    else:
        proc.communicate()  # Discard stdout and stderr

    runtime.stderr = '\n'.join(result['stderr'])
    runtime.stdout = '\n'.join(result['stdout'])
    runtime.merged = '\n'.join(result['merged'])
    runtime.returncode = proc.returncode
    return runtime


def get_dependencies(name, environ):
    """Return library dependencies of a dynamically linked executable

    Uses otool on darwin, ldd on linux. Currently doesn't support windows.

    """
    if sys.platform == 'darwin':
        proc = sp.Popen('otool -L `which %s`' % name,
                        stdout=sp.PIPE,
                        stderr=sp.PIPE,
                        shell=True,
                        env=environ)
    elif 'linux' in sys.platform:
        proc = sp.Popen('ldd `which %s`' % name,
                        stdout=sp.PIPE,
                        stderr=sp.PIPE,
                        shell=True,
                        env=environ)
    else:
        return 'Platform %s not supported' % sys.platform
    o, e = proc.communicate()
    return o.rstrip()


class CommandLineInputSpec(BaseInterfaceInputSpec):
    args = Str(argstr='%s', desc='Additional parameters to the command')
    environ = DictStrStr(desc='Environment variables', usedefault=True,
                         nohash=True)
    # This input does not have a "usedefault=True" so the set_default_terminal_output()
    # method would work
    terminal_output = traits.Enum('stream', 'allatonce', 'file', 'none',
                                  deprecated='1.0.0',
                                  desc=('Control terminal output: `stream` - '
                                        'displays to terminal immediately (default), '
                                        '`allatonce` - waits till command is '
                                        'finished to display output, `file` - '
                                        'writes output to file, `none` - output'
                                        ' is ignored'),
                                  nohash=True)


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
    >>> cli.cmdline # doctest: +ALLOW_UNICODE
    'ls -al'

    # Use get_traitsfree() to check all inputs set
    >>> pprint.pprint(cli.inputs.get_traitsfree())  # doctest: +NORMALIZE_WHITESPACE +ALLOW_UNICODE
    {'args': '-al',
     'environ': {'DISPLAY': ':1'},
     'ignore_exception': False}

    >>> cli.inputs.get_hashval()[0][0] # doctest: +ALLOW_UNICODE
    ('args', '-al')
    >>> cli.inputs.get_hashval()[1] # doctest: +ALLOW_UNICODE
    '11c37f97649cd61627f4afe5136af8c0'

    """
    input_spec = CommandLineInputSpec
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
            raise AttributeError('Invalid terminal output_type: %s' %
                                 output_type)

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

        if self._cmd is None:
            raise Exception("Missing command")

        if terminal_output is not None:
            self.terminal_output = terminal_output

        # Attach terminal_output callback for backwards compatibility
        self.inputs.on_trait_change(self._terminal_output_update,
                                    'terminal_output')

    @property
    def cmd(self):
        """sets base command, immutable"""
        return self._cmd

    @property
    def cmdline(self):
        """ `command` plus any arguments (args)
        validates arguments and generates command line"""
        self._check_mandatory_inputs()
        allargs = [self.cmd] + self._parse_inputs()
        return ' '.join(allargs)

    @property
    def terminal_output(self):
        return self._terminal_output

    @terminal_output.setter
    def terminal_output(self, value):
        if value not in VALID_TERMINAL_OUTPUT:
            raise RuntimeError(
                'Setting invalid value "%s" for terminal_output. Valid values are '
                '%s.' % (value, ', '.join(['"%s"' % v for v in VALID_TERMINAL_OUTPUT])))
        self._terminal_output = value

    def _terminal_output_update(self):
        self.terminal_output = self.terminal_output

    def raise_exception(self, runtime):
        raise RuntimeError(
            ('Command:\n{cmdline}\nStandard output:\n{stdout}\n'
             'Standard error:\n{stderr}\nReturn code: {returncode}').format(
                 **runtime.dictcopy()))

    def _get_environ(self):
        return getattr(self.inputs, 'environ', {})

    def version_from_command(self, flag='-v'):
        cmdname = self.cmd.split()[0]
        env = dict(os.environ)
        if _exists_in_path(cmdname, env):
            out_environ = self._get_environ()
            env.update(out_environ)
            proc = sp.Popen(' '.join((cmdname, flag)),
                            shell=True,
                            env=env,
                            stdout=sp.PIPE,
                            stderr=sp.PIPE,
                            )
            o, e = proc.communicate()
            return o

    def _run_interface(self, runtime, correct_return_codes=(0,)):
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
        executable_name = self.cmd.split()[0]
        exist_val, cmd_path = _exists_in_path(executable_name,
                                              runtime.environ)
        if not exist_val:
            raise IOError("command '%s' could not be found on host %s" %
                          (self.cmd.split()[0], runtime.hostname))

        runtime.command_path = cmd_path
        runtime.dependencies = get_dependencies(executable_name, runtime.environ)
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
            if isdefined(retval) and "%s" in retval:
                name_template = retval
            else:
                name_template = trait_spec.name_template
            if not name_template:
                name_template = "%s_generated"

            ns = trait_spec.name_source
            while isinstance(ns, (list, tuple)):
                if len(ns) > 1:
                    iflogger.warning('Only one name_source per trait is allowed')
                ns = ns[0]

            if not isinstance(ns, (str, bytes)):
                raise ValueError(
                    'name_source of \'{}\' trait should be an input trait '
                    'name, but a type {} object was found'.format(name, type(ns)))

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
                    raise NipypeInterfaceError('Mutually pointing name_sources')

                chain.append(name)
                base = self._filename_from_source(ns, chain)
                if isdefined(base):
                    _, _, source_ext = split_filename(base)

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
            outputs = self.output_spec().get()  # pylint: disable=E1102
            for name, trait_spec in list(traits.items()):
                out_name = name
                if trait_spec.output_name is not None:
                    out_name = trait_spec.output_name
                outputs[out_name] = \
                    os.path.abspath(self._filename_from_source(name))
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


class StdOutCommandLineInputSpec(CommandLineInputSpec):
    out_file = File(argstr="> %s", position=-1, genfile=True)


class StdOutCommandLine(CommandLine):
    input_spec = StdOutCommandLineInputSpec

    def _gen_filename(self, name):
        return self._gen_outfilename() if name == 'out_file' else None

    def _gen_outfilename(self):
        raise NotImplementedError


class MpiCommandLineInputSpec(CommandLineInputSpec):
    use_mpi = traits.Bool(False,
                          desc="Whether or not to run the command with mpiexec",
                          usedefault=True)
    n_procs = traits.Int(desc="Num processors to specify to mpiexec. Do not "
                         "specify if this is managed externally (e.g. through "
                         "SGE)")


class MpiCommandLine(CommandLine):
    """Implements functionality to interact with command line programs
    that can be run with MPI (i.e. using 'mpiexec').

    Examples
    --------
    >>> from nipype.interfaces.base import MpiCommandLine
    >>> mpi_cli = MpiCommandLine(command='my_mpi_prog')
    >>> mpi_cli.inputs.args = '-v'
    >>> mpi_cli.cmdline # doctest: +ALLOW_UNICODE
    'my_mpi_prog -v'

    >>> mpi_cli.inputs.use_mpi = True
    >>> mpi_cli.inputs.n_procs = 8
    >>> mpi_cli.cmdline # doctest: +ALLOW_UNICODE
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
        outputs = self.output_spec().get()  # pylint: disable=E1102
        return self._outputs_from_inputs(outputs)

    def _outputs_from_inputs(self, outputs):
        for name in list(outputs.keys()):
            corresponding_input = getattr(self.inputs, name)
            if isdefined(corresponding_input):
                if (isinstance(corresponding_input, bool) and
                        corresponding_input):
                    outputs[name] = \
                        os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(corresponding_input, list):
                        outputs[name] = [os.path.abspath(inp)
                                         for inp in corresponding_input]
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


class MultiPath(traits.List):
    """ Abstract class - shared functionality of input and output MultiPath
    """

    def validate(self, object, name, value):

        # want to treat range and other sequences (except str) as list
        if not isinstance(value, (str, bytes)) and isinstance(value, collections.Sequence):
            value = list(value)

        if not isdefined(value) or \
                (isinstance(value, list) and len(value) == 0):
            return Undefined

        newvalue = value

        if not isinstance(value, list) \
            or (self.inner_traits() and
                isinstance(self.inner_traits()[0].trait_type,
                           traits.List) and not
                isinstance(self.inner_traits()[0].trait_type,
                           InputMultiPath) and
                isinstance(value, list) and
                value and not
                isinstance(value[0], list)):
            newvalue = [value]
        value = super(MultiPath, self).validate(object, name, newvalue)

        if value:
            return value

        self.error(object, name, value)


class OutputMultiPath(MultiPath):
    """ Implements a user friendly traits that accepts one or more
    paths to files or directories. This is the output version which
    return a single string whenever possible (when it was set to a
    single value or a list of length 1). Default value of this trait
    is _Undefined. It does not accept empty lists.

    XXX This should only be used as a final resort. We should stick to
    established Traits to the extent possible.

    XXX This needs to be vetted by somebody who understands traits

    >>> from nipype.interfaces.base import OutputMultiPath
    >>> class A(TraitedSpec):
    ...     foo = OutputMultiPath(File(exists=False))
    >>> a = A()
    >>> a.foo
    <undefined>

    >>> a.foo = '/software/temp/foo.txt'
    >>> a.foo # doctest: +ALLOW_UNICODE
    '/software/temp/foo.txt'

    >>> a.foo = ['/software/temp/foo.txt']
    >>> a.foo # doctest: +ALLOW_UNICODE
    '/software/temp/foo.txt'

    >>> a.foo = ['/software/temp/foo.txt', '/software/temp/goo.txt']
    >>> a.foo # doctest: +ALLOW_UNICODE
    ['/software/temp/foo.txt', '/software/temp/goo.txt']

    """

    def get(self, object, name):
        value = self.get_value(object, name)
        if len(value) == 0:
            return Undefined
        elif len(value) == 1:
            return value[0]
        else:
            return value

    def set(self, object, name, value):
        self.set_value(object, name, value)


class InputMultiPath(MultiPath):
    """ Implements a user friendly traits that accepts one or more
    paths to files or directories. This is the input version which
    always returns a list. Default value of this trait
    is _Undefined. It does not accept empty lists.

    XXX This should only be used as a final resort. We should stick to
    established Traits to the extent possible.

    XXX This needs to be vetted by somebody who understands traits

    >>> from nipype.interfaces.base import InputMultiPath
    >>> class A(TraitedSpec):
    ...     foo = InputMultiPath(File(exists=False))
    >>> a = A()
    >>> a.foo
    <undefined>

    >>> a.foo = '/software/temp/foo.txt'
    >>> a.foo # doctest: +ALLOW_UNICODE
    ['/software/temp/foo.txt']

    >>> a.foo = ['/software/temp/foo.txt']
    >>> a.foo # doctest: +ALLOW_UNICODE
    ['/software/temp/foo.txt']

    >>> a.foo = ['/software/temp/foo.txt', '/software/temp/goo.txt']
    >>> a.foo # doctest: +ALLOW_UNICODE
    ['/software/temp/foo.txt', '/software/temp/goo.txt']

    """
    pass
