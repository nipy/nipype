import os
from copy import deepcopy
import gzip
import nipype.pipeline.engine as pe

from nipype.interfaces.base import (traits, isdefined, 
                                    File, InputMultiPath, OutputMultiPath)
from nipype.utils.filemanip import fname_presuffix, split_filename


class FileProxyNode(pe.Node):
    """ Generic file proxy for transforming files before and after interface
    execution."""
    
    def __init__(self,*args,**kwargs):
        self.proxy_out = kwargs.pop('proxy_out',True)
        super(FileProxyNode,self).__init__(*args,**kwargs)
    
    def _transform_input_file(self, fname, incwd=True):
        raise NotImplementedError

    def _add_output_file2proxy(self, fname):
        raise NotImplementedError

    def _process_output_files(self):
        raise NotImplementedError

    def _clean_proxy_files(self):
        raise NotImplementedError

    def _run_command(self,execute,copyfiles=True):
        self._file2 = []
        if execute and copyfiles:
            self._copyfiles_to_wd(os.getcwd(),execute)
            self._proxy_outputs = self.interface._list_outputs()
            self._proxy_originputs = deepcopy(self._interface.inputs)
            for name, spec in self.outputs.traits(transient=None).items():
                value = self.interface._list_outputs()[name]
                if isdefined(value):
                    if spec.is_trait_type(File):
                        self._add_output_file2proxy(value)
                    elif spec.is_trait_type(OutputMultiPath) and self.proxy_out:
                        rec_add = lambda x: map(rec_add,x) if isinstance(x,list) else self._add_output_file2proxy(x)
                        map(rec_add,value)

            for name, spec in self.inputs.traits(transient=None).items():
                value = getattr(self.inputs, name)
                if isdefined(value):
                    if spec.is_trait_type(File):
                        if os.path.isfile(value):
                            value = self._transform_input_file(value,copyfiles)
                            self.inputs.trait(name).copyfile = None
                        elif self.proxy_out:
                            value = self._add_output_file2proxy(value)
                    elif spec.is_trait_type(InputMultiPath):
                        rec_add = lambda x: map(rec_add,x) if isinstance(x,list) else self._transform_input_file(x,copyfiles)
                        if value:
                            value = map(rec_add, value)
                        self.inputs.trait(name).copyfile = None
                    elif spec.is_trait_type(OutputMultiPath) and self.proxy_out:
                        rec_add = lambda x: map(rec_add,x) if isinstance(x,list) else self._add_output_file2proxy(x)
                        if value:
                            value = map(rec_add, value)
                setattr(self.inputs,name,value)
        results = super(FileProxyNode,self)._run_command(execute,copyfiles)
        return results
    
    def _save_results(self, result, cwd):
        self._process_output_files()
        self._clean_proxy_files()
        if hasattr(self,'_proxy_outputs') and self.proxy_out:
            for t,v in self._proxy_outputs.items():
                setattr(result.outputs,t,v)
        return super(FileProxyNode,self)._save_results(result,cwd)
        



class GunzipNode(FileProxyNode):
    """ Handle gunziped file (as .nii.gz) for Matlab/SPM interfaces.
    Only the one which allows output file specification can gzip output.
    
    Any inputs having .nii.gz extension will be temporarily gunzipped and provided as input to interface.
    Any output file name having .nii.gz extension they will be provided to interface as .nii and then gzipped after interface runs.

    Example
    ========

    >>> import nipype.pipeline.file_proxy as fileproxy
    >>> realign = fileproxy.GunzipNode(interface=spm.Realign(),name='realign')
    >>> realign.inputs.in_files = 'functional.nii.gz'
    >>> realign.run()
    """
    
    def _transform_input_file(self,fname, incwd=True):
        path,base,ext = split_filename(fname)
        if not hasattr(self,'_gunzipped_files'):
            self._gunzipped_files = []
        if ext[-3:]=='.gz':
            if incwd:
                gunziped_file = fname_presuffix(fname, suffix=ext[:-3],
                                                use_ext=False,
                                                newpath=os.getcwd())
            else:
                gunziped_file = fname_presuffix(fname,suffix=ext[:-3],
                                                use_ext=False)
            f_in = gzip.open(fname,'rb')
            f_out = open(gunziped_file,'wb')
            f_out.write(f_in.read())
            f_out.close()
            f_in.close()
            self._gunzipped_files.append(gunziped_file)
            return gunziped_file
        return fname
            

    def _add_output_file2proxy(self,fname):
        path,base,ext = split_filename(fname)
        if not hasattr(self,'_file2gzip'):
            self._file2gzip = []
        if ext[-3:]=='.gz':
            fname = fname_presuffix(fname,newpath=os.getcwd())
            uncomp = fname_presuffix(fname,suffix=ext[:-3],use_ext=False,
                                     newpath=os.getcwd())
            self._file2gzip.append((uncomp,fname))
            return uncomp
        else:
            return fname
        
    def _process_output_files(self):
        if hasattr(self,'_file2gzip'):
            for f_in, f_out in self._file2gzip:
                if os.path.isfile(f_in):
                    f_in = open(f_in,'rb')
                    f_out = gzip.open(f_out,'wb')
                    f_out.write(f_in.read())
                    f_out.close()
                    f_in.close()

    def _clean_proxy_files(self):
        if hasattr(self,'_gunzipped_files'):
            for f in self._gunzipped_files:
                if os.path.isfile(f):
                    os.remove(f)
        if hasattr(self,'_file2gzip'):
            for f in self._file2gzip:
                if os.path.isfile(f[0]):
                    os.remove(f[0])
