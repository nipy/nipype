"""Miscellaneous file manipulation functions

"""
import os
import re
import shutil
from glob import glob
# The md5 module is deprecated in Python 2.6, but hashlib is only
# available as an external package for versions of python before 2.6.
# Both md5 algorithms appear to return the same result.
try:
    from hashlib import md5
except ImportError:
    from md5 import md5

import numpy as np

from nipype.utils.misc import is_container

try:
    # json included in Python 2.6
    import json
except ImportError:
    # simplejson is the json module that was included in 2.6 (I
    # believe).  Used here for Python 2.5
    import simplejson as json

def fname_presuffix(fname, prefix='', suffix='', newpath=None, use_ext=True):
    """Manipulates path and name of input filename

    Parameters
    ----------
    fname : string
        A filename (may or may not include path
    prefix : string
        Characters to prepend to the filename
    suffix : string
        Characters to append to the filename
    newpath : string
        Path to replace the path of the input fname
    use_ext : boolean
        If True (default), appends the extension of the original file
        to the output name.

    Returns
    -------
    Absolute path of the modified filename

    >>> from nipype.utils.filemanip import fname_presuffix
    >>> fname = 'foo.nii.gz'
    >>> fname_presuffix(fname,'pre','post','/tmp')
    '/tmp/prefoopost.nii.gz'
    """
    pth, fname = os.path.split(fname)
    fname, ext = os.path.splitext(fname)
    if fname.endswith('.nii'): # check for double extension nii.gz
        fname,ext2 = os.path.splitext(fname)
        ext = ext2 + ext
    if not use_ext:
        ext = ''
    if newpath:
        pth = os.path.abspath(newpath)
    return os.path.join(pth, prefix+fname+suffix+ext)


def fnames_presuffix(fnames, prefix='', suffix='', newpath=None,use_ext=True):
    """Calls fname_presuffix for a list of files.
    """
    f2 = []
    for fname in fnames:
        f2.append(fname_presuffix(fname, prefix, suffix, newpath, use_ext))
    return f2

def md5file(filename, excludeline="", includeline=""):
    """Compute md5 hash of the specified file"""
    m = md5()
    try:
        for line in open(filename,"rb"):
            if excludeline and line.startswith(excludeline):
                continue
            m.update(line)
        return m.hexdigest()
    except IOError:
        print "Unable to open the file in readmode:", filename
        
def hash_rename(filename, hash):
    """renames a file given original filename and hash
    and sets path to output_directory
    """
    path, name = os.path.split(filename)
    name, ext = os.path.splitext(name)
    newfilename = ''.join((name,'_0x',hash,ext))
    return os.path.join(path,newfilename)
             

def check_forhash(filename):
    """checks if file has a hash in its filename"""
    if isinstance(filename,list):
        filename = filename[0]
    path, name = os.path.split(filename)
    if re.search('(_0x[a-z0-9]{32})',name):
        hash = re.findall('(_0x[a-z0-9]{32})',name)
        return True, hash
    else:
        return False, None

def copyfile(originalfile, newfile, copy=False):
    """given a file moves it to a working directory

    Parameters
    ----------
    originalfile : file
        full path to original file
    newfile : file
        full path to new file
    copy : Bool
        specifies whether to copy or symlink files
        (default=False) but only for posix systems
         
    Returns
    -------
    None
    
    """
    if os.name is 'posix' and not copy and not os.path.islink(newfile):
        #print "linking %s to %s"%(originalfile,newfile)
        os.symlink(originalfile,newfile)
    else:
        #print "copying %s to %s"%(originalfile,newfile)
        try:
            shutil.copyfile(originalfile, newfile)
        except shutil.Error:
            print "File already exists"
        
    if originalfile.endswith(".img"):
        hdrofile = originalfile[:-4] + ".hdr"
        hdrnfile = newfile[:-4] + ".hdr"
        copyfile(hdrofile, hdrnfile, copy)

def copyfiles(filelist, dest, copy=False):
    """given a file moves it to a working directory

    Parameters
    ----------
    originalfile : file
        full path to original file
    dest : path/files
        full path to destination. If it is a list of length greater
        than 1, then it assumes that these are the names of the new
        files. 
    copy : Bool
        specifies whether to copy or symlink files
        (default=False) but only for posix systems
         
    Returns
    -------
    None
    
    """
    outfiles = filename_to_list(dest)
    newfiles = []
    for i,f in enumerate(filename_to_list(filelist)):
        if len(outfiles) > 1:
            destfile = outfiles[i]
        else:
            destfile = fname_presuffix(f, newpath=outfiles[0])
        copyfile(f,destfile,copy)
        newfiles.insert(i,destfile)
    return newfiles

def filename_to_list(filename):
    """Returns a list given either a string or a list
    """
    if isinstance(filename,str):
        return [filename]
    elif isinstance(filename,list):
        return filename
    elif is_container(filename):
        return [x for x in filename]
    else:
        return None

def list_to_filename(filelist):
    """Returns a list if filelist is a list of length greater than 1, 
       otherwise returns the first element
    """
    if len(filelist) > 1:
        return filelist
    else:
        return filelist[0]

def cleandir(dir):
    """Cleans all nifti, img/hdr, txt and matfiles from dir"""
    filetypes = ['*.nii','*.nii.gz','*.txt','*.img','*.hdr','*.mat','*.json']
    for ftype in filetypes:
        for f in glob(os.path.join(dir,ftype)):
            os.remove(f)
        
def save_json(filename, data):
    """Save data to a json file
    
    Parameters
    ----------
    filename : str
        Filename to save data in.
    data : dict
        Dictionary to save in json file.

    """

    fp = file(filename, 'w')
    json.dump(data, fp, sort_keys=True, indent=4)
    fp.close()

def debuglog(inputlines,filename='/tmp/dbginputs.txt'):
    fp=open(filename,'at')
    fp.writelines(inputlines)
    fp.close()

def load_json(filename):
    """Load data from a json file

    Parameters
    ----------
    filename : str
        Filename to load data from.

    Returns
    -------
    data : dict
   
    """

    fp = file(filename, 'r')
    data = json.load(fp)
    fp.close()
    return data

def loadflat(infile, *args):
    """Load an npz file into a dict
    """
    data = np.load(infile)
    out = {}
    if args:
        outargs = np.setdiff1d(args,data.files)
        if outargs:
            raise IOError('File does not contain variables: '+str(outargs))
    for k in data.files:
        if k in args or not args:
            out[k] = [f for f in data[k].flat]
            if len(out[k])==1:
                out[k] = out[k].pop()
    return out
