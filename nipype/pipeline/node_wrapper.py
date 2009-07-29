"""
Wraps interfaces modules to work with pipeline engine
"""
import os, re
import hashlib
import shutil
from nipype.interfaces.base import CommandLine as cl
import nipype.interfaces.fsl as fsl


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
                 output_directory='.',diskbased=False):
        #super(NodeWrapper,self).__init__(interface)
        self.interface = interface
        self.inputs = {}
        self.outputs = {}
        self.hashinputs = {}
        self.hashinputs['files'] = []
        self.iterables = iterables
        self.output_directory_base  = output_directory
        self.diskbased = diskbased

        
    def pre_execute(self):
        raise NotImplementedError("Child class must implement pre_execute()")
        """ moves files to unique hashednames in unique hashed_dir"""
        #self.update()
        #[self.inputs.update({k:v}) for k, v in self.interface.opts.iteritems() if v is not None]
        
        #hashed_dir = self.make_output_dir(self.output_directory())
        #self.hashinputs = 
        
    def post_execute(self):
        raise NotImplementedError("Child class must implement post_execute()")

    def execute(self):
        raise NotImplementedError("Child class must implement execute()")

    def update(self, **opts):
        self.interface = self.interface.update(**opts)
        
    def hash_inputs(self):
        return hashlib.md5(str(self.inputs)).hexdigest()

    def output_directory(self):
        return os.path.join(self.output_directory_base,
                            ''.join((self.interface.cmd, '_0x', self.hash_inputs())))

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


    def md5file(self,filename, excludeline="", includeline=""):
        """Compute md5 hash of the specified file"""
        m = hashlib.md5()
        try:
            for line in open(filename,"rb"):
                if excludeline and line.startswith(excludeline):
                    continue
                m.update(includeline)
            return m.hexdigest()
                 
        except IOError:
            print "Unable to open the file in readmode:", filename
            

    def hash_rename(self, filename, hash):
        """renames a file given original filename and hash
        and sets path to output_directory
        """
        path, name = os.path.split(filename)
        name, ext = os.path.splitext(name)
        newfilename = ''.join((name,'_0x',hash,ext))
        return os.path.join(self.output_directory(),newfilename)
        

    def check_forhash(self, filename):
        """checks if file has a hash in its filename"""
        if type(filename) == type(list):
            filename = filename[0]
        path, name = os.path.split(filename)

        if re.search('(_0x[a-z0-9]{32})',name):
            hash = re.findall('(_0x[a-z0-9]{32})',name)
            return True, hash
        else:
            return False, None

    def copyfiles_to_cwd(self,originalfile, newfile,symlink=True):
        """given a file moves it to a working directory

        Parameters
        ----------
        originalfile : file
            full path to original file
        newfile : file
            full path to new file
        symlink : Bool
            specifies whether to copy or symlink files
            (default=True) but only for posix systems
         
        Returns
        -------
        output : dict
            dictionary holding 'out', 'err', 'returncode'
        """
        if os.name is 'posix' and symlink:
            clout = cl().run('ls -s %s %s'%(originalfile, newfile))
        else:                
            clout = cl().run('cp %s %s'%(originalfile, newfile))
        return clout.output
        # if no signature hash_rename

        # join to output_directory

        # copy or symlink file to new directory

        # update new hashed name in output_directory 
        # to hashedfiles dictionary



class SkullStripNode(NodeWrapper):
    """ Node Wrapper for skull stripping 
            fsl.Bet()
            spm.Segment()
    """
    def __init__(self,interface=None, iterables={},
                 output_directory='.',diskbased=True):
        NodeWrapper.__init__(self, interface, iterables,
                             output_directory,diskbased)

        self.update()
        [self.inputs.update({k:v}) for k, v in self.interface.opts.iteritems() if v is not None]
        
    def pre_execute(self):
        """ moves files to unique hashednames in unique hashed_dir"""
        self.update()
        [self.inputs.update({k:v}) for k, v in self.interface.opts.iteritems() if v is not None]
        
        hashed_dir = self.make_output_dir(self.output_directory())
        # get hashed names
        
        if type(self.interface) == type(fsl.Bet()):
            # only one file allowed
        
            inputf = self.inputs['infile'][0]
            try:
                outputf = self.inputs['outfile']
            except KeyError:
                
                pth, nme = os.path.split(inputf)
                outputf = os.path.join(pth,'ss_%s'%(nme))
            hashash, hash =  self.check_forhash(inputf)
            if hashash:
                newinf = self.hash_rename(inputf,'')
                newoutf = self.hash_rename(outputf,hash)

            else:
                hash =  self.md5file(inputf)
                newinf = self.hash_rename(inputf,hash)
                newoutf = self.hash_rename(outputf,hash)
            self.copyfiles_to_cwd(inputf, newinf,symlink=False)
            
            self.hashinputs['infile'] = newinf
            self.hashinputs['outfile'] = newoutf

        self.update(**self.hashinputs)

        
    def post_execute(self):
        
        self.outputs['outfile'] = self.interface.outfile
        self.outputs['err'] = self.interface.err
        self.outputs['out'] = self.interface.out
        self.outputs['retcode'] = self.interface.retcode


    def execute(self):
        """ runs node with updated inputs"""
        self.pre_execute()
        self.interface = self.interface.run()
        self.post_execute()

table = {'spm': {'Realign': {'copyfiles': ['infile'], 'hash': [True]]}}

node_wrapper(package,interface,overwrite=None):
    interface = __import__('.'.join((package,interface)))
    interface.get_modified_inputs()
    

interface=spm.Realign(),
                copyfiles=['infile'],
                hash=[True]):
    if interface == spm.Realign:
        wrapped_node = SpmRealignWrapper() # node_wrapper()
    
    return wrapped_node



        
        
            
            
    
