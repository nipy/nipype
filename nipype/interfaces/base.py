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

# We are shooting for interoperability for now - Traits or Traitlets
import nipype.externals.traitlets as traits
# import enthought.traits.api as traits

from nipype.utils.filemanip import md5
from nipype.utils.misc import is_container

 
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

#
# New base classes
#
class NEW_Interface(object):
    """This is the template for Interface objects.

    It provides no functionality.  It defines the necessary attributes
    and methods all Interface objects should have.

    Everything in inputs should also be a possible (explicit?) argument to
    .__init__()
    """

    in_spec = None
    out_spec = None

    def __init__(self, **inputs):
        """Initialize command with given args and inputs."""
        raise NotImplementedError

    def run(self, cwd=None):
        """Execute the command."""
        raise NotImplementedError

    def aggregate_outputs(self):
        """Called to populate outputs"""
        raise NotImplementedError

    def get_input_info(self):
        """ Provides information about file inputs to copy or link to cwd.
            Necessary for pipeline operation
        """
        raise NotImplementedError

class NEW_BaseInterface(NEW_Interface):

    def __init__(self, **inputs):
        self.inputs = self.in_spec(**inputs)

    @classmethod
    def help(cls):
        """ Prints class help
        """
        # XXX Creates new object!  Need to make sure this is cheap.
        obj = cls()
        obj._inputs_help()
        print ''
        obj._outputs_help()

    def _inputs_help(self):
        """ Prints the help of inputs
        """
        helpstr = ['Inputs','------']
        opthelpstr = None
        manhelpstr = None
        for name, trait_spec in self.inputs.items():
            desc = trait_spec.get_metadata('desc')
            if trait_spec.get_metadata('mandatory'):
                if not manhelpstr:
                    manhelpstr = ['','Mandatory:']
                manhelpstr += [' %s: %s' % (name, desc)]
            else:
                if not opthelpstr:
                    opthelpstr = ['','Optional:']
                # We do not what the "trait default" which is the
                # default value for that type of trait and what is
                # returned from get_metadata('default').  We want the
                # default value from the package, which we set in the
                # in_spec class definition.
                default = trait_spec.get_default_value()
                if default not in [None, '', []]:
                    opthelpstr += [' %s: %s (default=%s)' % (name,
                                                             desc,
                                                             default)]
                else:
                    opthelpstr += [' %s: %s' % (name, desc)]
        if manhelpstr:
            helpstr += manhelpstr
        if opthelpstr:
            helpstr += opthelpstr
        print '\n'.join(helpstr)

    def _outputs_help(self):
        """ Prints the help of outputs
        """
        helpstr = ['Outputs','-------']
        out_spec = self.out_spec()
        for name, trait_spec in sorted(out_spec.traits().items()):
            desc = trait_spec.get_metadata('desc')
            helpstr += ['%s: %s' % (name, desc)]
        print '\n'.join(helpstr)

    def _outputs(self):
        """ Returns a bunch containing output fields for the class
        """
        outputs = Bunch()
        out_spec = self.out_spec()
        for name, trait_spec in sorted(out_spec.traits().items()):
            setattr(outputs, name, None)
        return outputs

    def _check_mandatory_inputs(self):
        for name, trait_spec in self.inputs.items():
            if trait_spec.get_metadata('mandatory'):
                # mandatory parameters must be set and therefore
                # should not have the default value.  XXX It seems
                # possible that a default value would be a valid
                # 'value'?  Currently most of the required params are
                # filenames where the default_value is the empty
                # string, so this may not be an issue.
                value = getattr(self.inputs, name)
                if value == trait_spec.get_default_value():
                    msg = "%s requires a value for input '%s'" % \
                        (self.__class__.__name__, name)
                    raise ValueError(msg)

    def run(self):
        """Execute this module.
        """
        # XXX What is the purpose of this method here?
        self._check_mandatory_inputs()
        runtime = Bunch(returncode=0,
                        stdout=None,
                        stderr=None)
        outputs = self.aggregate_outputs()
        return InterfaceResult(deepcopy(self), runtime, outputs = outputs)

    def get_input_info(self):
        """ Provides information about file inputs to copy or link to cwd.
            Necessary for pipeline operation
        """
        return []

