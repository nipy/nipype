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
from enthought.traits.api import Undefined
from enthought.traits.trait_base import _Undefined

from nipype.utils.filemanip import md5, hash_infile, FileNotFoundError
from nipype.utils.misc import is_container

 
__docformat__ = 'restructuredtext'

class BaseFile ( traits.BaseStr ):
    """ Defines a trait whose value must be the name of a file.
    """
	
    # A description of the type of value this trait accepts:
    info_text = 'a file name'
	
    def __init__ ( self, value = '', filter = None, auto_set = False,
                   entries = 0, exists = False, **metadata ):
        """ Creates a File trait.
	
        Parameters
        ----------
        value : string
        The default value for the trait
        filter : string
        A wildcard string to filter filenames in the file dialog box used by
        the attribute trait editor.
        auto_set : boolean
        Indicates whether the file editor updates the trait value after
        every key stroke.
        exists : boolean
        Indicates whether the trait value must be an existing file or
        not.
	
        Default Value
        -------------
        *value* or ''
        """
        self.filter = filter
        self.auto_set = auto_set
        self.entries = entries
        self.exists = exists
	
        super( BaseFile, self ).__init__( value, **metadata )
	
    def validate ( self, object, name, value ):
        """ Validates that a specified value is valid for this trait.
        
        Note: The 'fast validator' version performs this check in C.
        """
        if not self.exists:
            return super( BaseFile, self ).validate( object, name, value )
        
        if os.path.isfile( value ):
            return value
        else:
            raise FileNotFoundError
	
class File ( BaseFile ):
    """ Defines a trait whose value must be the name of a file using a C-level
    fast validator.
    """
    
    def __init__ ( self, value = '', filter = None, auto_set = False,
                   entries = 0, exists = False, **metadata ):
        """ Creates a File trait.
	
        Parameters
        ----------
        value : string
        The default value for the trait
        filter : string
        A wildcard string to filter filenames in the file dialog box used by
        the attribute trait editor.
        auto_set : boolean
        Indicates whether the file editor updates the trait value after
        every key stroke.
        exists : boolean
        Indicates whether the trait value must be an existing file or
        not.
	
        Default Value
        -------------
        *value* or ''
        """
        if not exists:
            # Define the C-level fast validator to use:
            fast_validate = ( 11, basestring )
	
        super( File, self ).__init__( value, filter, auto_set, entries, exists,
                                      **metadata )
	

class BaseDirectory ( traits.BaseStr ):
    """ Defines a trait whose value must be the name of a directory.
    """
    
    # A description of the type of value this trait accepts:
    info_text = 'a directory name'
    
    def __init__ ( self, value = '', auto_set = False, entries = 0,
                   exists = False, **metadata ):
        """ Creates a BaseDirectory trait.
	
        Parameters
        ----------
        value : string
            The default value for the trait
        auto_set : boolean
            Indicates whether the directory editor updates the trait value
            after every key stroke.
        exists : boolean
            Indicates whether the trait value must be an existing directory or
            not.

        Default Value
        -------------
        *value* or ''
        """
        self.entries = entries
        self.auto_set = auto_set
        self.exists = exists

        super( BaseDirectory, self ).__init__( value, **metadata )

    def validate ( self, object, name, value ):
        """ Validates that a specified value is valid for this trait.

            Note: The 'fast validator' version performs this check in C.
        """
        if not self.exists:
            return super( BaseDirectory, self ).validate( object, name, value )

        if os.path.isdir( value ):
            return value

        self.error( object, name, value )

    def create_editor(self):
        from .ui.editors.directory_editor import DirectoryEditor
        editor = DirectoryEditor(
            auto_set = self.auto_set,
            entries = self.entries,
        )
        return editor


