import nipype.interfaces.base as nii
from nipype.testing import assert_equal, assert_not_equal, assert_raises
import os

#test Bunch
def test_bunch():
    b = nii.Bunch()
    yield assert_equal, b.__dict__,{}
    b = nii.Bunch(a=1,b=[2,3])
    yield assert_equal, b.__dict__,{'a': 1, 'b': [2,3]}

def test_bunch_attribute():
    b = nii.Bunch(a=1,b=[2,3],c=None)
    yield assert_equal, b.a ,1
    yield assert_equal, b.b, [2,3]
    yield assert_equal, b.c, None

def test_bunch_repr():
    b = nii.Bunch(b=2,c=3,a=dict(n=1,m=2))
    yield assert_equal, repr(b), "Bunch(a={'m': 2, 'n': 1}, b=2, c=3)"

def test_bunch_methods():
    b = nii.Bunch(a=2)
    b.update(a=3)
    newb = b.dictcopy()
    yield assert_equal, b.a, 3
    yield assert_equal, b.get('a'), 3
    yield assert_equal, b.get('badkey', 'otherthing'), 'otherthing'
    yield assert_not_equal, b, newb
    yield assert_equal, type(dict()), type(newb)
    yield assert_equal, newb['a'], 3

def test_bunch_hash():
    # NOTE: Since the path to the json file is included in the Bunch,
    # the hash will be unique to each machine.
    pth = os.path.split(os.path.abspath(__file__))[0]
    json_pth = os.path.join(pth, 'realign_json.json')
    b = nii.Bunch(infile = json_pth, 
                  otherthing = 'blue',
                  yat = True)
    newbdict, bhash = b._get_bunch_hash()
    yield assert_equal, bhash, 'ddcc7b4ec5675df8cf317a48bd1857fa'
    # Make sure the hash stored in the json file for `infile` is correct.
    jshash = nii.md5()
    fp = file(json_pth)
    jshash.update(fp.read())
    fp.close()
    yield assert_equal, newbdict['infile'][0][1], jshash.hexdigest()
    yield assert_equal, newbdict['yat'], True

#test CommandLine
def test_commandline():
    cl = nii.CommandLine('echo', 'foo')
    yield assert_equal, cl.inputs.args, ['echo', 'foo']
    yield assert_equal, cl.cmdline, 'echo foo'
    yield assert_not_equal, cl, cl.run()
    
    yield assert_equal, nii.CommandLine('echo foo').cmdline,\
        nii.CommandLine(args='echo foo').cmdline
    yield assert_equal, nii.CommandLine('ls','-l').cmdline,\
        nii.CommandLine('ls -l').cmdline
    clout = cl.run()
    yield assert_equal, clout.runtime.returncode, 0
    yield assert_equal, clout.runtime.stderr,  ''
    yield assert_equal, clout.runtime.stdout, 'foo\n'
    yield assert_equal, clout.interface.cmdline, cl.cmdline
    yield assert_not_equal, clout.interface, cl

"""
stuff =CommandLine('this is what I want to run')

better = Bet(frac=0.5, input='anotherfile', flags = ['-R', '-k'])

betted = better.run(input='filea', output='ssfilea')

def f(a='', *args, **kwargs):
    whateve

f(file1, file2, a=Something, b='this')


cl = COmmandLine('ls')

d1 = cl.run('/path/to/d1')

d2 = cl.run('/path/to/d2')

d3 = CommandLine().run('ls /path/to/d3')
or
d3 = CommandLine('ls /path/to/d3').run()
or
d3 = CommandLine('ls').run('/path/to/d3')


stuff = CommandLine(flags={'-f':0.5, 'otherthing': 2, '-c':[100,87,92], '-R':None})

stuff = CommandLine('ls',flags=['-R', '--thingy', '100 87 90'])


cmd1 = CommandLine('ls -l *')
cmd2 = CommandLine.update('-a -h').remove('-l')
"""

