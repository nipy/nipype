# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Package contains interfaces for using existing functionality in other packages

Exaples  FSL, matlab/SPM , afni

Requires Packages to be installed
"""

from ConfigParser import NoOptionError
from copy import deepcopy
import datetime
import errno
import os
from socket import gethostname
from string import Template
import select
import subprocess
from textwrap import wrap
from time import time
from warnings import warn

from .traits_extension import (traits, Undefined, TraitDictObject,
                               TraitListObject, TraitError,
                               isdefined, File, Directory,
                               has_metadata)
from ..utils.filemanip import (md5, hash_infile, FileNotFoundError,
                               hash_timestamp)
from ..utils.misc import is_container, trim
from .. import config, logging

iflogger = logging.getLogger('interface')


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
        return self.__dict__.items()

    def iteritems(self):
        """iterates over bunch attributes as key, value pairs"""
        warn('iteritems is deprecated, use items instead')
        return self.items()

    def get(self, *args):
        '''Support dictionary get() functionality
        '''
        return self.__dict__.get(*args)

    def set(self, **kwargs):
        '''Support dictionary get() functionality
        '''
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
                fp = file(afile, 'rb')
                while True:
                    data = fp.read(8192)
                    if not data:
                        break
                    md5obj.update(data)
                fp.close()
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
        for key, val in self.items():
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
        return (dict_withhash, md5(sorted_dict).hexdigest())

    def __pretty__(self, p, cycle):
        '''Support for the pretty module

        pretty is included in ipython.externals for ipython > 0.10'''
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

    def __init__(self, interface, runtime, inputs=None, outputs=None):
        self._version = 1.0
        self.interface = interface
        self.runtime = runtime
        self.inputs = inputs
        self.outputs = outputs

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

    * get_hashval : returns a tuple containing the state of the trait as a dict and
      hashvalue corresponding to dict.

    XXX Reconsider this in the long run, but it seems like the best
    solution to move forward on the refactoring.
    """

    def __init__(self, **kwargs):
        """ Initialize handlers and inputs"""
        # NOTE: In python 2.6, object.__init__ no longer accepts input
        # arguments.  HasTraits does not define an __init__ and
        # therefore these args were being ignored.
        #super(TraitedSpec, self).__init__(*args, **kwargs)
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
                    self.trait_set(trait_change_notify=False, **{'%s' % name: Undefined})
                    msg = 'Input "%s" is mutually exclusive with input "%s", ' \
                          'which is already set' \
                            % (name, trait_name)
                    raise IOError(msg)

    def _requires_warn(self, obj, name, old, new):
        """Part of the xor behavior
        """
        if new:
            trait_spec = self.traits()[name]
            msg = None
            for trait_name in trait_spec.requires:
                if not isdefined(getattr(self, trait_name)):
                    if not msg:
                        msg = 'Input %s requires inputs: %s' \
                            % (name, ', '.join(trait_spec.requires))
            if msg:
                warn(msg)

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
                if config.get('execution', 'hash_method').lower() == 'timestamp':
                    hash = hash_timestamp(afile)
                elif config.get('execution', 'hash_method').lower() == 'content':
                    hash = hash_infile(afile)
                else:
                    raise Exception("Unknown hash method: %s" % config.get('execution', 'hash_method'))
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
            for key, val in object.items():
                if isdefined(val):
                    out[key] = self._clean_container(val, undefinedval)
                else:
                    if not skipundefined:
                        out[key] = undefinedval
        elif isinstance(object, TraitListObject) or isinstance(object, list) or \
                isinstance(object, tuple):
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
                trait = self.trait(name)
                if has_metadata(trait.trait_type, "nohash", True):
                    continue
                hash_files = not has_metadata(trait.trait_type, "hash_files", False)
                dict_nofilename[name] = self._get_sorteddict(val, hash_method=hash_method, hash_files=hash_files)
                dict_withhash[name] = self._get_sorteddict(val, True, hash_method=hash_method, hash_files=hash_files)
        return (dict_withhash, md5(str(dict_nofilename)).hexdigest())

    def _get_sorteddict(self, object, dictwithhash=False, hash_method=None, hash_files=True):
        if isinstance(object, dict):
            out = {}
            for key, val in sorted(object.items()):
                if isdefined(val):
                    out[key] = self._get_sorteddict(val, dictwithhash, hash_method=hash_method, hash_files=hash_files)
        elif isinstance(object, (list, tuple)):
            out = []
            for val in object:
                if isdefined(val):
                    out.append(self._get_sorteddict(val, dictwithhash, hash_method=hash_method, hash_files=hash_files))
            if isinstance(object, tuple):
                out = tuple(out)
        else:
            if isdefined(object):
                if hash_files and isinstance(object, str) and os.path.isfile(object):
                    if hash_method == None:
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


