"""
Wraps interfaces modules to work with pipeline engine
"""
import os
import sys
from tempfile import mkdtemp
from copy import deepcopy

from nipype.utils.filemanip import (copyfiles,fname_presuffix, cleandir,
                                    filename_to_list, list_to_filename, md5)
from nipype.interfaces.base import Bunch, InterfaceResult
from nipype.interfaces.fsl import FSLCommand
from nipype.utils.filemanip import save_json

class NodeWrapper(object):
    """
    Base class wrapper for interface objects to create nodes that can
    be used in the pipeline engine.

    Parameters
    ----------
    interface : interface object
        node specific interface  (fsl.Bet(), spm.Coregister())
    iterables : generator
        key and items to iterate using the pipeline engine
        for example to iterate over different frac values in fsl.Bet()
        node.iterables = dict(frac=lambda:[0.5,0.6,0.7])
    iterfield : 1-element list
        key over which to repeatedly call the function.
        for example, to iterate FSL.Bet over multiple files, one can
        set node.iterfield = ['infile']
    base_directory : directory
        base output directory (will be hashed before creations)
        default=None, which results in the use of mkdtemp
    diskbased : Boolean
        Whether the underlying object requires disk space for
        operation and storage of output
    overwrite : Boolean
        Whether to overwrite contents of output directory if it
        already exists. If directory exists and hash matches it
        assumes that process has been executed
    name : string
        Name of this node. By default node is named
        modulename.classname. But when the same class is being used
        several times, a different name ensures that output directory
        is not overwritten each time the same functionality is run.
    
    Notes
    -----
    creates output directory
    copies/discovers files to work with
    saves a hash.json file to indicate that a process has been completed

    Examples
    --------
    >>> import nipype.interfaces.spm as spm
    >>> realign = NodeWrapper(interface=spm.Realign(), base_directory='test2', \
            diskbased=True)
    >>> realign.inputs.infile = os.path.abspath('data/funcrun.nii')
    >>> realign.inputs.register_to_mean = True
    >>> realign.run() # doctest: +SKIP

    """
    def __init__(self, interface=None,
                 iterables={}, iterfield=[],
                 diskbased=False, base_directory=None,
                 overwrite=False,
                 name=None):
        # interface can only be set at initialization
        if interface is None:
            raise Exception('Interface must be provided')
        self._interface  = interface
        self._result     = None
        self.iterables  = iterables
        self.iterfield  = iterfield
        self.parameterization = None
        self.disk_based = diskbased
        self.output_directory_base  = None
        self.overwrite = None
        if not self.disk_based:
            if base_directory is not None:
                msg = 'Setting base_directory requires a disk based interface'
                raise ValueError(msg)
        if self.disk_based:
            self.output_directory_base  = base_directory
            self.overwrite = overwrite
        if name is None:
            cname = interface.__class__.__name__
            mname = interface.__class__.__module__.split('.')[-1]
            self.name = '.'.join((cname, mname))
        else:
            self.name = name

    @property
    def interface(self):
        return self._interface
    
    @property
    def result(self):
        return self._result

    @property
    def inputs(self):
        return self._interface.inputs

    def set_input(self, parameter, val, *args, **kwargs):
        if callable(val):
            setattr(self._interface.inputs, parameter, 
                    deepcopy(val(*args, **kwargs)))
        else:
            setattr(self._interface.inputs, parameter, deepcopy(val))

    def get_output(self, parameter):
        if self._result is not None:
            return self._result.outputs.get(parameter)
        else:
            return None

    def _save_hashfile(self, hashfile, hashed_inputs):
        try:
            save_json(hashfile, hashed_inputs)
        except (IOError, TypeError):
            err_type = sys.exc_info()[0]
            if err_type is TypeError:
                # XXX - SG current workaround is to just
                # create the hashed file and not put anything
                # in it
                fd = open(hashfile,'wt')
                fd.writelines(str(hashed_inputs))
                fd.close()
                print "Unable to write a particular type to the json file"
            else:
                print "Unable to open the file in write mode:", hashfile
        
        
    def run(self,updatehash=None):
        """Executes an interface within a directory.
        """
        # print "\nInputs:\n" + str(self.inputs) +"\n"
        # check to see if output directory and hash exist
        if self.disk_based:
            outdir = self._output_directory()
            outdir = self._make_output_dir(outdir)
            # This is a temporary measure while exploring alternatives to
            # dealing with cwd
            if not isinstance(self._interface, FSLCommand):
                self._interface.inputs.cwd = outdir
            # Get a dictionary with hashed filenames and a hashvalue
            # of the dictionary itself.
            hashed_inputs, hashvalue = self.inputs._get_bunch_hash()
            hashfile = os.path.join(outdir, '_0x%s.json' % hashvalue)
            if updatehash:
                self._save_hashfile(hashfile,hashed_inputs)
            if not updatehash and (self.overwrite or not os.path.exists(hashfile)):
                print "continuing to execute\n"
                cleandir(outdir)
                # copy files over and change the inputs
                for info in self._interface.get_input_info():
                    files = self.inputs[info.key]
                    if files is not None:
                        infiles = filename_to_list(files)
                        newfiles = copyfiles(infiles, [outdir], copy=info.copy)
                        self.inputs[info.key] = list_to_filename(newfiles)
                self._run_interface(execute=True, cwd=outdir)
                if type(self._result.runtime) == list:
                    # XXX In what situation is runtime ever a list?
                    # Normally it's a Bunch.
                    # Ans[SG]: Runtime is a list when we are iterating
                    # over an input field using iterfield 
                    returncode = 0
                    for r in self._result.runtime:
                        returncode = max(r.returncode, returncode)
                else:
                    returncode = self._result.runtime.returncode
                if returncode == 0:
                    self._save_hashfile(hashfile,hashed_inputs)
                else:
                    msg = "Could not run %s" % self.name
                    msg += "\nwith inputs:\n%s" % self.inputs
                    msg += "\n\tstderr: %s" % self._result.runtime.stderr
                    raise StandardError(msg)
            else:
                print "skipping\n"
                # change the inputs
                for info in self._interface.get_input_info():
                    files = self.inputs[info.key]
                    if files is not None:
                        if type(files) is not type([]):
                            infiles = [files]
                        else:
                            infiles = files
                        for i,f in enumerate(infiles):
                            newfile = fname_presuffix(f, newpath=outdir)
                            if not os.path.exists(newfile):
                                copyfiles(f, newfile, copy=info.copy)
                            if type(files) is not type([]):
                                self.inputs[info.key] = newfile
                            else:
                                self.inputs[info.key][i] = newfile
                self._run_interface(execute=False, cwd=outdir)
        else:
            self._run_interface(execute=True)
        if self.disk_based:
            # Should pickle the output
            pass
        # print "\nOutputs:\n" + str(self._result.outputs) +"\n"
        return self._result

    # XXX This function really seriously needs to check returncodes and similar
    def _run_interface(self, execute=True, cwd=None):
        if cwd is not None:
            old_cwd = os.getcwd()
            os.chdir(cwd)
        if len(self.iterfield) > 1:
            raise ValueError('At most one iterfield is supported at this time\n'
                             'Got: %s in %s', (self.iterfield, self.name))
        if len(self.iterfield) == 1:
            # This branch of the if takes care of iterfield and
            # basically calls the underlying interface each time 
            itervals = self.inputs.get(self.iterfield[0])
            notlist = False
            if type(itervals) is not list:
                notlist = True
                itervals = [itervals]
            self._result = InterfaceResult(interface=[], runtime=[],
                                           outputs=Bunch())
            for i,v in enumerate(itervals):
                print "iterating %s on %s: %s\n"%(self.name, self.iterfield[0], str(v))
                self.set_input(self.iterfield[0], v)
                # XXX - SG - we might consider creating a sub
                # directory for each v
                if execute:
                    cmdline = None
                    try:
                        cmdline = self._interface.cmdline
                    except:
                        pass
                    if cmdline is not None:
                        print "Running command:"
                        print cmdline
                    # Passing cwd in here is redundant, even for FSLCommand
                    # instances. For FSLCommand, this is an example of another
                    # way we might do it if we decide to ditch the setwd
                    # approach. Again - something should be removed when we
                    # settle on a solution
                    result = self._interface.run(cwd=cwd)
                    if result.runtime.returncode != 0:
                        print result.runtime.stderr
                    self._result.interface.insert(i, result.interface)
                    self._result.runtime.insert(i, result.runtime)
                    outputs = result.outputs
                else:
                    # Could also pass in cwd here...
                    outputs = self._interface.aggregate_outputs()

                if outputs is None:
                    raise Exception('%s failed to properly generate outputs (returncode'
                          'was 0)' % self.name)
                
                for key,val in outputs.iteritems():
                    try:
                        # This has funny default behavior if the length of the
                        # list is < i - 1. I'd like to simply use append... feel
                        # free to second my vote here!
                        self._result.outputs.get(key).insert(i, val)
                    except AttributeError:
                        # .insert(i, val) is equivalent to the following if
                        # outputs.key == None, so this is far less likely to
                        # produce subtle errors down the road!
                        setattr(self._result.outputs, key, [val])

            if notlist:
                self.set_input(self.iterfield[0], itervals.pop())
            else:
                self.set_input(self.iterfield[0], itervals)
        else:
            if execute:
                cmdline = None
                try:
                    cmdline = self._interface.cmdline
                except:
                    pass
                if cmdline is not None:
                    print "Running command:"
                    print cmdline
                self._result = self._interface.run(cwd=cwd)
                if self._result.runtime.returncode != 0:
                    print self._result.runtime.stderr
            else:
                # Likewise, cwd could go in here
                print "Not running command. just collecting outputs:"
                aggouts = self._interface.aggregate_outputs()
                self._result = InterfaceResult(interface=None,
                                               runtime=None,
                                               outputs=aggouts)
            if self._result.outputs is None:
                raise Exception('%s failed to properly generate outputs (returncode'
                                'was 0)\nSTDOUT:\n%s\nSTDERR:\n%s\n' % (self.name,
                                                                  self._result.runtime.stdout,
                                                                  self._result.runtime.stderr))
        
        if cwd is not None:
            os.chdir(old_cwd)

    def update(self, **opts):
        self.inputs.update(**opts)
        
    def hash_inputs(self):
        """Computes a hash of the input fields of the underlying interface."""
        return md5(str(self.inputs)).hexdigest()

    def _output_directory(self):
        if self.output_directory_base is None:
            self.output_directory_base = mkdtemp()
        return os.path.abspath(os.path.join(self.output_directory_base,
                                            self.name))

    def _make_output_dir(self, outdir):
        """Make the output_dir if it doesn't exist.
        """
        if not os.path.exists(os.path.abspath(outdir)):
            # XXX Should this use os.makedirs which will make any
            # necessary parent directories?  I didn't because the one
            # case where mkdir failed because a missing parent
            # directory, something went wrong up-stream that caused an
            # invalid path to be passed in for `outdir`.
            os.mkdir(outdir)
        return outdir

    def __repr__(self):
        return self.name