class Directory ( BaseDirectory ):
    """ Defines a trait whose value must be the name of a directory using a
        C-level fast validator.
    """

    def __init__ ( self, value = '', auto_set = False, entries = 0,
                         exists = False, **metadata ):
        """ Creates a Directory trait.

        Parameters
        ----------
        value : string
            The default value for the trait
        auto_set : boolean
            Indicates whether the directory editor updates the trait value
            after every key stroke.
        exists : boolean
            Indicates whether the trait value must be an existing directory or
            not.

        Default Value
        -------------
        *value* or ''
        """
        # Define the C-level fast validator to use if the directory existence
        # test is not required:
        if not exists:
            self.fast_validate = ( 11, basestring )

        super( Directory, self ).__init__( value, auto_set, entries, exists,
                                           **metadata )

    

def isdefined(object):
    return not isinstance(object, _Undefined)

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

    def _hash_infile(self,adict, key):
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
            file_list.append((afile,md5hex ))
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
                if isinstance(val,dict):
                    # XXX - SG should traverse dicts, but ignoring for now
                    item = None
                else:
                    if len(val) == 0:
                        raise AttributeError('%s attribute is empty'%key)
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

    def _get_hashval(self):
        return self._get_bunch_hash()
            
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
        as the `inputs` to another node in when interfaces are used in
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

    # We could actually call aggregate_outputs in here...
    def __init__(self, interface, runtime, outputs=None):
        self.interface = interface
        self.runtime = runtime
        self.outputs = outputs

#
# Original base classes
#
class Interface(object):
    """This is the template for Interface objects.

    It provides no functionality.  It defines the necessary attributes
    and methods all Interface objects should have.

    Everything in inputs should also be a possible (explicit?) argument to
    .__init__()
    """

    def __init__(self, *args, **inputs):
        """Initialize command with given args and inputs."""
        raise NotImplementedError

    def run(self, cwd=None):
        """Execute the command."""
        raise NotImplementedError

    def _runner(self):
        """Performs the call to execute the command."""
        raise NotImplementedError

    def _populate_inputs(self):
        """Initialize the inputs Bunch attributes."""
        raise NotImplementedError

    def aggregate_outputs(self):
        """Called to populate outputs
        
        Currently, search for discussion of this on private e-mails between Dav
        and Satra (ugh!).  This needs to get in here!"""
        raise NotImplementedError