class Interface(object):
    """This is an abstract definition for Interface objects.

    It provides no functionality.  It defines the necessary attributes
    and methods all Interface objects should have.

    """

    input_spec = None  # A traited input specification
    output_spec = None  # A traited output specification

    _can_resume = False  # defines if the interface can reuse partial results after interruption

    @property
    def can_resume(self):
        return self._can_resume

    _always_run = False # should the interface be always run even if the inputs were not changed?

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
    ignore_exception = traits.Bool(False, desc="Print an error message instead \
of throwing an exception in case the interface fails to run", usedefault=True,
                                   nohash=True)


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

    def __init__(self, **inputs):
        if not self.input_spec:
            raise Exception('No input_spec in class: %s' % \
                                self.__class__.__name__)
        self.inputs = self.input_spec(**inputs)

    @classmethod
    def help(cls, returnhelp=False):
        """ Prints class help
        """

        if cls.__doc__:
            #docstring = cls.__doc__.split('\n')
            #docstring = [trim(line, '') for line in docstring]
            docstring = trim(cls.__doc__).split('\n') + ['']
        else:
            docstring = ['']

        allhelp = '\n'.join(docstring + cls._inputs_help() + [''] +
                            cls._outputs_help() + [''])
        if returnhelp:
            return allhelp
        else:
            print allhelp

    @classmethod
    def _get_trait_desc(self, inputs, name, spec):
        desc = spec.desc
        xor = spec.xor
        requires = spec.requires

        manhelpstr = ['\t%s' % name]
        try:
            setattr(inputs, name, None)
        except TraitError as excp:
            def_val = ''
            if getattr(spec, 'usedefault'):
                def_val = ', nipype default value: %s' % str(getattr(spec, 'default_value')()[1])
            line = "(%s%s)" % (excp.info, def_val)
            manhelpstr = wrap(line, 90, initial_indent=manhelpstr[0]+': ',
                              subsequent_indent='\t\t ')
        if desc:
            for line in desc.split('\n'):
                manhelpstr += wrap(line, 90, initial_indent='\t\t',
                                   subsequent_indent='\t\t')
        if xor:
            line = '%s' % ', '.join(xor)
            manhelpstr += wrap(line, 90, initial_indent='\t\tmutually_exclusive: ',
                               subsequent_indent='\t\t ')
        if requires: # and name not in xor_done:
            others = [field for field in requires if field != name]
            line = '%s' % ', '.join(others)
            manhelpstr += wrap(line, 90, initial_indent='\t\trequires: ',
                               subsequent_indent='\t\t ')
        return manhelpstr

    @classmethod
    def _inputs_help(cls):
        """ Prints description for input parameters
        """
        helpstr = ['Inputs::']

        inputs = cls.input_spec()
        if len(inputs.traits(transient=None).items()) == 0:
            helpstr += ['', '\tNone']
            return helpstr

        manhelpstr = ['', '\t[Mandatory]']
        for name, spec in sorted(inputs.traits(mandatory=True).items()):
            manhelpstr += cls._get_trait_desc(inputs, name, spec)

        opthelpstr = ['', '\t[Optional]']
        for name, spec in sorted(inputs.traits(mandatory=None,
                                               transient=None).items()):
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
            for name, spec in sorted(cls.output_spec().traits(transient=None).items()):
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
            info.append(dict(key=name,
                             copy=spec.copyfile))
        return info

    def _check_requires(self, spec, name, value):
        """ check if required inputs are satisfied
        """
        if spec.requires:
            values = [not isdefined(getattr(self.inputs, field)) for field in spec.requires]
            if any(values) and isdefined(value):
                msg = "%s requires a value for input '%s' because one of %s is set. " \
                    "For a list of required inputs, see %s.help()" % \
                    (self.__class__.__name__, name,
                     ', '.join(spec.requires), self.__class__.__name__)
                raise ValueError(msg)

    def _check_xor(self, spec, name, value):
        """ check if mutually exclusive inputs are satisfied
        """
        if spec.xor:
            values = [isdefined(getattr(self.inputs, field)) for field in spec.xor]
            if not any(values) and not isdefined(value):
                msg = "%s requires a value for one of the inputs '%s'. " \
                    "For a list of required inputs, see %s.help()" % \
                    (self.__class__.__name__, ', '.join(spec.xor),
                     self.__class__.__name__)
                raise ValueError(msg)

    def _check_mandatory_inputs(self):
        """ Raises an exception if a mandatory input is Undefined
        """
        for name, spec in self.inputs.traits(mandatory=True).items():
            value = getattr(self.inputs, name)
            self._check_xor(spec, name, value)
            if not isdefined(value) and spec.xor is None:
                msg = "%s requires a value for input '%s'. " \
                    "For a list of required inputs, see %s.help()" % \
                    (self.__class__.__name__, name, self.__class__.__name__)
                raise ValueError(msg)
            if isdefined(value):
                self._check_requires(spec, name, value)
        for name, spec in self.inputs.traits(mandatory=None,
                                             transient=None).items():
            self._check_requires(spec, name, getattr(self.inputs, name))

    def _run_interface(self, runtime):
        """ Core function that executes interface
        """
        raise NotImplementedError

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
        self.inputs.set(**inputs)
        self._check_mandatory_inputs()
        interface = self.__class__
        # initialize provenance tracking
        env = deepcopy(os.environ.data)
        runtime = Bunch(cwd=os.getcwd(),
                        returncode=None,
                        duration=None,
                        environ=env,
                        hostname=gethostname())
        t = time()
        try:
            runtime = self._run_interface(runtime)
            runtime.duration = time() - t
            results = InterfaceResult(interface, runtime,
                                      inputs=self.inputs.get_traitsfree())
            results.outputs = self.aggregate_outputs(results.runtime)
        except Exception, e:
            if len(e.args) == 0:
                e.args = ("")

            message = "\nInterface %s failed to run." % self.__class__.__name__

            if config.has_option('logging', 'interface_level') and config.get('logging', 'interface_level').lower() == 'debug':
                inputs_str = "Inputs:" + str(self.inputs) + "\n"
            else:
                inputs_str = ''

            if len(e.args) == 1 and isinstance(e.args[0], str):
                e.args = (e.args[0] + " ".join([message, inputs_str]),)
            else:
                e.args += (message, )
                if inputs_str != '':
                    e.args += (inputs_str, )

            #exception raising inhibition for special cases
            if hasattr(self.inputs, 'ignore_exception') and \
            isdefined(self.inputs.ignore_exception) and \
            self.inputs.ignore_exception:
                import traceback
                runtime.traceback = traceback.format_exc()
                runtime.traceback_args = e.args
                return InterfaceResult(interface, runtime)
            else:
                raise
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
            for key, val in predicted_outputs.items():
                if needed_outputs and key not in needed_outputs:
                    continue
                try:
                    setattr(outputs, key, val)
                    _ = getattr(outputs, key)
                except TraitError, error:
                    if hasattr(error, 'info') and error.info.startswith("an existing"):
                        msg = "File/Directory '%s' not found for %s output '%s'." \
                            % (val, self.__class__.__name__, key)
                        raise FileNotFoundError(msg)
                    else:
                        raise error
        return outputs


