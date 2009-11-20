"""
Package contains interfaces for using existing functionality in other packages

Exaples  FSL, matlab/SPM , afni

Requires Packages to be installed
"""

import os
import subprocess
from copy import deepcopy
from string import Template
from warnings import warn
import copy

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

    def iteritems(self):
        """iterates over bunch attributes as key,value pairs"""
        return self.__dict__.iteritems()

    def get(self, *args):
        '''Support dictionary get() functionality 
        '''
        return self.__dict__.get(*args)

    def __setitem__(self, key, value):
        '''deprecated, dict-like setting of attributes'''
        # get rid of for 0.2?
        warn(DeprecationWarning('please use direct attribute or .update()'))
        self.__dict__[key] = value

    def __getitem__(self, key):
        '''deprecated, dict-like getting of attributes'''
        # get rid of for 0.2?
        warn(DeprecationWarning('please use direct attribute or .set()'))
        return(self.__dict__[key])

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
        for k, v in sorted(self.iteritems()):
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
                md5obj.update(fp.read())
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

        Returns
        -------
        dict_withhash : dict
            Copy of our dictionary with the new file hashes included
            with each file.
        hashvalue : str
            The md5 hash value of the `dict_withhash`

        """

        infile_list = []
        for key, val in self.iteritems():
            if is_container(val):
                # XXX - SG this probably doesn't catch numpy arrays
                # containing embedded file names either. 
                if type(val) == type({}):
                    # XXX - SG should traverse dicts, but ignoring for now
                    item = None
                else:
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
        for item in infile_list:
            dict_withhash[item] = self._hash_infile(dict_withhash, item)
        # Sort the items of the dictionary, before hashing the string
        # representation so we get a predictable order of the
        # dictionary.
        sorted_dict = str(sorted(dict_withhash.items()))
        return (dict_withhash, md5(sorted_dict).hexdigest())
            
    def __pretty__(self, p, cycle):
        '''Support for the pretty module
        
        pretty is included in ipython.externals for ipython > 0.10'''
        if cycle:
            p.text('Bunch(...)')
        else:
            p.begin_group(6, 'Bunch(')
            first = True
            for k, v in sorted(self.iteritems()):
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
            Note that unlike calls to Popen, cwd=None will still check
            self.inputs.cwd!  Use an alternative like '.' if you need it
        """
        if cwd is None:
            # I'd like to deprecate this -DJC
            cwd = self.inputs.get('cwd', os.getcwd())
        runtime = Bunch(cmdline=self.cmdline, cwd=cwd)

        proc  = subprocess.Popen(runtime.cmdline,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=True,
                                 cwd=cwd)

        runtime.stdout, runtime.stderr = proc.communicate()
        runtime.returncode = proc.returncode

        return InterfaceResult(deepcopy(self), runtime)

    def get_input_info(self):
        """ Provides information about file inputs to copy or link to cwd.
        
        Notes
        -----
        see `spm.Realign.get_input_info`
            
        """
        return []