class NEW_CommandLine(NEW_BaseInterface):
    def __init__(self, command=None, **inputs):
        super(NEW_CommandLine, self).__init__(**inputs)
        self._environ = {}
        self._cmd = command # XXX Currently I don't see any code using
                            # this feature.  Each class overrides the
                            # cmd property.  Delete?

    @property
    def cmd(self):
        """sets base command, immutable"""
        return self._cmd

    @property
    def cmdline(self):
        """validates fsl options and generates command line argument"""
        allargs = self._parse_inputs()
        allargs.insert(0, self.cmd)
        return ' '.join(allargs)

    def run(self, cwd=None, **inputs):
        """Execute the command.

        Parameters
        ----------
        cwd : path
            Where do we effectively execute this command? (default: os.getcwd())
        inputs : mapping
            additional key,value pairs will update inputs
            it will overwrite existing key, value pairs

        Returns
        -------
        results : InterfaceResult Object
            A `Bunch` object with a copy of self in `interface`

        """
        #self.inputs.update(inputs)
        for key, val in inputs.items():
            setattr(self.inputs, key, val)

        self._check_mandatory_inputs()
        if cwd is None:
            cwd = os.getcwd()
        # initialize provenance tracking
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

        results = InterfaceResult(deepcopy(self), runtime)
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs()
        return results

    def _gen_outfiles(self, check = False):
        return self._outputs()

    def aggregate_outputs(self):
        return self._gen_outfiles(check = True)

    def _convert_inputs(self, opt, val):
        """Convert input to appropriate format. Override this function for
        class specific modifications that do not fall into general format:

        For example fnirt should implement this:

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

        """
        return val

    def _format_arg(self, trait_spec, value):
        '''A helper function for _parse_inputs'''
        argstr = trait_spec.get_metadata('argstr')
        if isinstance(trait_spec, traits.Bool):
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
        elif isinstance(trait_spec, traits.List):
            # This is a bit simple-minded at present, and should be
            # construed as the default. If more sophisticated behavior
            # is needed, it can be accomplished with metadata (e.g.
            # format string for list member str'ification, specifying
            # the separator, etc.)

            # Depending on whether we stick with traitlets, and whether or
            # not we beef up traitlets.List, we may want to put some
            # type-checking code here as well

            return argstr % ' '.join(str(elt) for elt in value)
        else:
            # Append options using format string.
            return argstr % value

    def _parse_inputs(self):
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
        for name, trait_spec in self.inputs.items():
            value = getattr(self.inputs, name)
            if value == trait_spec.get_default_value():
                # For inputs that have the genfile metadata flag, we
                # call the _convert_inputs method to get the generated
                # value.
                genfile = trait_spec.get_metadata('genfile')
                if genfile is not None:
                    gen_val = self._convert_inputs(name, value)
                    value = gen_val
                else:
                    # skip attrs that haven't been assigned
                    continue
            arg = self._format_arg(trait_spec, value)
            pos = trait_spec.get_metadata('position')
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