def test_TraitedSpec():
    class spec(nii.TraitedSpec):
        foo = nii.traits.Int
        goo = nii.traits.Float
        hoo = nii.traits.List(nii.traits.File)

    a = spec(foo=1, goo=2.0, hoo=['foo.nii'])
    

def test_NEW_Interface():
    pass

def test_NEW_BaseInterface():
    pass

def test_NEW_Commandline():
    pass

class TraitedSpec(traits.HasTraits):
    """Provide a few methods necessary to support the Bunch interface.

    In refactoring to Traits, the self.inputs attrs call some methods
    of the Bunch class that the Traited classes do not inherit from
    traits.HasTraits.  We can provide those methods here.

    XXX Reconsider this in the long run, but it seems like the best
    solution to move forward on the refactoring.
    """

    def __init__(self, **kwargs):
        self._generate_handlers()
        # NOTE: In python 2.6, object.__init__ no longer accepts input
        # arguments.  HasTraits does not define an __init__ and
        # therefore these args were being ignored.
        #super(TraitedSpec, self).__init__(*args, **kwargs)
        super(TraitedSpec, self).__init__()
        for key, val in kwargs.items():
            setattr(self, key, val)

    def __repr__(self):
        outstr = []
        for name, trait_spec in self.items():
            value = getattr(self, name)
            outstr.append('%s = %s' % (name, value))
        return '\n'.join(outstr)

    def items(self):
        for name, trait_spec in sorted(self.traits().items()):
            if name in ['trait_added', 'trait_modified']:
                # Skip these trait api functions
                continue
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
                    setattr(self, trait_name, tspec.default)
                    msg = 'Input %s is mutually exclusive with inputs:  %s' \
                        % (name, ', '.join(trait_spec.xor))
                    msg += '\nResetting %s to %s' % (trait_name,
                                                     tspec.default)
                    warn(msg)


    def _dictcopy(self):
        out_dict = {}
        for name, trait_spec in self.items():
            out_dict[name] = deepcopy(getattr(self, name))
        return out_dict

    def _hash_infile(self, adict, key):
        # Inject file hashes into adict[key]
        stuff = adict[key]
        if not is_container(stuff):
            stuff = [stuff]
        file_list = []
        for afile in stuff:
            file_list.append((afile, hash_infile(afile) ))
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
            The md5 hash value of the traited spec

        """

        infile_list = []
        for name, trait_spec in self.items():
            val = getattr(self, name)
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
                    infile_list.append(name)
            except TypeError:
                # `item` is not a file or string.
                continue
        dict_withhash = self._dictcopy()
        dict_nofilename = self._dictcopy()
        for item in infile_list:
            dict_withhash[item] = self._hash_infile(dict_withhash, item)
            dict_nofilename[item] = [val[1] for val in dict_withhash[item]]
        # Sort the items of the dictionary, before hashing the string
        # representation so we get a predictable order of the
        # dictionary.
        sorted_dict = str(sorted(dict_nofilename.items()))
        return (dict_withhash, md5(sorted_dict).hexdigest())

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

    def run(self, cwd=None):
        """Execute the command."""
        raise NotImplementedError

    def aggregate_outputs(self):
        """Called to populate outputs"""
        raise NotImplementedError

    @classmethod
    def help(cls):
        """ Prints class help"""
        raise NotImplementedError
        
    def _inputs_help(self):
        """ Prints inputs help"""
        raise NotImplementedError
    
    def _outputs_help(self):
        """ Prints outputs help"""
        raise NotImplementedError
    
    def _outputs(self):
        """ Initializes outputs"""
        raise NotImplementedError

    def _list_outputs(self):
        """ List expected outputs"""
        raise NotImplementedError
        
    def _get_filecopy_info(self):
        """ Provides information about file inputs to copy or link to cwd.
            Necessary for pipeline operation
        """
        raise NotImplementedError

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

    def __init__(self, **inputs):
        if not self.input_spec:
            raise Exception('No input_spec in class: %s' % \
                          self.__class__.__name__)
        self.inputs = self.input_spec(**inputs)

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
            desc = trait_spec.desc
            if trait_spec.mandatory:
                if not manhelpstr:
                    manhelpstr = ['','Mandatory:']
                manhelpstr += [' %s: %s' % (name, desc)]
            else:
                if not opthelpstr:
                    opthelpstr = ['','Optional:']
                default = trait_spec.default
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
        if self.output_spec:
            output_spec = self.output_spec()
            for name, trait_spec in sorted(output_spec.items()):
                helpstr += ['%s: %s' % (name, trait_spec.desc)]
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

    def _check_mandatory_inputs(self):
        for name, trait_spec in self.inputs.items():
            if trait_spec.mandatory:
                value = getattr(self.inputs, name)
                if not value:
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
    
    @classmethod
    def _get_filecopy_info(cls):
        """ Provides information about file inputs to copy or link to cwd.
            Necessary for pipeline operation
        """
        info = []
        for name, trait_spec in cls.input_spec().items():
            if trait_spec.copyfile is not None:
                info.append(dict(key=name,
                                 copy=trait_spec.copyfile))
        return info


class NEW_CommandLine(NEW_BaseInterface):
    """Implements functionality to interact with command line programs

    >>> from nipype.interfaces.base import NEW_CommandLine
    >>> cli = NEW_CommandLine(command='which')
    >>> cli.inputs.args = 'ls'
    >>> cli.cmdline
    'which ls'
    
    >>> cli.inputs._dictcopy()
    {'args' : 'ls'}

    >>> cli.inputs._get_bunch_hash()
    ({'args': 'ls'}, 'dacab83636459a3a76bc73e1f70b6d4e')

    """

    class input_spec(TraitedSpec):
        args = traits.Str(argstr='%s', desc='Parameters to the command')
        
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

    def set_cmd(self, cmd):
        self._cmd = cmd

    @property
    def cmdline(self):
        """validates options and generates command line"""
        self._check_mandatory_inputs()
        allargs = self._parse_inputs()
        allargs.insert(0, self.cmd)
        return ' '.join(allargs)

    def _update_env(self):
        env = deepcopy(os.environ.data)
        env.update(self._environ)
        return env
        
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
            A result object with a copy of self in `interface`

        """
        for key, val in inputs.items():
            setattr(self.inputs, key, val)

        if cwd is None:
            cwd = os.getcwd()
        # initialize provenance tracking
        runtime = Bunch(cmdline=self.cmdline, cwd=cwd,
                        stdout = None, stderr = None,
                        returncode = None, duration = None,
                        environ=deepcopy(os.environ.data),
                        hostname = gethostname())

        t = time()
        if hasattr(self, '_environ') and self._environ:
            env = self._update_env()
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

    def _gen_filename(self, name):
        raise NotImplementedError
    
    def _list_outputs(self):
        if self.output_spec:
            return self._outputs()._dictcopy()
        else:
            return None

    def aggregate_outputs(self):
        outputs = self._outputs()
        expected_outputs = self._list_outputs()
        if expected_outputs:
            for key, val in expected_outputs.items():
                setattr(outputs, key, val)
        return outputs

    def _format_arg(self, name, trait_spec, value):
        '''A helper function for _parse_inputs'''
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
        for name, trait_spec in self.inputs.items():
            if skip and name in skip:
                continue
            value = getattr(self.inputs, name)
            if not value:
                if trait_spec.genfile:
                    gen_val = self._gen_filename(name)
                    value = gen_val
                else:
                    continue
            arg = self._format_arg(name, trait_spec, value)
            pos = trait_spec.position
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
    ...     foo = MultiPath(traits.File(exists=False))
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
        return super(MultiPath, self).validate(object, name, newvalue)
