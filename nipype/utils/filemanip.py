"""Miscellaneous file manipulation functions

"""
import os, re
import hashlib
import shutil

def fname_presuffix(fname, prefix='', suffix='', newpath=None, use_ext=True):
    pth, fname = os.path.split(fname)
    fname, ext = os.path.splitext(fname)
    if not use_ext:
        ext = ''
    if newpath is not None:
        pth = os.path.abspath(newpath)
    return os.path.join(pth, prefix+fname+suffix+ext)


def fnames_presuffix(fnames, prefix='', suffix='', newpath=None,use_ext=True):
    f2 = []
    for fname in fnames:
        f2.append(fname_presuffix(fname, prefix, suffix, newpath, use_ext))
    return f2

def md5file(filename, excludeline="", includeline=""):
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
    if type(filename) == type(list):
        filename = filename[0]
    path, name = os.path.split(filename)

    if re.search('(_0x[a-z0-9]{32})',name):
        hash = re.findall('(_0x[a-z0-9]{32})',name)
        return True, hash
    else:
        return False, None

def copyfile(originalfile, newfile,copy=False):
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
    None
    
    """
    if os.name is 'posix' and not copy:
        os.symlink(originalfile,newfile)
    else:
        shutil.copyfile(originalfile, newfile)

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
    symlink : Bool
        specifies whether to copy or symlink files
        (default=True) but only for posix systems
         
    Returns
    -------
    None
    
    """
    outfiles = filename_to_list(dest)
    for i,f in enumerate(filename_to_list(filelist)):
        if len(outfiles) > 1:
            newfile = outfiles[i]
        else:
            newfile = fname_presuffix(f, newpath=outfiles[0])
        copyfile(f,newfile,copy)


def filename_to_list(filename):
    if type(filename) == type(''):
        return [filename]
    elif type(filename) == type([]):
        return filename
    else:
        return None

def list_to_filename(filelist):
    if len(filelist) == 1:
        return filelist[0]
    else:
        return filelist