class CommandLine(Interface):
    """Encapsulate a command-line function along with the arguments and options.

    Provides a convenient mechanism to build a command line with it's
    arguments and options incrementally.  A `CommandLine` object can
    be reused, and it's arguments and options updated.  The
    `CommandLine` class is the base class for all nipype.interfaces
    classes.

    Parameters
    ----------
    args : string
        A string representing the command and it's arguments.
    inputs : mapping
        key value pairs that populate a Bunch()


    Attributes
    ----------
    args : list
        The command, it's arguments and options store in a list of strings.
        ['ls', '-al']
        These are added to command line string first
    inputs : Bunch of key,value inputs
        The only valid key for CommandLine is args
        Other keys are not recognized in CommandLine, and
        require parsing in subclasses
        if there are args=['ls','-al'] 
        These are added to command line string before simple positional args
    Returns
    -------
    
    cmd : CommandLine
        A `CommandLine` object that can be run and/or updated.

    Examples
    --------
    >>> from nipype.interfaces.base import CommandLine
    >>> cmd = CommandLine('echo')
    >>> cmd.cmdline
    'echo'
    >>> res = cmd.run(None, 'foo')
    >>> print res.runtime.stdout
    foo
    <BLANKLINE>

    You could pass arguments in the following ways and all result in
    the same command.
    >>> lscmd = CommandLine('ls', '-l', '-t')
    >>> lscmd.cmdline
    'ls -l -t'
    >>> lscmd = CommandLine('ls -l -t') 
    >>> lscmd.cmdline
    'ls -l -t'
    >>> lscmd = CommandLine(args=['ls', '-l', '-t'])
    >>> lscmd.cmdline
    'ls -l -t'

    Notes
    -----
    
    When subclassing CommandLine, you will generally override at least:
        _compile_command, and run

    Also quite possibly __init__ but generally not  _runner

    """

    def __init__(self, *args, **inputs):
        self._populate_inputs()
        self._update(*args, **inputs)
        self._environ = {}

    def _update(self, *args, **inputs):
        """Update the `self.inputs` Bunch.

        Updates the Bunch dictionary `self.inputs` with values from
        `args` and `inputs`.  Positional arguments in `args` will be
        appended to self.inputs.args if it exists.  Keyword arguments
        in `inputs` will be added to the `self.inputs` dictionary.  As
        with any dictionary, if the key already exists in
        `self.inputs` the new value will overwrite the previous
        values.  For example, if inputs['args'] is passed it, it will
        overwrite the previous value of `self.inputs.args`.

        Parameters
        ----------
        args : list
            List of parameters to be assigned to self.inputs.args
        inputs : dict
            Dictionary whose items are used to update the self.inputs
            dictionary.

        Examples
        --------
        >>> from nipype.interfaces.base import CommandLine
        >>> cmd = CommandLine('echo')
        >>> cmd._update('foo', 'bar', new_input_var='whatever')
        >>> cmd.inputs
        Bunch(args=['echo', 'foo', 'bar'], new_input_var='whatever')

        """

        try:
            # if inputs['args'] exists and is splittable (thus, not a
            # list), split it.
            # So if inputs['args'] == 'foo bar
            # then after this block:
            # inputs['args'] == ['foo', 'bar']
            if hasattr(inputs['args'], 'split'):
                inputs['args']  = inputs['args'].split()
        except KeyError:
            pass

        self.inputs.update(inputs)

        if args:
            # Note: .get() returns None if key doesn't exist
            if self.inputs.get('args') is not None:
                self.inputs.args.extend(list(args))
            else:
                self.inputs.args = list(args)

    def run(self, cwd=None, *args, **inputs):
        """Execute the command.
        
        Parameters
        ----------
        cwd : path
            Where do we effectively execute this command? (default: os.getcwd())
        args : list
            additional arguments that will be appended to inputs.args
        inputs : mapping
            additional key,value pairs will update inputs
            it will overwrite existing key, value pairs
           
        Returns
        -------
        results : InterfaceResult Object
            A `Bunch` object with a copy of self in `interface`
        
        """
        self._update(*args, **inputs) 
            
        return self._runner(cwd=cwd)

    def _populate_inputs(self):
        self.inputs = Bunch(args=None)

    @property
    def cmdline(self):
        # This handles args like ['bet', '-f 0.2'] without crashing
        return ' '.join(self.inputs.args)

    def _runner(self, cwd=None):
        """Run the command using subprocess.Popen.

        Currently, shell is set to True, i.e., a shell parses the command line
        
        Arguments
        ---------
        cwd : str
            default os.getcwd()
        """
        if cwd is None:
            cwd = os.getcwd()
        runtime = Bunch(cmdline=self.cmdline, cwd=cwd,
                        stdout = None, stderr = None,
                        returncode = None, duration = None,
                        environ=deepcopy(os.environ.data),
                        hostname = gethostname())
        
        t = time()
        if hasattr(self, '_environ') and self._environ != None:
            env = deepcopy(os.environ.data)
            env.update(self._environ)
            runtime.environ = env
            proc  = subprocess.Popen(runtime.cmdline,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     shell=True,
                                     cwd=cwd,
                                     env=env)
        else:
            proc  = subprocess.Popen(runtime.cmdline,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     shell=True,
                                     cwd=cwd)

        runtime.stdout, runtime.stderr = proc.communicate()
        runtime.duration = time()-t
        runtime.returncode = proc.returncode

        return InterfaceResult(deepcopy(self), runtime)

    def get_input_info(self):
        """ Provides information about file inputs to copy or link to cwd.
        
        Notes
        -----
        see `spm.Realign.get_input_info`
            
        """
        return []
    
    
