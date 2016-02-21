# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Definition of inputs/outputs of interfaces.
"""

from __future__ import print_function
from __future__ import division

from copy import deepcopy
import os
import re
from textwrap import wrap

from future import standard_library
standard_library.install_aliases()
from builtins import range
from builtins import object

from traits.api import Interface, provides
from ...utils.filemanip import md5, auto_hash, split_filename
from ...utils.misc import is_container
from ...utils.errors import InterfaceInputsError
from ... import logging, LooseVersion
from ... import __version__
from ...external.six import string_types

from .traits_extension import (traits, Undefined, TraitDictObject, TraitListObject, TraitError,
                               isdefined, File, has_metadata)


NIPYPE_VERSION = LooseVersion(__version__)
IFLOGGER = logging.getLogger('interface')
__docformat__ = 'restructuredtext'

class IInputSpec(Interface):
    """The abstract interface for inputs specifications"""
    def items(self):
        """Name, trait generator for user modifiable traits"""

    def check_inputs(self):
        """Checks the correctness of inputs set"""

    def check_version(self):
        """
        Checks if the version the implemented interface
        matches that of the installed software
        """

    def get_outputs(self):
        """Infers the outputs and returns a dictionary of results"""

    @classmethod
    def help(cls):
        """Print help of these traits"""


class IOutputSpec(Interface):
    """The abstract interface for outputs specifications"""
    def items(self):
        """Name, trait generator for user modifiable traits"""

    @classmethod
    def help(cls):
        """Print help of these traits"""


class IInputCommandLineSpec(Interface):
    def parse_args(self):
        """Parse inputs to commandline arguments"""


@provides(IInputSpec)
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

        # Attach deprecated handler
        has_deprecation = dict(deprecated=lambda t: t is not None)
        deprecated = self.trait_names(**has_deprecation)
        for elem in deprecated:
            self.on_trait_change(self._check_deprecated, elem)

        # Forward inputs
        self.set(**kwargs)

    def __repr__(self):
        """ Return a well-formatted representation of the traits """
        outstr = []
        for name, value in sorted(self.trait_get().items()):
            outstr.append('%s = %s' % (name, value))
        return '\n' + '\n'.join(outstr) + '\n'

    def items(self):
        """ Name, trait generator for user modifiable traits
        """
        for name in sorted(self.copyable_trait_names()):
            yield name, self.traits()[name]

    def _check_deprecated(self, name, new):
        """ Generate a warning when a deprecated trait is set """
        if isdefined(new):
            spec = self.traits()[name]
            msg1 = ('Input %s in interface %s is deprecated.' %
                    (name,
                     self.__class__.__name__.split('InputSpec')[0]))
            msg2 = ('Will be removed or raise an error as of release %s'
                    % spec.deprecated)
            if spec.new_name:
                if spec.new_name not in self.copyable_trait_names():
                    raise TraitError(msg1 + ' Replacement trait %s not found' %
                                     spec.new_name)
                msg3 = 'It has been replaced by %s.' % spec.new_name
            else:
                msg3 = ''
            msg = ' '.join((msg1, msg2, msg3))
            if LooseVersion(str(spec.deprecated)) < NIPYPE_VERSION:
                raise TraitError(msg)
            else:
                if spec.new_name:
                    msg += 'Unsetting old value %s; setting new value %s.' % (
                        name, spec.new_name)
                IFLOGGER.warn(msg)
                if spec.new_name:
                    self.trait_set(trait_change_notify=False,
                                   **{'%s' % name: Undefined,
                                      '%s' % spec.new_name: new})

    def _hash_infile(self, adict, key):
        """ Inject file hashes into adict[key]"""
        stuff = adict[key]
        if not is_container(stuff):
            stuff = [stuff]
        file_list = []
        for afile in stuff:
            if is_container(afile):
                hashlist = self._hash_infile({'infiles': afile}, 'infiles')
                hashval = [val[1] for val in hashlist]
            else:
                hashval = auto_hash(afile)

            file_list.append((afile, hashval))
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
            outdict = {}
            for key, val in list(obj.items()):
                if isdefined(val):
                    outdict[key] = self._clean_container(val, undefinedval)
                else:
                    if not skipundefined:
                        outdict[key] = undefinedval
            return outdict
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
                return tuple(out)
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
        out = None
        if isinstance(obj, dict):
            obj_items = [(key, val) for key, val in sorted(obj.items()) if isdefined(val)]
            out = [(key, self._get_sorteddict(val, dictwithhash, hash_method=hash_method,
                                               hash_files=hash_files)) for key, val in obj_items]
        elif isinstance(obj, (list, tuple)):
            out = [self._get_sorteddict(
                val, dictwithhash, hash_method=hash_method, hash_files=hash_files)
                for val in obj if isdefined(val)]
            if isinstance(obj, tuple):
                return tuple(out)
        elif isinstance(obj, float):
            out = '%.10f' % obj
        elif isinstance(obj, string_types) and hash_files and os.path.isfile(obj):
            out = auto_hash(obj, hash_method)
            if dictwithhash:
                return (obj, out)
        elif isdefined(obj):
            out = obj
        return out

    def _get_trait_desc(self, name, spec=None):
        if spec is None:
            spec = self.traits()[name]

        desc = spec.desc
        xor = spec.xor
        requires = spec.requires
        argstr = spec.argstr
        name_source = spec.name_source
        if name_source is None:
            name_source = spec.ns

        manhelpstr = ['\t%s' % name]

        type_info = spec.full_info(self, name, None)

        default = ''
        if spec.usedefault:
            default = ', nipype default value: %s' % str(spec.default_value()[1])
        line = "(%s%s)" % (type_info, default)

        manhelpstr = wrap(line, 70,
                          initial_indent=manhelpstr[0] + ': ',
                          subsequent_indent='\t\t ')

        if desc:
            for line in desc.split('\n'):
                line = re.sub(r'\s+', ' ', line)
                manhelpstr += wrap(line, 70, initial_indent='\t\t',
                                   subsequent_indent='\t\t')

        if argstr:
            pos = spec.position
            if pos is not None:
                manhelpstr += wrap('flag: %s, position: %s' % (argstr, pos), 70,
                                   initial_indent='\t\t', subsequent_indent='\t\t')
            else:
                manhelpstr += wrap('flag: %s' % argstr, 70, initial_indent='\t\t',
                                   subsequent_indent='\t\t')

        if xor:
            line = '%s' % ', '.join(xor)
            manhelpstr += wrap(line, 70, initial_indent='\t\tmutually_exclusive: ',
                               subsequent_indent='\t\t ')

        if requires:
            others = [field for field in requires if field != name]
            line = '%s' % ', '.join(others)
            manhelpstr += wrap(line, 70, initial_indent='\t\trequires: ',
                               subsequent_indent='\t\t ')

        if name_source:
            tpl = ', name_template not defined'
            if spec.name_template:
                tpl = ', name_template is \'%s\'' % spec.name_template
            manhelpstr += wrap(('name source: %s' % name_source) + tpl, 70,
                               initial_indent='\t\t', subsequent_indent='\t\t ')
        return manhelpstr

    def help(self):
        """Print help of these traits"""
        helpstr = []
        for name, spec in sorted(self.traits(transient=None).items()):
            helpstr += self._get_trait_desc(name, spec)
        if len(helpstr) == 0:
            helpstr += ['\tNone']
        return helpstr


class TraitedSpec(BaseTraitedSpec):
    """ Create a subclass with strict traits.

    This is used in 90% of the cases.
    """
    _ = traits.Disallow


@provides(IInputSpec)
class BaseInputSpec(BaseTraitedSpec):
    """ Base class for InputSpecs with strict traits """
    _ = traits.Disallow

    def __init__(self, **kwargs):
        """ Initialize handlers and inputs"""
        super(BaseInputSpec, self).__init__(**kwargs)

        # Attach xor handler
        has_xor = dict(xor=lambda t: t is not None)
        xors = self.trait_names(**has_xor)
        for elem in xors:
            self.on_trait_change(self._check_xor, elem)

    def mandatory_items(self):
        """Get those items that are mandatory"""
        return list(self.traits(mandatory=True).items())

    def optional_items(self):
        """Get those items that are optional"""
        allitems = self.traits(transient=None).items()
        for k, _ in self.mandatory_items():
            try:
                allitems.remove(k)
            except ValueError:
                pass
        return allitems

    def _check_xor(self, obj, name, old, new):
        """ Checks inputs with xor list """
        IFLOGGER.error('Called check_xorg with name %s' % name)
        if isdefined(getattr(self, name)):
            xor_list = self.traits()[name].xor
            if not isinstance(xor_list, list):
                xor_list = list(xor_list)

            if name in xor_list:
                xor_list.remove(name)
            # for each xor, set to default_value
            for trait_name in xor_list:
                trait_val = getattr(self, trait_name)
                if isdefined(trait_val) and isinstance(trait_val, bool) and not trait_val:
                    trait_val = Undefined  # Boolean inputs set false should not count as defined
                if isdefined(trait_val):
                    self.trait_set(trait_change_notify=False,
                                   **{'%s' % name: Undefined})
                    msg = ('Input "%s" is mutually exclusive with input "%s", '
                           'which is already set') % (name, trait_name)
                    raise TraitError(msg)

    def _check_requires(self, name, spec=None):
        if not isdefined(getattr(self, name)):
            return True
        if spec is None:
            spec = self.traits()[name]
        if spec.requires is None:
            return True

        req_defined = [isdefined(rname) for rname in getattr(spec, 'requires', [])]
        if not all(req_defined):
            raise ValueError(
                '%s requires a value for input \'%s\' because one of %s is set. For a list of'
                ' required inputs, see %s.help()' % (self.__class__.__name__, name,
                ', '.join(spec.requires), self.__class__.__name__))
        return True


    def check_inputs(self):
        """ Raises an exception if a mandatory input is Undefined
        """
        for name, spec in list(self.mandatory_items()):
            value = getattr(self, name)
            if not isdefined(value):
                xor_spec = getattr(spec, 'xor', [])
                if xor_spec is None:
                    xor_spec = []

                if xor_spec and not any([isdefined(getattr(self, xname)) for xname in xor_spec]):
                    raise ValueError(
                        '%s requires a value for one of these inputs %s. For a list of required inputs, '
                        'see %s.help()' % (self.__class__.__name__, [name] + xor_spec, self.__class__.__name__))
            self._check_requires(name)

        for elem in list(self.optional_items()):
            self._check_requires(*elem)

    def get_filecopy_info(self):
        """ Provides information about file inputs to copy or link to cwd.
            Necessary for pipeline operation
        """
        info = []
        metadata = dict(copyfile=lambda t: t is not None)
        for name, spec in sorted(self.traits(**metadata).items()):
            info.append(dict(key=name, copy=spec.copyfile))
        return info

    def check_version(self, version, raise_exception=True):
        """ Raises an exception on version mismatch"""
        unavailable_traits = []
        # check minimum version
        check = dict(min_ver=lambda t: t is not None)

        for name in self.trait_names(**check):
            min_ver = LooseVersion(str(self.traits()[name].min_ver))
            if min_ver > version:
                unavailable_traits.append(name)
                if not isdefined(getattr(self, name)):
                    continue

                msg = ('Trait %s (%s) (version %s < required %s)' %
                       (name, self.__class__.__name__, version, min_ver))
                if raise_exception:
                    raise Exception(msg)
                else:
                    IFLOGGER.warn(msg)

        # Check maximum version
        check = dict(max_ver=lambda t: t is not None)
        for name in self.trait_names(**check):
            max_ver = LooseVersion(str(self.traits()[name].max_ver))
            if max_ver < version:
                unavailable_traits.append(name)
                if not isdefined(getattr(self, name)):
                    continue
                msg = ('Trait %s (%s) (version %s > required %s)' %
                       (name, self.__class__.__name__, version, max_ver))
                if raise_exception:
                    raise Exception(msg)
                else:
                    IFLOGGER.warn(msg)

        return unavailable_traits

    def help(self):
        """Print inputs formatted"""
        manhelpstr = []
        for name, spec in sorted(self.mandatory_items()):
            manhelpstr += self._get_trait_desc(name, spec)
        opthelpstr = []
        for name, spec in sorted(self.optional_items()):
            opthelpstr += self._get_trait_desc(name, spec)

        helpstr = []
        if manhelpstr:
            manhelpstr.insert(0, '')
            manhelpstr.insert(1, '\t[Mandatory]')
            helpstr += manhelpstr
        if opthelpstr:
            opthelpstr.insert(0, '')
            opthelpstr.insert(1, '\t[Optional]')
            helpstr += opthelpstr

        if not helpstr:
            return ['', '\tNone']

        return helpstr


@provides(IInputSpec)
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


@provides(IInputSpec)
class BaseInterfaceInputSpec(BaseInputSpec):
    """ BaseInputSpec with an input added to ignore exceptions """
    ignore_exception = traits.Bool(False, usedefault=True, nohash=True,
                                   desc='Print an error message instead of throwing an exception'
                                        ' in case the interface fails to run')


@provides(IInputSpec, IInputCommandLineSpec)
class CommandLineInputSpec(BaseInterfaceInputSpec):
    """ The InputSpec for interfaces wrapping a command line """
    args = traits.Str(argstr='%s', desc='Additional parameters to the command')

    def _format_arg(self, name, spec=None, value=None):
        """A helper function for parse_args

        Formats a trait containing argstr metadata
        """
        if spec is None:
            spec = self.traits()[name]

        if value is None:
            value = getattr(self, name)

        argstr = spec.argstr
        IFLOGGER.debug('Formatting %s, value=%s' % (name, str(value)))
        if spec.is_trait_type(traits.Bool) and "%" not in argstr:
            if value:
                # Boolean options have no format string. Just append options
                # if True.
                return argstr
            else:
                return None
        # traits.Either turns into traits.TraitCompound and does not have any
        # inner_traits
        elif spec.is_trait_type(traits.List) \
            or (spec.is_trait_type(traits.TraitCompound) and
                isinstance(value, list)):
            # This is a bit simple-minded at present, and should be
            # construed as the default. If more sophisticated behavior
            # is needed, it can be accomplished with metadata (e.g.
            # format string for list member str'ification, specifying
            # the separator, etc.)

            # Depending on whether we stick with traitlets, and whether or
            # not we beef up traitlets.List, we may want to put some
            # type-checking code here as well
            sep = spec.sep
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

    def parse_args(self, skip=None):
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
        for name, spec in sorted(self.traits(**metadata).items()):
            if skip and name in skip:
                continue
            value = getattr(self, name)
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
        first_args = [arg for pos, arg in sorted(initial_args.items())]
        last_args = [arg for pos, arg in sorted(final_args.items())]
        return first_args + all_args + last_args


class StdOutCommandLineInputSpec(CommandLineInputSpec):
    """Appends a command line argument to pipe standard output to a file"""
    out_file = File('standard.out', argstr="> %s", position=-1, usedefault=True)

class StdOutCommandLineOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='file containing the standard output')


@provides(IInputSpec, IInputCommandLineSpec)
class MpiCommandLineInputSpec(CommandLineInputSpec):
    """Appends the necessary inputs to run MpiCommandLine interfaces"""
    use_mpi = traits.Bool(False, usedefault=True,
                          desc='Whether or not to run the command with mpiexec')
    n_procs = traits.Int(desc='Num processors to specify to mpiexec. Do not specify if this '
                              'is managed externally (e.g. through SGE)')


@provides(IInputSpec, IInputCommandLineSpec)
class SEMLikeCommandLineInputSpec(CommandLineInputSpec):
    """Redefines the formatting of outputs"""

    def _format_arg(self, name, spec=None, value=None):
        if name in list(self._outputs_filenames.keys()):
            if isinstance(value, bool):
                if value:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(SEMLikeCommandLineInputSpec, self)._format_arg(name, spec, value)
