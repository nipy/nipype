# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Package contains interfaces for using existing functionality in other packages

Exaples  FSL, matlab/SPM , afni

Requires Packages to be installed
"""

import os
import subprocess
from copy import deepcopy
from socket import gethostname
from string import Template
from time import time
from warnings import warn


import enthought.traits.api as traits
from enthought.traits.trait_handlers import TraitDictObject, TraitListObject
from nipype.interfaces.traits import Undefined

from nipype.utils.filemanip import md5, hash_infile, FileNotFoundError, \
    hash_timestamp
from nipype.utils.misc import is_container
from enthought.traits.trait_errors import TraitError
from nipype.utils.config import config
from nipype.utils.misc import isdefined
from ConfigParser import NoOptionError

__docformat__ = 'restructuredtext'

# We'll use our versions of File and Directory until error reporting
# will be fixed upstream
#try:
#    class dummy(traits.HasTraits):
#        foo = traits.File
#    dummy().foo = 'bar'
#    from enthought.traits.api import File, Directory
#except:
#    warn('traitsUI unavailable')
from nipype.interfaces.traits import File, Directory

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
        """iterates over bunch attributes as key,value pairs"""
        return self.__dict__.items()

    def iteritems(self):
        """iterates over bunch attributes as key,value pairs"""
        warn('iteritems is deprecated, use items instead')
        return self.items()

    def get(self, *args):
        '''Support dictionary get() functionality
        '''
        return self.__dict__.get(*args)

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
    interface : object
        A copy of the `Interface` that was run to generate this result.
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


    def __init__(self, interface, runtime, outputs=None):
        self.interface = interface
        self.runtime = runtime
        self.outputs = outputs

class BaseTraitedSpec(traits.HasTraits):
    """Provide a few methods necessary to support nipype interface api

    The inputs attribute of interfaces call certain methods that are not
    available in traits.HasTraits. These are provided here.

    new metadata:

    * usedefault : set this to True if the default value of the trait should be
      used. Unless this is set, the attributes are set to traits.Undefined

    new attribute:

    * hashval : returns a tuple containing the state of the trait as a dict and
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
        has_xor = dict(xor=lambda t : t is not None)
        xors = self.trait_names(**has_xor)
        for elem in xors:
            self.on_trait_change(self._xor_warn, elem)
        has_requires = dict(requires=lambda t : t is not None)
        requires = self.trait_names(**has_requires)
        for elem in requires:
            self.on_trait_change(self._requires_warn, elem)

    def _xor_warn(self, obj, name, old, new):
        """ Generates warnings for xor traits
        """
        if isdefined(new):
            trait_spec = self.traits()[name]
            msg = None
            # for each xor, set to default_value
            undefined_traits = {}
            for trait_name in trait_spec.xor:
                if trait_name == name:
                    # skip ourself
                    continue
                if isdefined(getattr(self, trait_name)):
                    undefined_traits[trait_name] = Undefined
                    if not msg:
                        msg = 'Input %s is mutually exclusive with inputs: %s' \
                            % (name, ', '.join(trait_spec.xor))
                    msg += '\nResetting %s to %s' % (trait_name, Undefined)
            if msg:
                warn(msg)
            self.trait_set(trait_change_notify=False, **undefined_traits)

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
                hashlist = self._hash_infile({'infiles':afile}, 'infiles')
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

    def _clean_container(self, object, undefinedval=None):
        """Convert a traited obejct into a pure python representation.
        """
        if isinstance(object, TraitDictObject) or isinstance(object, dict):
            out = {}
            for key, val in object.items():
                if isdefined(val):
                    out[key] = self._clean_container(val, undefinedval)
                else:
                    out[key] = undefinedval
        elif isinstance(object, TraitListObject) or isinstance(object, list) or \
                isinstance(object, tuple):
            out = []
            for val in object:
                if isdefined(val):
                    out.append(self._clean_container(val, undefinedval))
                else:
                    out.append(undefinedval)
            if isinstance(object, tuple):
                out = tuple(out)
        else:
            if isdefined(object):
                out = object
            else:
                out = undefinedval
        return out

    #@traits.cached_property
    @property
    def hashval(self):
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
        dict_withhash = self._get_sorteddict(self.get(),True)
        dict_nofilename = self._get_sorteddict(self.get())
        return (dict_withhash, md5(str(dict_nofilename)).hexdigest())

    def _get_sorteddict(self, object, dictwithhash=False):
        if isinstance(object, dict):
            out = {}
            for key, val in sorted(object.items()):
                if isdefined(val):
                    out[key] = self._get_sorteddict(val, dictwithhash)
        elif isinstance(object, (list,tuple)):
            out = []
            for val in object:
                if isdefined(val):
                    out.append(self._get_sorteddict(val, dictwithhash))
            if isinstance(object, tuple):
                out = tuple(out)
        else:
            if isdefined(object):
                if isinstance(object, str) and os.path.isfile(object):
                    if config.get('execution', 'hash_method').lower() == 'timestamp':
                        hash = hash_timestamp(object)
                    elif config.get('execution', 'hash_method').lower() == 'content':
                        hash = hash_infile(object)
                    else:
                        raise Exception("Unknown hash method: %s" % config.get('execution', 'hash_method'))
                    if dictwithhash:
                        out = (object, hash)
                    else:
                        out = hash
                elif isinstance(object, float):
                    out = '%.10f'%object
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
            value = getattr(self, key)
        # clone once
        dup = self.clone_traits(memo=memo)
        for key in self.copyable_trait_names():
            try:
                value = getattr(dup, key)
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

    input_spec = None # A traited input specification
    output_spec = None # A traited output specification
    can_resume = False # defines if the interface can reuse partial results after interruption

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

    def aggregate_outputs(self):
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

    def __init__(self, **inputs):
        if not self.input_spec:
            raise Exception('No input_spec in class: %s' % \
                                self.__class__.__name__)
        self.inputs = self.input_spec(**inputs)

    @classmethod
    def help(cls):
        """ Prints class help
        """
        cls._inputs_help()
        print ''
        cls._outputs_help()

    @classmethod
    def _inputs_help(cls):
        """ Prints description for input parameters
        """
        helpstr = ['Inputs', '------']
        opthelpstr = None
        manhelpstr = None
        if cls.input_spec is None:
            helpstr += ['None']
            print '\n'.join(helpstr)
            return
        xor_done = []
        for name, spec in sorted(cls.input_spec().traits(mandatory=True).items()):
            desc = spec.desc
            xor = spec.xor
            requires = spec.requires
            if not manhelpstr:
                manhelpstr = ['', 'Mandatory:']
            manhelpstr += [' %s: %s' % (name, desc)]
            if xor: # and name not in xor_done:
                xor_done.extend(xor)
                manhelpstr += ['  mutually exclusive: %s' % ', '.join(xor)]
            if requires: # and name not in xor_done:
                others = [field for field in requires if field != name]
                manhelpstr += ['  requires: %s' % ', '.join(others)]
        for name, spec in sorted(cls.input_spec().traits(mandatory=None,
                                                         transient=None).items()):
            desc = spec.desc
            xor = spec.xor
            requires = spec.requires
            if not opthelpstr:
                opthelpstr = ['', 'Optional:']
            opthelpstr += [' %s: %s' % (name, desc)]
            if spec.usedefault:
                opthelpstr[-1] += ' (default=%s)' % spec.default
            if xor: # and name not in xor_done:
                xor_done.extend(xor)
                opthelpstr += ['  mutually exclusive: %s' % ', '.join(xor)]
            if requires: # and name not in xor_done:
                others = [field for field in requires if field != name]
                opthelpstr += ['  requires: %s' % ', '.join(others)]
        if manhelpstr:
            helpstr += manhelpstr
        if opthelpstr:
            helpstr += opthelpstr
        print '\n'.join(helpstr)

    @classmethod
    def _outputs_help(cls):
        """ Prints description for output parameters
        """
        helpstr = ['Outputs', '-------']
        if cls.output_spec:
            for name, spec in sorted(cls.output_spec().traits(transient=None).items()):
                helpstr += ['%s: %s' % (name, spec.desc)]
        else:
            helpstr += ['None']
        print '\n'.join(helpstr)

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
        metadata = dict(copyfile=lambda t : t is not None)
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
        interface = deepcopy(self)
        # initialize provenance tracking
        env = deepcopy(os.environ.data)
        runtime = Bunch(cwd=os.getcwd(),
                        returncode=None,
                        duration=None,
                        environ=env,
                        hostname=gethostname())
        t = time()
        runtime = self._run_interface(runtime)
        runtime.duration = time() - t
        results = InterfaceResult(interface, runtime)
        if results.runtime.returncode is None:
            raise Exception('Returncode from an interface cannot be None')
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs(results.runtime)
        return results

    def _list_outputs(self):
        """ List the expected outputs
        """
        if self.output_spec:
            raise NotImplementedError
        else:
            return None

    def aggregate_outputs(self, runtime=None):
        """ Collate expected outputs and check for existence
        """
        predicted_outputs = self._list_outputs()
        outputs = self._outputs()
        if predicted_outputs:
            for key, val in predicted_outputs.items():
                try:
                    setattr(outputs, key, val)
                    value = getattr(outputs, key)
                except TraitError, error:
                    if hasattr(error, 'info') and error.info.startswith("an existing"):
                        msg = "File/Directory '%s' not found for %s output '%s'." \
                            % (val, self.__class__.__name__, key)
                        raise FileNotFoundError(msg)
                    else:
                        raise error
        return outputs