class OptMapCommand(CommandLine):
    '''Common FreeSurfer and FSL commands support'''
    opt_map = {}

    @property
    def cmdline(self):
        """validates fsl options and generates command line argument"""
        allargs = self._parse_inputs()
        allargs.insert(0, self.cmd)
        return ' '.join(allargs)

    def run(self):
        """Execute the command.

        Returns
        -------
        results : InterfaceResult
            An :class:`nipype.interfaces.base.InterfaceResult` object
            with a copy of self in `interface`

        """
        results = self._runner(cwd=os.getcwd())
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs()

        return results

    def _parse_inputs(self, skip=()):
        """Parse all inputs and format options using the opt_map format string.

        Any inputs that are assigned (that are not None) are formatted
        to be added to the command line.

        Parameters
        ----------
        skip : tuple or list
            Inputs to skip in the parsing.  This is for inputs that
            require special handling, for example input files that
            often must be at the end of the command line.  Inputs that
            require special handling like this should be handled in a
            _parse_inputs method in the subclass.

        Returns
        -------
        allargs : list
            A list of all inputs formatted for the command line.

        """
        allargs = []
        inputs = sorted((k, v) for k, v in self.inputs.items()
                            if v is not None and k not in skip)
        for opt, value in inputs:
            if opt == 'args':
                # XXX Where is this used?  Is self.inputs.args still
                # used?  Or is it leftover from the original design of
                # base.CommandLine?
                allargs.extend(value)
                continue
            try:
                argstr = self.opt_map[opt]
                if is_container(argstr):
                    # The value in opt_map may be a tuple whose first
                    # element is the format string and second element
                    # a one-line docstring.  This docstring will
                    # become the desc field in the traited version of
                    # the code.
                    argstr = argstr[0]
                if argstr.find('%') == -1:
                    # Boolean options have no format string.  Just
                    # append options if True.
                    if value is True:
                        allargs.append(argstr)
                    elif value is not False:
                        raise TypeError('Boolean option %s set to %s' %
                                         (opt, str(value)) )
                elif isinstance(value, list) and self.__class__.__name__ == 'Fnirt':
                    # XXX Hack to deal with special case where some
                    # parameters to Fnirt can have a variable number
                    # of arguments.  Splitting the argument string,
                    # like '--infwhm=%d', then add as many format
                    # strings as there are values to the right-hand
                    # side.
                    argparts = argstr.split('=')
                    allargs.append(argparts[0] + '=' +
                                   ','.join([argparts[1] % y for y in value]))
                elif isinstance(value, list):
                    allargs.append(argstr % tuple(value))
                else:
                    # Append options using format string.
                    allargs.append(argstr % value)
            except TypeError, err:
                msg = 'Error when parsing option %s in class %s.\n%s' % \
                    (opt, self.__class__.__name__, err.message)
                warn(msg)
            except KeyError:
                warn("Option '%s' is not supported!" % (opt))
                raise

        return allargs

    def _populate_inputs(self):
        self.inputs = Bunch((k,None) for k in self.opt_map.keys())

    def inputs_help(self):
        """Print command line documentation for the command."""
        from nipype.utils.docparse import get_doc
        print get_doc(self.cmd, self.opt_map, '-h')

    def outputs_help(self):
        """Print the help for outputs."""
        # XXX This function does the same for FSL and SPM, consider
        # moving to a top-level class.
        print self.outputs.__doc__

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        raise NotImplementedError(
                'Subclasses of OptMapCommand must implement aggregate_outputs')

    def outputs(self):
        """Virtual function"""
        raise NotImplementedError(
                'Subclasses of OptMapCommand must implement outputs')

#####################################################################
#
# New base classes
#
#####################################################################

