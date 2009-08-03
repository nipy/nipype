"""
Wraps interfaces modules to work with pipeline engine
"""
import os
import hashlib
from nipype.utils.filemanip import copyfiles
from nipype.interfaces.base import Bunch, InterfaceResult


class NodeWrapper(object):
    """
    base class wrapper for specific interface objects

    Parameters
    ----------
    interface : interface object
        node specific interface  (fsl.Bet(), spm.Coregister())
    iterables : generator
        key and items to iterate
        for example to iterate over different frac values in fsl.Bet()
        node.iterables = dict(frac=lambda:[0.5,0.6,0.7])
    output_directory : directory
        base output directory (will be hashed before creations)
        default='.'

    Notes
    -----
    creates output directory (hashname)
    discover files to work with
    renames them with hash
    moves hashed_files to hashed_output_directory
    
    """
    def __init__(self, interface=None, iterables={},
                 output_directory='.',diskbased=False,
                 overwrite=None):
        #super(NodeWrapper,self).__init__(interface)
        self.interface  = interface
        self.output     = None
        self.iterables  = iterables
        self.parameterization = None
        self.output_directory_base  = output_directory
        self.diskbased = diskbased
        self.overwrite = overwrite

    @property
    def inputs(self):
        return self.interface.inputs

    def set_input(self,parameter,val,*args,**kwargs):
        if callable(val):
            self.interface.inputs[parameter] = val(*args,**kwargs)
        else:
            self.interface.inputs[parameter] = val

    def get_output(self,parameter):
        if self.output is not None:
            self.output.outputs[parameter]
        else:
            return None
        
    def run(self):
        """
        >>> import nipype.interfaces.spm as spm
        >>> realign = nw.NodeWrapper(interface=spm.Realign(),output_directory='test2',diskbased=True)
        >>> realign.inputs.infile = os.path.abspath('data/funcrun.nii')
        >>> realign.inputs.register_to_mean = True
        >>> realign.run()
        """
        # check to see if output directory and hash exist
        if self.diskbased:
            try:
                outdir = self.output_directory()
                outdir = self.make_output_dir(outdir)
            except:
                print "directory %s exists\n"%outdir
            hashvalue = self.hash_inputs()
            hashfile = os.path.join(outdir,'_0x%s.txt'%hashvalue)
            self.interface.inputs.cwd = outdir
            if (os.path.exists(hashfile) and self.overwrite) or not os.path.exists(hashfile):
                try:
                    fd = open(hashfile,"wt")
                    fd.writelines(str(self.interface.inputs))
                    fd.close()
                except IOError:
                    print "Unable to open the file in readmode:", filename
                # copy files over and change the inputs
                for info in self.interface.get_input_info():
                    originalfile = self.inputs[info.key]
                    path,name = os.path.split(originalfile)
                    newfile = os.path.abspath(os.path.join(outdir,name))
                    copyfiles(originalfile,newfile,copy=info.copy)
                    self.inputs[info.key] = newfile
                self.output = self.interface.run()
            else:
                # change the inputs
                for info in self.interface.get_input_info():
                    originalfile = self.inputs[info.key]
                    path,name = os.path.split(originalfile)
                    newfile = os.path.abspath(os.path.join(outdir,name))
                    self.inputs[info.key] = newfile
                self.output = InterfaceResult(interface=None,
                                              runtime=None,
                                              outputs=self.interface._aggregate_outputs())
        else:
            self.output = self.interface.run()
        if self.diskbased:
            # Should pickle the output
            pass
        return self.output
    
    def update(self, **opts):
        self.inputs.update(**opts)
        
    def hash_inputs(self):
        """ Computes a hash of the input fields of the underlying
        interface """
        return hashlib.md5(str(self.inputs)).hexdigest()

    def output_directory(self):
        return os.path.abspath(os.path.join(self.output_directory_base,self.interface.cmd))

    def make_output_dir(self, outdir):
        """Make the output_dir if it doesn't exist, else raise an exception
        """
        # This needs to be changed to update dynamically based on a hash of
        # CURRENT instance attributes
        odir = os.path.abspath(outdir)
        if os.path.exists(outdir):
            raise IOError('Directory %s exists'%(outdir))
        os.mkdir(outdir)
        return outdir







        
        
            
            
    