class Stream(object):
    """Function to capture stdout and stderr streams with timestamps

    http://stackoverflow.com/questions/4984549/merge-and-sync-stdout-and-stderr/5188359#5188359
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
        buf = os.read(fd, 4096)
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
        self._rows += [(now, '%s %s:%s' % (self._name, now, r), r) for r in rows]
        for idx in range(self._lastidx, len(self._rows)):
            iflogger.info(self._rows[idx][1])
        self._lastidx = len(self._rows)


def run_command(runtime, timeout=0.01):
    """
    Run a command, read stdout and stderr, prefix with timestamp. The returned
    runtime contains a merged stdout+stderr log with timestamps

    http://stackoverflow.com/questions/4984549/merge-and-sync-stdout-and-stderr/5188359#5188359
    """
    PIPE = subprocess.PIPE
    proc = subprocess.Popen(runtime.cmdline,
                             stdout=PIPE,
                             stderr=PIPE,
                             shell=True,
                             cwd=runtime.cwd,
                             env=runtime.environ)
    streams = [
        Stream('stdout', proc.stdout),
        Stream('stderr', proc.stderr)
        ]

    def _process(drain=0):
        try:
            res = select.select(streams, [], [], timeout)
        except select.error, e:
            iflogger.info(str(e))
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
    runtime.returncode = proc.returncode
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
    runtime.stderr = '\n'.join(result['stderr'])
    runtime.stdout = '\n'.join(result['stdout'])
    runtime.merged = result['merged']
    return runtime


class CommandLineInputSpec(BaseInterfaceInputSpec):
    args = traits.Str(argstr='%s', desc='Additional parameters to the command')
    environ = traits.DictStrStr(desc='Environment variables', usedefault=True,
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

    >>> from nipype.interfaces.base import CommandLine
    >>> cli = CommandLine(command='ls', environ={'DISPLAY': ':1'})
    >>> cli.inputs.args = '-al'
    >>> cli.cmdline
    'ls -al'

    >>> cli.inputs.trait_get()
    {'ignore_exception': False, 'args': '-al', 'environ': {'DISPLAY': ':1'}}

    >>> cli.inputs.get_hashval()
    ({'args': '-al'}, 'a2f45e04a34630c5f33a75ea2a533cdd')

    """

    input_spec = CommandLineInputSpec
    _cmd = None

    def __init__(self, command=None, **inputs):
        super(CommandLine, self).__init__(**inputs)
        self._environ = None
        if not hasattr(self, '_cmd'):
            self._cmd = None
        if self.cmd is None and command is None:
            raise Exception("Missing command")
        if command:
            self._cmd = command

    @property
    def cmd(self):
        """sets base command, immutable"""
        return self._cmd

    @property
    def cmdline(self):
        """ `command` plus any arguments (args)
        validates arguments and generates command line"""
        self._check_mandatory_inputs()
        allargs = self._parse_inputs()
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

        allhelp = "Wraps command **%s**\n\n"%cls._cmd + allhelp

        if returnhelp:
            return allhelp
        else:
            print allhelp


    def _run_interface(self, runtime):
        """Execute command via subprocess

        Parameters
        ----------
        runtime : passed by the run function

        Returns
        -------
        runtime : updated runtime information

        """
        setattr(runtime, 'stdout', None)
        setattr(runtime, 'stderr', None)
        setattr(runtime, 'cmdline', self.cmdline)
        out_environ = {}
        try:
            display_var = config.get('execution', 'display_variable')
            out_environ = {'DISPLAY': display_var}
        except NoOptionError:
            pass
        iflogger.debug(out_environ)
        if isdefined(self.inputs.environ):
            out_environ.update(self.inputs.environ)
        runtime.environ.update(out_environ)
        if not self._exists_in_path(self.cmd.split()[0]):
            raise IOError("%s could not be found on host %s" % (self.cmd.split()[0],
                                                                runtime.hostname))
        runtime = run_command(runtime)
        if runtime.returncode is None or runtime.returncode != 0:
            self.raise_exception(runtime)

        return runtime

    def _exists_in_path(self, cmd):
        '''
        Based on a code snippet from http://orip.org/2009/08/python-checking-if-executable-exists-in.html
        '''

        extensions = os.environ.get("PATHEXT", "").split(os.pathsep)
        for directory in os.environ.get("PATH", "").split(os.pathsep):
            base = os.path.join(directory, cmd)
            options = [base] + [(base + ext) for ext in extensions]
            for filename in options:
                if os.path.exists(filename):
                    return True
        return False

    def _gen_filename(self, name):
        """ Generate filename attributes before running.

        Called when trait.genfile = True and trait is Undefined
        """
        raise NotImplementedError

    def _format_arg(self, name, trait_spec, value):
        """A helper function for _parse_inputs

        Formats a trait containing argstr metadata
        """
        argstr = trait_spec.argstr
        iflogger.debug('%s_%s' %(name, str(value)))
        if trait_spec.is_trait_type(traits.Bool) and "%" not in argstr:
            if value:
                # Boolean options have no format string. Just append options
                # if True.
                return argstr
            else:
                return None
        #traits.Either turns into traits.TraitCompound and does not have any inner_traits
        elif trait_spec.is_trait_type(traits.List) \
        or (trait_spec.is_trait_type(traits.TraitCompound) \
        and isinstance(value, list)):
            # This is a bit simple-minded at present, and should be
            # construed as the default. If more sophisticated behavior
            # is needed, it can be accomplished with metadata (e.g.
            # format string for list member str'ification, specifying
            # the separator, etc.)

            # Depending on whether we stick with traitlets, and whether or
            # not we beef up traitlets.List, we may want to put some
            # type-checking code here as well
            sep = trait_spec.sep
            if sep == None:
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
                if pos >= 0:
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


class StdOutCommandLine(CommandLine):
    input_spec = StdOutCommandLineInputSpec

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        raise NotImplementedError


class MultiPath(traits.List):
    """ Abstract class - shared functionality of input and output MultiPath
    """

    def validate(self, object, name, value):
        if not isdefined(value) or (isinstance(value, list) and len(value) == 0):
            return Undefined
        newvalue = value

        if not isinstance(value, list) \
        or (self.inner_traits() \
            and isinstance(self.inner_traits()[0].trait_type, traits.List) \
            and not isinstance(self.inner_traits()[0].trait_type, InputMultiPath) \
            and isinstance(value, list) \
            and value \
            and not isinstance(value[0], list)):
            newvalue = [value]
        value = super(MultiPath, self).validate(object, name, newvalue)

        if len(value) > 0:
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
    >>> a.foo
    '/software/temp/foo.txt'

    >>> a.foo = ['/software/temp/foo.txt']
    >>> a.foo
    '/software/temp/foo.txt'

    >>> a.foo = ['/software/temp/foo.txt', '/software/temp/goo.txt']
    >>> a.foo
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
