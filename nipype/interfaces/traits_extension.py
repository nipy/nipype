# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""This module contains Trait classes that we've pulled from the
traits source and fixed due to various bugs.  File and Directory are
redefined as the release version had dependencies on TraitsUI, which
we do not want Nipype to depend on.  At least not yet.
"""

#from traits.api import File, Directory

from ..external import traitlets as traits
from ..external.traitlets import TraitError, File, Directory
from ..external.traitlets import _Undefined, Undefined
from ..external.traitlets import Dict as TraitDictObject
from ..external.traitlets import List as TraitListObject

def isdefined(object):
    return not isinstance(object, _Undefined)

def has_metadata(trait, metadata, value=None, recursive=True):
    '''
    Checks if a given trait has a metadata (and optionally if it is set to
    particular value)
    '''
    count = 0
    if hasattr(trait, "_metadata") and metadata in trait._metadata.keys() and \
            (trait._metadata[metadata] == value or value==None):
        count += 1
    if recursive:
        if hasattr(trait, 'inner_traits'):
            for inner_trait in trait.inner_traits():
                count += has_metadata(inner_trait, metadata,
                                      recursive)
        if hasattr(trait, 'handlers') and trait.handlers != None:
            for handler in trait.handlers:
                count += has_metadata(handler, metadata, recursive)

    return count > 0


import os

from warnings import warn
from ..utils.misc import is_container
from ..utils.filemanip import (md5, hash_infile, hash_timestamp)
from .. import config, LooseVersion
from .. import __version__

nipype_version = LooseVersion(__version__)

def _get_sorteddict(object, dictwithhash=False, hash_method=None,
                    hash_files=True):
    out = None
    if isinstance(object, dict):
        out = {}
        for key, val in sorted(object.items()):
            if isdefined(val):
                out[key] = \
                    _get_sorteddict(val, dictwithhash,
                                         hash_method=hash_method,
                                         hash_files=hash_files)
    elif isinstance(object, (list, tuple)):
        out = []
        for val in object:
            if isdefined(val):
                out.append(_get_sorteddict(val, dictwithhash,
                                                hash_method=hash_method,
                                                hash_files=hash_files))
        if isinstance(object, tuple):
            out = tuple(out)
    else:
        if isdefined(object):
            if (hash_files and isinstance(object, str) and
                    os.path.isfile(object)):
                if hash_method is None:
                    hash_method = config.get('execution', 'hash_method')

                if hash_method.lower() == 'timestamp':
                    hash = hash_timestamp(object)
                elif hash_method.lower() == 'content':
                    hash = hash_infile(object)
                else:
                    raise Exception("Unknown hash method: %s" % hash_method)
                if dictwithhash:
                    out = (object, hash)
                else:
                    out = hash
            elif isinstance(object, float):
                out = '%.10f' % object
            else:
                out = object
    return out

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
        super(BaseTraitedSpec, self).__init__(**kwargs)
        undefined_traits = {}
        for name, trait in self.traits().items():
            if trait.get_metadata('usedefault') is None:
                undefined_traits[name] = Undefined
        self.set(**undefined_traits)
        self._generate_handlers()
        self.set(**kwargs)

    def items(self):
        """ Name, trait generator for user modifiable traits
        """
        for name in sorted(self.trait_names()):
            yield name, self.traits()[name]

    def __repr__(self):
        """ Return a well-formatted representation of the traits """
        outstr = []
        for name, value in sorted(self.get().items()):
            outstr.append('%s = %s' % (name, value))
        return '\n' + '\n'.join(outstr) + '\n'

    def get(self, **kwargs):
        """ Returns traited class as a dict

        Augments the trait get function to return a dictionary without
        notification handles
        """
        out = dict([(key, getattr(self, key)) for key in self.trait_names()])
        out = self._clean_container(out, Undefined)
        return out

    def set(self, **kwargs):
        """ Returns traited class as a dict

        Augments the trait get function to return a dictionary without
        notification handles
        """
        for key, val in kwargs.items():
            setattr(self, key, val)

    def trait(self, name):
        return self.traits()[name]

    def get_traitsfree(self, **kwargs):
        """ Returns traited class as a dict

        Augments the trait get function to return a dictionary without
        any traits. The dictionary does not contain any attributes that
        were Undefined
        """
        out = dict([(key, getattr(self, key)) for key in self.trait_names()])
        out = self._clean_container(out, skipundefined=True)
        return out

    def _clean_container(self, object, undefinedval=None, skipundefined=False):
        """Convert a traited obejct into a pure python representation.
        """
        if isinstance(object, TraitDictObject) or isinstance(object, dict):
            out = {}
            for key, val in object.items():
                if isdefined(val):
                    out[key] = self._clean_container(val, undefinedval)
                else:
                    if not skipundefined:
                        out[key] = undefinedval
        elif (isinstance(object, TraitListObject) or isinstance(object, list)
              or isinstance(object, tuple)):
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

    def _xor_warn(self, name, old, new):
        """ Generates warnings for xor traits
        """
        if isdefined(new):
            trait_spec = self.traits()[name]
            # for each xor, set to default_value
            for trait_name in trait_spec.get_metadata('xor'):
                if trait_name == name:
                    # skip ourself
                    continue
                if isdefined(getattr(self, trait_name)):
                    self.set(**{'%s' % name: Undefined})
                    msg = ('Input "%s" is mutually exclusive with input "%s", '
                           'which is already set') % (name, trait_name)
                    raise IOError(msg)

    def _requires_warn(self, name, old, new):
        """Part of the xor behavior
        """
        if isdefined(new):
            trait_spec = self.traits()[name]
            msg = None
            requires = trait_spec.get_metadata('requires')
            for trait_name in requires:
                if not isdefined(getattr(self, trait_name)):
                    if not msg:
                        msg = 'Input %s requires inputs: %s' \
                            % (name, ', '.join(requires))
            if msg:
                warn(msg)

    def _deprecated_warn(self, name, old, new):
        """Checks if a user assigns a value to a deprecated trait
        """
        if isdefined(new):
            trait_spec = self.traits()[name]
            msg1 = ('Input %s in interface %s is deprecated.' %
                    (name,
                     self.__class__.__name__.split('InputSpec')[0]))
            deprecated = trait_spec.get_metadata('deprecated')
            msg2 = ('Will be removed or raise an error as of release %s'
                    % deprecated)
            new_name = trait_spec.get_metadata('new_name')
            if new_name:
                if new_name not in self.trait_names():
                    raise TraitError(msg1 + ' Replacement trait %s not found' %
                                     new_name)
                msg3 = 'It has been replaced by %s.' % new_name
            else:
                msg3 = ''
            msg = ' '.join((msg1, msg2, msg3))
            if LooseVersion(str(deprecated)) < nipype_version:
                raise TraitError(msg)
            else:
                warn(msg)
                if new_name:
                    warn('Unsetting %s and setting %s.' % (name,
                                                           new_name))
                    self.set(**{'%s' % name: Undefined,
                                '%s' % new_name: new})

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

        dict_withhash = {}
        dict_nofilename = {}
        for name, val in sorted(self.get().items()):
            if isdefined(val):
                trait = self.traits()[name]
                print name
                if has_metadata(trait, "nohash", True):
                    continue
                hash_files = (not has_metadata(trait, "hash_files", False)
                              and not has_metadata(trait, "name_source", False))
                dict_nofilename[name] = _get_sorteddict(val,
                                                        hash_method=hash_method,
                                                        hash_files=hash_files)
                dict_withhash[name] = _get_sorteddict(val, True,
                                                      hash_method=hash_method,
                                                      hash_files=hash_files)
                print dict_withhash
        return (dict_withhash, md5(str(dict_nofilename)).hexdigest())

