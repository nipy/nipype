# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Definition of inputs/outputs of interfaces.
"""

from __future__ import print_function
from __future__ import division

from copy import deepcopy
import os

from future import standard_library
standard_library.install_aliases()
from builtins import range
from builtins import object

from .traits_extension import (traits, Undefined, TraitDictObject, TraitListObject, TraitError,
                               isdefined, File, has_metadata)
from ..utils.filemanip import md5, hash_infile, hash_timestamp
from ..utils.misc import is_container
from .. import config, logging, LooseVersion
from .. import __version__
from ..external.six import string_types

NIPYPE_VERSION = LooseVersion(__version__)
IFLOGGER = logging.getLogger('interface')
__docformat__ = 'restructuredtext'


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
                if os.path.isfile(item):
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
            if os.path.isfile(fname):
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
        self.set(**kwargs)

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
        return '\n' + '\n'.join(outstr) + '\n'

    def _generate_handlers(self):
        """Find all traits with the 'xor' metadata and attach an event
        handler to them.
        """
        has_xor = dict(xor=lambda t: t is not None)
        xors = self.trait_names(**has_xor)
        for elem in xors:
            self.on_trait_change(self._xor_warn, elem)
        has_requires = dict(requires=lambda t: t is not None)
        requires = self.trait_names(**has_requires)
        for elem in requires:
            self.on_trait_change(self._requires_warn, elem)
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
                IFLOGGER.warn(msg)

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
            if LooseVersion(str(trait_spec.deprecated)) < NIPYPE_VERSION:
                raise TraitError(msg)
            else:
                if trait_spec.new_name:
                    msg += 'Unsetting old value %s; setting new value %s.' % (
                        name, trait_spec.new_name)
                IFLOGGER.warn(msg)
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

    def _clean_container(self, obj, undefinedval=None, skipundefined=False):
        """Convert a traited obejct into a pure python representation.
        """
        if isinstance(obj, TraitDictObject) or isinstance(obj, dict):
            out = {}
            for key, val in list(obj.items()):
                if isdefined(val):
                    out[key] = self._clean_container(val, undefinedval)
                else:
                    if not skipundefined:
                        out[key] = undefinedval
        elif (isinstance(obj, TraitListObject) or
                isinstance(obj, list) or isinstance(obj, tuple)):
            out = []
            for val in obj:
                if isdefined(val):
                    out.append(self._clean_container(val, undefinedval))
                else:
                    if not skipundefined:
                        out.append(undefinedval)
                    else:
                        out.append(None)
            if isinstance(obj, tuple):
                out = tuple(out)
        else:
            if isdefined(obj):
                out = obj
            else:
                if not skipundefined:
                    out = undefinedval
        return out

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
            if isdefined(val):
                trait = self.trait(name)
                if has_metadata(trait.trait_type, "nohash", True):
                    continue
                hash_files = (not has_metadata(trait.trait_type, "hash_files",
                                               False) and not
                              has_metadata(trait.trait_type, "name_source"))
                dict_nofilename.append((name,
                                        self._get_sorteddict(val, hash_method=hash_method,
                                                             hash_files=hash_files)))
                dict_withhash.append((name,
                                      self._get_sorteddict(val, True, hash_method=hash_method,
                                                           hash_files=hash_files)))
        return dict_withhash, md5(str(dict_nofilename).encode()).hexdigest()

    def _get_sorteddict(self, obj, dictwithhash=False, hash_method=None,
                        hash_files=True):
        if isinstance(obj, dict):
            out = []
            for key, val in sorted(obj.items()):
                if isdefined(val):
                    out.append((key,
                                self._get_sorteddict(val, dictwithhash,
                                                     hash_method=hash_method,
                                                     hash_files=hash_files)))
        elif isinstance(obj, (list, tuple)):
            out = []
            for val in obj:
                if isdefined(val):
                    out.append(self._get_sorteddict(val, dictwithhash,
                                                    hash_method=hash_method,
                                                    hash_files=hash_files))
            if isinstance(obj, tuple):
                out = tuple(out)
        else:
            if isdefined(obj):
                if (hash_files and isinstance(obj, string_types) and
                        os.path.isfile(obj)):
                    if hash_method is None:
                        hash_method = config.get('execution', 'hash_method')

                    if hash_method.lower() == 'timestamp':
                        hash = hash_timestamp(obj)
                    elif hash_method.lower() == 'content':
                        hash = hash_infile(obj)
                    else:
                        raise Exception("Unknown hash method: %s" % hash_method)
                    if dictwithhash:
                        out = (obj, hash)
                    else:
                        out = hash
                elif isinstance(obj, float):
                    out = '%.10f' % obj
                else:
                    out = obj
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
        dup.set(**dup_dict)
        return dup


class TraitedSpec(BaseTraitedSpec):
    """ Create a subclass with strict traits.

    This is used in 90% of the cases.
    """
    _ = traits.Disallow


class BaseInterfaceInputSpec(TraitedSpec):
    ignore_exception = traits.Bool(False, usedefault=True, nohash=True,
                                   desc='Print an error message instead of throwing an exception'
                                        ' in case the interface fails to run')


class CommandLineInputSpec(BaseInterfaceInputSpec):
    args = traits.Str(argstr='%s', desc='Additional parameters to the command')
    environ = traits.DictStrStr(desc='Environment variables', usedefault=True,
                                nohash=True)
    # This input does not have a "usedefault=True" so the set_default_terminal_output()
    # method would work
    terminal_output = traits.Enum('stream', 'allatonce', 'file', 'none',
                                  desc=('Control terminal output: `stream` - '
                                        'displays to terminal immediately (default), '
                                        '`allatonce` - waits till command is '
                                        'finished to display output, `file` - '
                                        'writes output to file, `none` - output'
                                        ' is ignored'),
                                  nohash=True)

    def _format_arg(self, name, trait_spec, value):
        """A helper function for _parse_inputs

        Formats a trait containing argstr metadata
        """
        argstr = trait_spec.argstr
        IFLOGGER.debug('%s_%s' % (name, str(value)))
        if trait_spec.is_trait_type(traits.Bool) and "%" not in argstr:
            if value:
                # Boolean options have no format string. Just append options
                # if True.
                return argstr
            else:
                return None
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
            sep = trait_spec.sep
            if sep is None:
                sep = ' '
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
            if not isdefined(value):
                if spec.genfile:
                    value = self._gen_filename(name)
                else:
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
        first_args = [arg for pos, arg in sorted(initial_args.items())]
        last_args = [arg for pos, arg in sorted(final_args.items())]
        return first_args + all_args + last_args


class StdOutCommandLineInputSpec(CommandLineInputSpec):
    out_file = File(argstr="> %s", position=-1, genfile=True)


class MpiCommandLineInputSpec(CommandLineInputSpec):
    use_mpi = traits.Bool(False,
                          desc="Whether or not to run the command with mpiexec",
                          usedefault=True)
    n_procs = traits.Int(desc="Num processors to specify to mpiexec. Do not "
                         "specify if this is managed externally (e.g. through "
                         "SGE)")


class SEMLikeCommandLineInputSpec(CommandLineInputSpec):

    def _format_arg(self, name, spec, value):
        if name in list(self._outputs_filenames.keys()):
            if isinstance(value, bool):
                if value:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(SEMLikeCommandLineInputSpec, self)._format_arg(name, spec, value)


class MultiPath(traits.List):
    """ Abstract class - shared functionality of input and output MultiPath
    """

    def validate(self, obj, name, value):
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
        value = super(MultiPath, self).validate(obj, name, newvalue)

        if len(value) > 0:
            return value

        self.error(obj, name, value)


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
    >>> a.foo
    '/software/temp/foo.txt'

    >>> a.foo = ['/software/temp/foo.txt']
    >>> a.foo
    '/software/temp/foo.txt'

    >>> a.foo = ['/software/temp/foo.txt', '/software/temp/goo.txt']
    >>> a.foo
    ['/software/temp/foo.txt', '/software/temp/goo.txt']

    """

    def get(self, obj, name):
        value = self.get_value(obj, name)
        if len(value) == 0:
            return Undefined
        elif len(value) == 1:
            return value[0]
        else:
            return value

    def set(self, obj, name, value):
        self.set_value(obj, name, value)


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
    >>> a.foo
    ['/software/temp/foo.txt']

    >>> a.foo = ['/software/temp/foo.txt']
    >>> a.foo
    ['/software/temp/foo.txt']

    >>> a.foo = ['/software/temp/foo.txt', '/software/temp/goo.txt']
    >>> a.foo
    ['/software/temp/foo.txt', '/software/temp/goo.txt']

    """
    pass