class TraitedSpec(traits.HasStrictTraits):
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
        super(TraitedSpec, self).__init__(**kwargs)
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
        return '\n'.join(outstr)

    def _generate_handlers(self):
        # Find all traits with the 'xor' metadata and attach an event
        # handler to them.
        def has_xor(item):
            if is_container(item):
                return item
        xors = self.trait_names(xor=has_xor)
        for elem in xors:
            self.on_trait_change(self._xor_warn, elem)

    def _xor_warn(self, obj, name, old, new):
        trait_spec = self.traits()[name]
        if new:
            # for each xor, set to default_value
            for trait_name in trait_spec.xor:
                if trait_name == name:
                    # skip ourself
                    continue
                value = getattr(self, trait_name)
                if value == new:
                    tspec = self.traits()[trait_name]
                    setattr(self, trait_name, Undefined)
                    msg = 'Input %s is mutually exclusive with inputs:  %s' \
                        % (name, ', '.join(trait_spec.xor))
                    msg += '\nResetting %s to %s' % (trait_name,
                                                     Undefined)
                    warn(msg)

    def _hash_infile(self, adict, key):
        # Inject file hashes into adict[key]
        stuff = adict[key]
        if not is_container(stuff):
            stuff = [stuff]
        file_list = []
        for afile in stuff:
            file_list.append((afile, hash_infile(afile) ))
        return file_list

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
        dict_withhash = self.get()
        dict_nofilename = self.get()
        for key, spec in self.items():
            #do not hash values which are not set
            if not isdefined(dict_withhash[key]):
                del dict_withhash[key]
                del dict_nofilename[key]
                continue
            innertype = []
            if spec.inner_traits:
                innertype = [1 for inner in spec.inner_traits \
                                 if inner.is_trait_type(File)]
            if spec.is_trait_type(File) or innertype:
                if dict_withhash[key]:
                    dict_withhash[key] = self._hash_infile(dict_withhash, key)
                    dict_nofilename[key] = [val[1] for val in dict_withhash[key]]
        # Sort the items of the dictionary, before hashing the string
        # representation so we get a predictable order of the
        # dictionary.
        sorted_dict = str(sorted(dict_nofilename.items()))
        return (dict_withhash, md5(sorted_dict).hexdigest())
    
    def _get_hashval(self):
        return self.hashval

class NEW_Interface(object):
    """This is an abstract defintion for Interface objects.

    It provides no functionality.  It defines the necessary attributes
    and methods all Interface objects should have.

    """

    input_spec = None # A traited input specification
    output_spec = None # A traited output specification

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

class BaseInterfaceInputSpec(TraitedSpec):
    environ = traits.DictStrStr(desc='Environment variables', usedefault=True)

class NEW_BaseInterface(NEW_Interface):
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
        helpstr = ['Inputs','------']
        opthelpstr = None
        manhelpstr = None
        if cls.input_spec is None:
            helpstr += ['None']
            print '\n'.join(helpstr)
            return
        for name, spec in sorted(cls.input_spec().traits(mandatory=True).items()):
            desc = spec.desc
            if not manhelpstr:
                manhelpstr = ['','Mandatory:']
            manhelpstr += [' %s: %s' % (name, desc)]
        for name, spec in sorted(cls.input_spec().traits(mandatory=None,
                                                         transient=None).items()):
            desc = spec.desc
            if not opthelpstr:
                opthelpstr = ['','Optional:']
            opthelpstr += [' %s: %s' % (name, desc)]
            if spec.usedefault:
                opthelpstr[-1] += ' (default=%s)' % spec.default
        if manhelpstr:
            helpstr += manhelpstr
        if opthelpstr:
            helpstr += opthelpstr
        print '\n'.join(helpstr)

    @classmethod
    def _outputs_help(cls):
        """ Prints description for output parameters
        """
        helpstr = ['Outputs','-------']
        if cls.output_spec:
            for name, spec in sorted(cls.output_spec().traits(transient=None).items()):
                helpstr += ['%s: %s' % (name, spec.desc)]
        else:
            helpstr += ['None']
        print '\n'.join(helpstr)

    @classmethod
    def _outputs(cls):
        """ Returns a bunch containing output fields for the class
        """
        outputs = None
        if cls.output_spec:
            outputs = cls.output_spec()
        return outputs

    @classmethod
    def _get_filecopy_info(cls):
        """ Provides information about file inputs to copy or link to cwd.
            Necessary for pipeline operation
        """
        info = []
        if cls.input_spec is None:
            return info
        metadata = dict(copyfile = lambda t : t is not None)
        for name, spec in sorted(cls.input_spec().traits(**metadata).items()):
            info.append(dict(key=name,
                             copy=spec.copyfile))
        return info
    
    def _check_mandatory_inputs(self):
        """ Raises an exception if a mandatory input is Undefined
        """
        for name, value in self.inputs.trait_get(mandatory=True).items():
            if not isdefined(value):
                msg = "%s requires a value for input '%s'" % \
                    (self.__class__.__name__, name)
                self.help()
                raise ValueError(msg)

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
        # initialize provenance tracking
        env = deepcopy(os.environ.data)
        env.update(self.inputs.environ)
        runtime = Bunch(cwd=os.getcwd(),
                        returncode = None,
                        duration = None,
                        environ=env,
                        hostname = gethostname())
        t = time()
        runtime = self._run_interface(runtime)
        runtime.duration = time()-t
        results = InterfaceResult(deepcopy(self), runtime)
        if results.runtime.returncode is None:
            raise Exception('Returncode from an interface cannot be None')
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs()
        return results
    
    def _list_outputs(self):
        """ List the expected outputs
        """
        if self.output_spec:
            raise NotImplementedError
        else:
            return None
    
    def aggregate_outputs(self):
        """ Collate expected outputs and check for existence
        """
        outputs = self._outputs()
        expected_outputs = self._list_outputs()
        if expected_outputs:
            outputs.set(**expected_outputs)
        return outputs