class CommandLineInputSpec(TraitedSpec):
    args = traits.Str(argstr='%s', desc='Additional parameters to the command')
    environ = traits.DictStrStr(desc='Environment variables', usedefault=True)

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
    {'args': '-al', 'environ': {'DISPLAY': ':1'}}

    >>> cli.help()
    Inputs
    ------
    <BLANKLINE>
    Optional:
     args: Additional parameters to the command
     environ: Environment variables (default={})
    <BLANKLINE>
    Outputs
    -------
    None


    >>> cli.inputs.hashval
    ({'args': '-al', 'environ': {'DISPLAY': ':1'}}, '998f3bdb3d4ed9b5177e34387117cb0d')

    """

    input_spec = CommandLineInputSpec

    def __init__(self, command=None, **inputs):
        super(CommandLine, self).__init__(**inputs)
        self._environ = None
        if not hasattr(self, '_cmd'):
            self._cmd = None
        if self.cmd is None and command is None:
            raise Exception("Missing command")
        if command:
            self._cmd = command
        try:
            display_var = config.get('execution', 'display_variable')
            self.inputs.environ['DISPLAY'] = display_var
        except NoOptionError:
            pass

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
        runtime.environ.update(self.inputs.environ)
        if not self._exists_in_path(self.cmd.split()[0]):
            raise IOError("%s could not be found on host %s"%(self.cmd.split()[0],
                                                         runtime.hostname))
        proc = subprocess.Popen(runtime.cmdline,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=True,
                                 cwd=runtime.cwd,
                                 env=runtime.environ)
        runtime.stdout, runtime.stderr = proc.communicate()
        runtime.returncode = proc.returncode
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
        if trait_spec.is_trait_type(traits.Bool):
            if value:
                # Boolean options have no format string. Just append options
                # if True.
                return argstr
            else:
                # If we end up here we're trying to add a Boolean to
                # the arg string but whose value is False.  This
                # should not happen, something went wrong upstream.
                # Raise an error.
                msg = "Object '%s' attempting to format argument " \
                    "string for attr '%s' with value '%s'."  \
                    % (self, trait_spec.name, value)
                raise ValueError(msg)
        elif trait_spec.is_trait_type(traits.List):
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
        metadata = dict(argstr=lambda t : t is not None)
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


class MultiPath(traits.List):
    """ Abstract class - shared functionality of input and output MultiPath
    """

    def validate(self, object, name, value):
        if not isdefined(value) or (isinstance(value, list) and len(value) == 0):
            return Undefined
        newvalue = value
        if not isinstance(value, list):
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

