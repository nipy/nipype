# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""

Base I/O specifications for Nipype interfaces
.............................................

Define the API for the I/O of interfaces

"""
import os
from inspect import isclass
from copy import deepcopy
from warnings import warn
from packaging.version import Version

from traits.trait_errors import TraitError
from traits.trait_handlers import TraitDictObject, TraitListObject
from ...utils.filemanip import md5, hash_infile, hash_timestamp
from .traits_extension import (
    traits,
    File,
    Str,
    Undefined,
    isdefined,
    has_metadata,
    OutputMultiObject,
)

from ... import config, __version__

_float_fmt = "{:.10f}".format
nipype_version = Version(__version__)


class BaseTraitedSpec(traits.HasTraits):
    """
    Provide a few methods necessary to support nipype interface api

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
            outstr.append("%s = %s" % (name, value))
        return "\n{}\n".format("\n".join(outstr))

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
                    self.trait_set(
                        trait_change_notify=False, **{"%s" % name: Undefined}
                    )
                    msg = (
                        'Input "%s" is mutually exclusive with input "%s", '
                        "which is already set"
                    ) % (name, trait_name)
                    raise IOError(msg)

    def _deprecated_warn(self, obj, name, old, new):
        """Checks if a user assigns a value to a deprecated trait
        """
        if isdefined(new):
            trait_spec = self.traits()[name]
            msg1 = "Input %s in interface %s is deprecated." % (
                name,
                self.__class__.__name__.split("InputSpec")[0],
            )
            msg2 = (
                "Will be removed or raise an error as of release %s"
                % trait_spec.deprecated
            )
            if trait_spec.new_name:
                if trait_spec.new_name not in self.copyable_trait_names():
                    raise TraitError(
                        msg1 + " Replacement trait %s not found" % trait_spec.new_name
                    )
                msg3 = "It has been replaced by %s." % trait_spec.new_name
            else:
                msg3 = ""
            msg = " ".join((msg1, msg2, msg3))
            if Version(str(trait_spec.deprecated)) < self.package_version:
                raise TraitError(msg)
            else:
                if trait_spec.new_name:
                    msg += "Unsetting old value %s; setting new value %s." % (
                        name,
                        trait_spec.new_name,
                    )
                warn(msg)
                if trait_spec.new_name:
                    self.trait_set(
                        trait_change_notify=False,
                        **{"%s" % name: Undefined, "%s" % trait_spec.new_name: new}
                    )

    def trait_get(self, **kwargs):
        """ Returns traited class as a dict

        Augments the trait get function to return a dictionary without
        notification handles
        """
        out = super(BaseTraitedSpec, self).trait_get(**kwargs)
        out = self._clean_container(out, Undefined)
        return out

    get = trait_get

    def get_traitsfree(self, **kwargs):
        """ Returns traited class as a dict

        Augments the trait get function to return a dictionary without
        any traits. The dictionary does not contain any attributes that
        were Undefined
        """
        out = super(BaseTraitedSpec, self).trait_get(**kwargs)
        out = self._clean_container(out, skipundefined=True)
        return out

    def _clean_container(self, objekt, undefinedval=None, skipundefined=False):
        """Convert a traited obejct into a pure python representation.
        """
        if isinstance(objekt, TraitDictObject) or isinstance(objekt, dict):
            out = {}
            for key, val in list(objekt.items()):
                if isdefined(val):
                    out[key] = self._clean_container(val, undefinedval)
                else:
                    if not skipundefined:
                        out[key] = undefinedval
        elif (
            isinstance(objekt, TraitListObject)
            or isinstance(objekt, list)
            or isinstance(objekt, tuple)
        ):
            out = []
            for val in objekt:
                if isdefined(val):
                    out.append(self._clean_container(val, undefinedval))
                else:
                    if not skipundefined:
                        out.append(undefinedval)
                    else:
                        out.append(None)
            if isinstance(objekt, tuple):
                out = tuple(out)
        else:
            out = None
            if isdefined(objekt):
                out = objekt
            else:
                if not skipundefined:
                    out = undefinedval
        return out

    def has_metadata(self, name, metadata, value=None, recursive=True):
        """
        Return has_metadata for the requested trait name in this
        interface
        """
        return has_metadata(self.trait(name).trait_type, metadata, value, recursive)

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
        list_withhash : dict
            Copy of our dictionary with the new file hashes included
            with each file.
        hashvalue : str
            The md5 hash value of the traited spec

        """
        list_withhash = []
        list_nofilename = []
        for name, val in sorted(self.trait_get().items()):
            if not isdefined(val) or self.has_metadata(name, "nohash", True):
                # skip undefined traits and traits with nohash=True
                continue

            hash_files = not self.has_metadata(
                name, "hash_files", False
            ) and not self.has_metadata(name, "name_source")
            list_nofilename.append(
                (
                    name,
                    self._get_sorteddict(
                        val, hash_method=hash_method, hash_files=hash_files
                    ),
                )
            )
            list_withhash.append(
                (
                    name,
                    self._get_sorteddict(
                        val, True, hash_method=hash_method, hash_files=hash_files
                    ),
                )
            )
        return list_withhash, md5(str(list_nofilename).encode()).hexdigest()

    def _get_sorteddict(
        self, objekt, dictwithhash=False, hash_method=None, hash_files=True
    ):
        if isinstance(objekt, dict):
            out = []
            for key, val in sorted(objekt.items()):
                if isdefined(val):
                    out.append(
                        (
                            key,
                            self._get_sorteddict(
                                val,
                                dictwithhash,
                                hash_method=hash_method,
                                hash_files=hash_files,
                            ),
                        )
                    )
        elif isinstance(objekt, (list, tuple)):
            out = []
            for val in objekt:
                if isdefined(val):
                    out.append(
                        self._get_sorteddict(
                            val,
                            dictwithhash,
                            hash_method=hash_method,
                            hash_files=hash_files,
                        )
                    )
            if isinstance(objekt, tuple):
                out = tuple(out)
        else:
            out = None
            if isdefined(objekt):
                if (
                    hash_files
                    and isinstance(objekt, (str, bytes))
                    and os.path.isfile(objekt)
                ):
                    if hash_method is None:
                        hash_method = config.get("execution", "hash_method")

                    if hash_method.lower() == "timestamp":
                        hash = hash_timestamp(objekt)
                    elif hash_method.lower() == "content":
                        hash = hash_infile(objekt)
                    else:
                        raise Exception("Unknown hash method: %s" % hash_method)
                    if dictwithhash:
                        out = (objekt, hash)
                    else:
                        out = hash
                elif isinstance(objekt, float):
                    out = _float_fmt(objekt)
                else:
                    out = objekt
        return out

    @property
    def __all__(self):
        return self.copyable_trait_names()

    def __getstate__(self):
        """
        Override __getstate__ so that OutputMultiObjects are correctly pickled.

        >>> class OutputSpec(TraitedSpec):
        ...     out = OutputMultiObject(traits.List(traits.Int))
        >>> spec = OutputSpec()
        >>> spec.out = [[4]]
        >>> spec.out
        [4]

        >>> spec.__getstate__()['out']
        [[4]]

        >>> spec.__setstate__(spec.__getstate__())
        >>> spec.out
        [4]

        """
        state = super(BaseTraitedSpec, self).__getstate__()
        for key in self.__all__:
            _trait_spec = self.trait(key)
            if _trait_spec.is_trait_type(OutputMultiObject):
                state[key] = _trait_spec.handler.get_value(self, key)
        return state


class TraitedSpec(BaseTraitedSpec):
    """ Create a subclass with strict traits.

    This is used in 90% of the cases.
    """

    _ = traits.Disallow


class BaseInterfaceInputSpec(TraitedSpec):
    pass


class DynamicTraitedSpec(BaseTraitedSpec):
    """ A subclass to handle dynamic traits

    This class is a workaround for add_traits and clone_traits not
    functioning well together.
    """

    def __deepcopy__(self, memo):
        """
        Replace the ``__deepcopy__`` member with a traits-friendly implementation.

        A bug in ``__deepcopy__`` for ``HasTraits`` results in weird cloning behaviors.
        """
        id_self = id(self)
        if id_self in memo:
            return memo[id_self]
        dup_dict = deepcopy(self.trait_get(), memo)
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


class CommandLineInputSpec(BaseInterfaceInputSpec):
    args = Str(argstr="%s", desc="Additional parameters to the command")
    environ = traits.DictStrStr(
        desc="Environment variables", usedefault=True, nohash=True
    )


class StdOutCommandLineInputSpec(CommandLineInputSpec):
    out_file = File(argstr="> %s", position=-1, genfile=True)


class MpiCommandLineInputSpec(CommandLineInputSpec):
    use_mpi = traits.Bool(
        False, desc="Whether or not to run the command with mpiexec", usedefault=True
    )
    n_procs = traits.Int(
        desc="Num processors to specify to mpiexec. Do not "
        "specify if this is managed externally (e.g. through "
        "SGE)"
    )


def get_filecopy_info(cls):
    """Provides information about file inputs to copy or link to cwd.
    Necessary for pipeline operation
    """
    if cls.input_spec is None:
        return None

    # normalize_filenames is not a classmethod, hence check first
    if not isclass(cls) and hasattr(cls, "normalize_filenames"):
        cls.normalize_filenames()
    info = []
    inputs = cls.input_spec() if isclass(cls) else cls.inputs
    metadata = dict(copyfile=lambda t: t is not None)
    for name, spec in sorted(inputs.traits(**metadata).items()):
        info.append(dict(key=name, copy=spec.copyfile))
    return info
