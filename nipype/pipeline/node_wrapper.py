"""
Wraps interfaces modules to work with pipeline engine
"""
import os
import hashlib
from nipype.utils.filemanip import copyfile, fname_presuffix
from nipype.interfaces.base import Bunch, InterfaceResult


class NodeWrapper(object):
    """
    Base class wrapper for interface objects to create nodes that can
    be used in the pipeline engine.

    Parameters
    ----------
    
    interface : interface object
        node specific interface  (fsl.Bet(), spm.Coregister())
    iterables : generator
        key and items to iterate
        for example to iterate over different frac values in fsl.Bet()
        node.iterables = dict(frac=lambda:[0.5,0.6,0.7])
    base_directory : directory
        base output directory (will be hashed before creations)
        default='.'
    diskbased : Boolean
        Whether the underlying object requires disk space for
        operation and storage of output
    overwrite : Boolean
        Whether to overwrite contents of output directory if it
        already exists. If directory exists and hash matches it
        assumes that process has been executed
    name : string
        Name of this node. By default node is named
    modulename.classname
    
    Notes
    -----
    
    creates output directory (hashname)
    discover files to work with
    renames them with hash
    moves hashed_files to hashed_output_directory

    Examples
    --------

    >>> import nipype.interfaces.spm as spm
    >>> realign = NodeWrapper(interface=spm.Realign(),base_directory='test2',diskbased=True)
    >>> realign.inputs.infile = os.path.abspath('data/funcrun.nii')
    >>> realign.inputs.register_to_mean = True
    >>> realign.run()
    """
    def __init__(self, interface=None, iterables={},iterfield=[],
                 base_directory='.',diskbased=False,
                 overwrite=None,name=None):
        #super(NodeWrapper,self).__init__(interface)
        self.interface  = interface
        self.result     = None
        self.iterables  = iterables
        self.iterfield  = []
        self.parameterization = None
        self.output_directory_base  = base_directory
        self.diskbased = diskbased
        self.overwrite = overwrite
        if name is None:
            self.name = '.'.join((interface.__class__.__name__,interface.__class__.__module__.split('.')[-1]))
        else:
            self.name = name

    @property
    def inputs(self):
        return self.interface.inputs

    def set_input(self,parameter,val,*args,**kwargs):
        if callable(val):
            self.interface.inputs[parameter] = val(*args,**kwargs)
        else:
            self.interface.inputs[parameter] = val

    def get_output(self,parameter):
        if self.result is not None:
            return self.result.outputs[parameter]
        else:
            return None
        
    def run(self):
        """Executes an interface within a directory.
        """
        # check to see if output directory and hash exist
        if self.diskbased:
            try:
                outdir = self._output_directory()
                outdir = self._make_output_dir(outdir)
            except:
                print "directory %s exists\n"%outdir
            self.interface.inputs.cwd = outdir
            hashvalue = self.hash_inputs()
            inputstr  = str(self.inputs)
            hashfile = os.path.join(outdir,'_0x%s.txt'%hashvalue)
            if (os.path.exists(hashfile) and self.overwrite) or not os.path.exists(hashfile):
                # copy files over and change the inputs
                for info in self.interface.get_input_info():
                    files = self.inputs[info.key]
                    if files is not None:
                        if type(files) is not type([]):
                            infiles = [files]
                        else:
                            infiles = files
                        for i,f in enumerate(infiles):
                            newfile = fname_presuffix(f,newpath=outdir)
                            if not os.path.exists(newfile):
                                copyfile(f,newfile,copy=info.copy)
                            if type(files) is not type([]):
                                self.inputs[info.key] = newfile
                            else:
                                self.inputs[info.key][i] = newfile
                self._run_interface(execute=True)
                if type(self.result.runtime) == type([]):
                    returncode = 0
                    for r in self.result.runtime:
                        returncode = max(r.returncode,returncode)
                else:
                    returncode = self.result.runtime.returncode
                if returncode == 0:
                    try:
                        fd = open(hashfile,"wt")
                        fd.writelines(inputstr)
                        fd.close()
                    except IOError:
                        print "Unable to open the file in readmode:", filename
                else:
                    print self.result.runtime.stderr
                    print self.inputs
                    raise Exception("Could not run %s"%self.name)
            else:
                # change the inputs
                for info in self.interface.get_input_info():
                    files = self.inputs[info.key]
                    if files is not None:
                        if type(files) is not type([]):
                            infiles = [files]
                        else:
                            infiles = files
                        for i,f in enumerate(infiles):
                            newfile = fname_presuffix(f,newpath=outdir)
                            if not os.path.exists(newfile):
                                copyfiles(f,newfile,copy=info.copy)
                            if type(files) is not type([]):
                                self.inputs[info.key] = newfile
                            else:
                                self.inputs[info.key][i] = newfile
                self._run_interface(execute=False)
        else:
            self._run_interface(execute=True)
        if self.diskbased:
            # Should pickle the output
            pass
        return self.result

    def _run_interface(self,execute=True):
        if len(self.iterfield) == 1:
            itervals = self.inputs[self.iterfield[0]]
            if type(itervals) is not type([]):
                itervals = [itervals]
            self.result = InterfaceResult(interface=[],runtime=[],outputs=Bunch())
            for i,v in enumerate(itervals):
                print "running %s on %s\n"%(self.name,self.iterfield[0])
                self.inputs[self.iterfield[0]] = v
                if execute:
                    result = self.interface.run()
                    self.result.interface.insert(i,result.interface)
                    self.result.runtime.insert(i,result.runtime)
                    outputs = result.outputs
                else:
                    outputs = self.interface.aggregate_outputs()
                for key,val in outputs.iteritems():
                    try:
                        self.result.outputs[key].insert(i,val)
                    except:
                        self.result.outputs[key] = []
                        self.result.outputs[key].insert(i,val)
        else:
            if execute:
                self.result = self.interface.run()
            else:
                self.result = InterfaceResult(interface=None,
                                              runtime=None,
                                              outputs=self.interface.aggregate_outputs())
        
    def update(self, **opts):
        self.inputs.update(**opts)
        
    def hash_inputs(self):
        """ Computes a hash of the input fields of the underlying
        interface """
        return hashlib.md5(str(self.inputs)).hexdigest()

    def _output_directory(self):
        return os.path.abspath(os.path.join(self.output_directory_base,self.name))

    def _make_output_dir(self, outdir):
        """Make the output_dir if it doesn't exist, else raise an exception
        """
        # This needs to be changed to update dynamically based on a hash of
        # CURRENT instance attributes
        odir = os.path.abspath(outdir)
        if os.path.exists(outdir):
            raise IOError('Directory %s exists'%(outdir))
        os.mkdir(outdir)
        return outdir

    def __repr__(self):
        return self.name