class TraitedAttr(traits.HasTraits):
    """Provide a few methods necessary to support the Bunch interface.

    In refactoring to Traits, the self.inputs attrs call some methods
    of the Bunch class that the Traited classes do not inherit from
    traits.HasTraits.  We can provide those methods here.

    XXX Reconsider this in the long run, but it seems like the best
    solution to move forward on the refactoring.
    """

    # XXX These are common inputs that I believe all CommandLine
    # objects are suppose to have.  Should we define these here?  As
    # opposed to in each in_spec.  They would not make sense for
    # the output_spec, but I don't know if output_spec needs a parent
    # class like this one.
    # XXX flags and args.  Are these both necessary?
    flags = traits.Str(argstr='%s')
    args = traits.Str(argstr='%s')

    def __init__(self, *args, **kwargs):
        # XXX Should we accept args anymore?
        self._generate_handlers()
        # NOTE: In python 2.6, object.__init__ no longer accepts input
        # arguments.  HasTraits does not define an __init__ and
        # therefore these args were being ignored.
        #super(TraitedAttr, self).__init__(*args, **kwargs)
        super(TraitedAttr, self).__init__()
        for key, val in kwargs.items():
            setattr(self, key, val)

    def __repr__(self):
        outstr = []
        for name, trait_spec in self.items():
            value = getattr(self, name)
            outstr.append('%s = %s' % (name, value))
        return '\n'.join(outstr)

    def __deepcopy__(self, memo):
        # When I added the dynamic trait notifiers via
        # on_trait_change, tests errored when the run method was
        # called.  I would get this error: 'TypeError: instancemethod
        # expected at least 2 arguments, got 0' and a traceback deep
        # in the copy module triggered by the
        # 'InterfaceResult(deepcopy(self), runtime)' line returned
        # from CommandLine._runner.  To fix this, I create a new
        # instance of self, then assign all traited attrs with
        # deepcopied values.
        id_self = id(self)
        if id_self in memo:
            return memo[id_self]
        # Create new dictionary of trait items with deep copies of elements
        dup_dict = {}
        for key in self.traits():
            dup_dict[key] = deepcopy(getattr(self, key), memo)
        # create new instance and update with copied values
        dup = self.__class__()
        dup.update(**dup_dict)
        return dup

    def items(self):
        for name, trait_spec in sorted(self.traits().items()):
            yield name, trait_spec

    def _generate_handlers(self):
        # Find all traits with the 'xor' metadata and attach an event
        # handler to them.
        def has_xor(item):
            if is_container(item):
                return item
        xors = self.trait_names(xor=has_xor)
        for elem in xors:
            self.on_trait_change(self._xor_warn, elem)

    def _xor_warn(self, name, old, new):
        trait_spec = self.traits()[name]
        if new:
            xor_names = trait_spec.get_metadata('xor')
            # for each xor, set to default_value
            for trait_name in xor_names:
                if trait_name == name:
                    # skip ourself
                    continue
                tspec = self.traits()[trait_name]
                setattr(self, trait_name, tspec.get_default_value())

    # XXX This is redundant, need to do a global find-replace and remove this
    update = traits.HasTraits.set

#
# DEBUG
# XXX: Simple class to test base classes!
#
class Foo(NEW_CommandLine):
    class in_spec(TraitedAttr):
        infile = traits.Str(argstr='%s', position=0, mandatory=True,
                            desc = 'Input file for Bet')
        outfile = traits.Str(argstr='%s', position=1, mandatory=True,
                             desc = 'Filename for skull stripped image')
        mask = traits.Bool(argstr='-m',
                           desc = 'Create mask image')
        frac = traits.Float(argstr='-f %.2f',
                            desc = 'Threshold for fractional intensity')
        fakey = traits.Bool(argstr = '-fake') # Test for no desc, and
                                              # minimal metadata

        center = traits.List(argstr='-c %s', trait=traits.Int, minlen=3,
                             maxlen=3, units='voxels')
        _xor_inputs = ('functional', 'reduce_bias')
        functional = traits.Bool(argstr='-F', xor=_xor_inputs)
        reduce_bias = traits.Bool(argstr='-B', xor=_xor_inputs)

    class out_spec(traits.HasTraits):
        # Note - desc has special meaning in Traits, similar to __doc__
        outfile = traits.Str(desc = 'Filename for skull stripped image')
        # Would like to do this:
        #    desc = Foo.in_spec.outfile.get_metadata('desc'))
        maskfile = traits.Str(
                        desc = "Filename of binary brain mask (if generated)")

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'bet'

    # def run(self):
    #     print 'Foo.run'

    def get_input_info(self):
        print 'Foo.get_input_info'

def test_Foo():
    from nipype.testing import assert_equal, assert_not_equal, assert_raises
    foo = Foo(infile = '/data/foo.nii')
    assert_equal(foo.inputs.infile, '/data/foo.nii')
    foo.help() # print without error?
    print '\noutputs:'
    outputs = foo.aggregate_outputs()
    print outputs
    assert isinstance(outputs, Bunch)
    assert hasattr(outputs, 'outfile')
    assert hasattr(outputs, 'maskfile')
    # run
    foo.inputs.outfile = '/tmp/bar.nii'
    res = foo.run()
    assert isinstance(res, InterfaceResult)
    assert isinstance(res.runtime, Bunch)
    assert_equal(res.runtime.returncode, 1)
    realcmd = 'bet /data/foo.nii /tmp/bar.nii'
    assert_equal(foo.cmdline, realcmd)
    assert_equal(res.runtime.cmdline, realcmd)

if __name__ == '__main__':
    test_Foo()