class CommandLineInputSpec(BaseInterfaceInputSpec):
    args = traits.Str(argstr='%s', desc='Additional parameters to the command')

class NEW_CommandLine(NEW_BaseInterface):
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
        
    >>> from nipype.interfaces.base import NEW_CommandLine
    >>> cli = NEW_CommandLine(command='ls')
    >>> cli.inputs.args = '-al'
    >>> cli.cmdline
    'ls -al'
    
    >>> cli.inputs.trait_get()
    {'args': '-al', 'environ': {}}

    >>> cli.inputs.hashval
    ({'args': '-al', 'environ': {}}, 'c005b3eb45d97fd5733997ae75689457')

    """

    input_spec = CommandLineInputSpec
        
    def __init__(self, command=None, **inputs):
        super(NEW_CommandLine, self).__init__(**inputs)
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
        proc  = subprocess.Popen(runtime.cmdline,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=True,
                                 cwd=runtime.cwd,
                                 env=runtime.environ)
        runtime.stdout, runtime.stderr = proc.communicate()
        runtime.returncode = proc.returncode
        return runtime

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
            if argstr.endswith('...'):
                # repeatable option
                # --id %d... will expand to
                # --id 1 --id 2 --id 3 etc.,.
                argstr = argstr.replace('...','')
                return ' '.join([argstr % elt for elt in value])
            else:
                return argstr % ' '.join(str(elt) for elt in value)
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
        metadata=dict(argstr=lambda t : t is not None)
        for name, spec in self.inputs.traits(**metadata).items():
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
    """ Implements a user friendly traits that accepts one or more
    paths to files or directories

    XXX This should only be used as a final resort. We should stick to
    established Traits to the extent possible.

    XXX This needs to be vetted by somebody who understands traits

    >>> from nipype.interfaces.base import MultiPath
    >>> class A(traits.HasTraits):
    ...     foo = MultiPath(File(exists=False))
    >>> a = A()
    >>> a
    []
    
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
    info_text = 'a list of paths'
    
    def __init__(self, trait  = None, value = None, **metadata):
        if trait:
            self.info_text = 'a list of %s' % trait.info()
        super(MultiPath, self).__init__(trait, value,
                                        **metadata)

    def get(self, object, name):
        value = self.get_value(object, name)
        if value:
            if len(value)==1:
                return value[0]
        return value

    def set(self, object, name, value):
        self.set_value(object, name, value)

    def validate(self, object, name, value):
        newvalue = value
        if isinstance(value, str):
            newvalue = [value]
        if not isdefined(value):
            return value
        else:
            return super(MultiPath, self).validate(object, name, newvalue)
