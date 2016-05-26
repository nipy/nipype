# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Miscellaneous file manipulation functions

"""

from future import standard_library
standard_library.install_aliases()

import pickle
import gzip
import hashlib
from hashlib import md5
import simplejson
import os
import re
import shutil
import posixpath

import numpy as np

from .misc import is_container
from ..external.six import string_types
from ..interfaces.traits_extension import isdefined

from .. import logging, config
fmlogger = logging.getLogger("filemanip")


class FileNotFoundError(Exception):
    pass


def split_filename(fname):
    """Split a filename into parts: path, base filename and extension.

    Parameters
    ----------
    fname : str
        file or path name

    Returns
    -------
    pth : str
        base path from fname
    fname : str
        filename from fname, without extension
    ext : str
        file extension from fname

    Examples
    --------
    >>> from nipype.utils.filemanip import split_filename
    >>> pth, fname, ext = split_filename('/home/data/subject.nii.gz')
    >>> pth
    '/home/data'

    >>> fname
    'subject'

    >>> ext
    '.nii.gz'

    """

    special_extensions = [".nii.gz", ".tar.gz"]

    pth = os.path.dirname(fname)
    fname = os.path.basename(fname)

    ext = None
    for special_ext in special_extensions:
        ext_len = len(special_ext)
        if (len(fname) > ext_len) and \
                (fname[-ext_len:].lower() == special_ext.lower()):
            ext = fname[-ext_len:]
            fname = fname[:-ext_len]
            break
    if not ext:
        fname, ext = os.path.splitext(fname)

    return pth, fname, ext


def fname_presuffix(fname, prefix='', suffix='', newpath=None, use_ext=True):
    """Manipulates path and name of input filename

    Parameters
    ----------
    fname : string
        A filename (may or may not include path)
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
    pth, fname, ext = split_filename(fname)
    if not use_ext:
        ext = ''
    if newpath and isdefined(newpath):
        pth = os.path.abspath(newpath)
    return os.path.join(pth, prefix + fname + suffix + ext)


def fnames_presuffix(fnames, prefix='', suffix='', newpath=None, use_ext=True):
    """Calls fname_presuffix for a list of files.
    """
    f2 = []
    for fname in fnames:
        f2.append(fname_presuffix(fname, prefix, suffix, newpath, use_ext))
    return f2


def hash_rename(filename, hashvalue):
    """renames a file given original filename and hash
    and sets path to output_directory
    """
    path, name, ext = split_filename(filename)
    newfilename = ''.join((name, '_0x', hashvalue, ext))
    return os.path.join(path, newfilename)


def check_forhash(filename):
    """checks if file has a hash in its filename"""
    if isinstance(filename, list):
        filename = filename[0]
    path, name = os.path.split(filename)
    if re.search('(_0x[a-z0-9]{32})', name):
        hashvalue = re.findall('(_0x[a-z0-9]{32})', name)
        return True, hashvalue
    else:
        return False, None


def hash_infile(afile, chunk_len=8192, crypto=hashlib.md5):
    """ Computes hash of a file using 'crypto' module"""
    hex = None
    if os.path.isfile(afile):
        crypto_obj = crypto()
        with open(afile, 'rb') as fp:
            while True:
                data = fp.read(chunk_len)
                if not data:
                    break
                crypto_obj.update(data)
        hex = crypto_obj.hexdigest()
    return hex


def hash_timestamp(afile):
    """ Computes md5 hash of the timestamp of a file """
    md5hex = None
    if os.path.isfile(afile):
        md5obj = md5()
        stat = os.stat(afile)
        md5obj.update(str(stat.st_size).encode())
        md5obj.update(str(stat.st_mtime).encode())
        md5hex = md5obj.hexdigest()
    return md5hex


def copyfile(originalfile, newfile, copy=False, create_new=False,
             hashmethod=None, use_hardlink=False):
    """Copy or link ``originalfile`` to ``newfile``.

    If ``use_hardlink`` is True, and the file can be hard-linked, then a
    link is created, instead of copying the file.

    If a hard link is not created and ``copy`` is False, then a symbolic
    link is created.

    Parameters
    ----------
    originalfile : str
        full path to original file
    newfile : str
        full path to new file
    copy : Bool
        specifies whether to copy or symlink files
        (default=False) but only for POSIX systems
    use_hardlink : Bool
        specifies whether to hard-link files, when able
        (Default=False), taking precedence over copy

    Returns
    -------
    None

    """
    newhash = None
    orighash = None
    fmlogger.debug(newfile)

    if create_new:
        while os.path.exists(newfile):
            base, fname, ext = split_filename(newfile)
            s = re.search('_c[0-9]{4,4}$', fname)
            i = 0
            if s:
                i = int(s.group()[2:]) + 1
                fname = fname[:-6] + "_c%04d" % i
            else:
                fname += "_c%04d" % i
            newfile = base + os.sep + fname + ext

    if hashmethod is None:
        hashmethod = config.get('execution', 'hash_method').lower()

    # Existing file
    # -------------
    # Options:
    #   symlink
    #       to originalfile             (keep if not (use_hardlink or copy))
    #       to other file               (unlink)
    #   regular file
    #       hard link to originalfile   (keep)
    #       copy of file (same hash)    (keep)
    #       different file (diff hash)  (unlink)
    keep = False
    if os.path.lexists(newfile):
        if os.path.islink(newfile):
            if all(os.path.readlink(newfile) == originalfile, not use_hardlink,
                   not copy):
                keep = True
        elif posixpath.samefile(newfile, originalfile):
            keep = True
        else:
            if hashmethod == 'timestamp':
                hashfn = hash_timestamp
            elif hashmethod == 'content':
                hashfn = hash_infile
            newhash = hashfn(newfile)
            fmlogger.debug("File: %s already exists,%s, copy:%d" %
                           (newfile, newhash, copy))
            orighash = hashfn(originalfile)
            keep = newhash == orighash
        if keep:
            fmlogger.debug("File: %s already exists, not overwriting, copy:%d"
                           % (newfile, copy))
        else:
            os.unlink(newfile)

    # New file
    # --------
    # use_hardlink & can_hardlink => hardlink
    # ~hardlink & ~copy & can_symlink => symlink
    # ~hardlink & ~symlink => copy
    if not keep and use_hardlink:
        try:
            fmlogger.debug("Linking File: %s->%s" % (newfile, originalfile))
            # Use realpath to avoid hardlinking symlinks
            os.link(os.path.realpath(originalfile), newfile)
        except OSError:
            use_hardlink = False  # Disable hardlink for associated files
        else:
            keep = True

    if not keep and not copy and os.name == 'posix':
        try:
            fmlogger.debug("Symlinking File: %s->%s" % (newfile, originalfile))
            os.symlink(originalfile, newfile)
        except OSError:
            copy = True  # Disable symlink for associated files
        else:
            keep = True

    if not keep:
        try:
            fmlogger.debug("Copying File: %s->%s" % (newfile, originalfile))
            shutil.copyfile(originalfile, newfile)
        except shutil.Error as e:
            fmlogger.warn(e.message)

    # Associated files
    if originalfile.endswith(".img"):
        hdrofile = originalfile[:-4] + ".hdr"
        hdrnfile = newfile[:-4] + ".hdr"
        matofile = originalfile[:-4] + ".mat"
        if os.path.exists(matofile):
            matnfile = newfile[:-4] + ".mat"
            copyfile(matofile, matnfile, copy, hashmethod=hashmethod,
                     use_hardlink=use_hardlink)
        copyfile(hdrofile, hdrnfile, copy, hashmethod=hashmethod,
                 use_hardlink=use_hardlink)
    elif originalfile.endswith(".BRIK"):
        hdrofile = originalfile[:-5] + ".HEAD"
        hdrnfile = newfile[:-5] + ".HEAD"
        copyfile(hdrofile, hdrnfile, copy, hashmethod=hashmethod,
                 use_hardlink=use_hardlink)

    return newfile


def get_related_files(filename):
    """Returns a list of related files for Nifti-Pair, Analyze (SPM) and AFNI
       files
    """
    related_files = []
    if filename.endswith(".img") or filename.endswith(".hdr"):
        path, name, ext = split_filename(filename)
        for ext in ['.hdr', '.img', '.mat']:
            related_files.append(os.path.join(path, name + ext))
    elif filename.endswith(".BRIK") or filename.endswith(".HEAD"):
        path, name, ext = split_filename(filename)
        for ext in ['.BRIK', '.HEAD']:
            related_files.append(os.path.join(path, name + ext))
    if not len(related_files):
        related_files = [filename]
    return related_files


def copyfiles(filelist, dest, copy=False, create_new=False):
    """Copy or symlink files in ``filelist`` to ``dest`` directory.

    Parameters
    ----------
    filelist : list
        List of files to copy.
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
    for i, f in enumerate(filename_to_list(filelist)):
        if isinstance(f, list):
            newfiles.insert(i, copyfiles(f, dest, copy=copy,
                                         create_new=create_new))
        else:
            if len(outfiles) > 1:
                destfile = outfiles[i]
            else:
                destfile = fname_presuffix(f, newpath=outfiles[0])
            destfile = copyfile(f, destfile, copy, create_new=create_new)
            newfiles.insert(i, destfile)
    return newfiles


def filename_to_list(filename):
    """Returns a list given either a string or a list
    """
    if isinstance(filename, (str, string_types)):
        return [filename]
    elif isinstance(filename, list):
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


def save_json(filename, data):
    """Save data to a json file

    Parameters
    ----------
    filename : str
        Filename to save data in.
    data : dict
        Dictionary to save in json file.

    """

    with open(filename, 'w') as fp:
        simplejson.dump(data, fp, sort_keys=True, indent=4)


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

    with open(filename, 'r') as fp:
        data = simplejson.load(fp)
    return data


def loadcrash(infile, *args):
    if '.pkl' in infile:
        return loadpkl(infile)
    elif '.npz' in infile:
        DeprecationWarning(('npz files will be deprecated in the next '
                            'release. you can use numpy to open them.'))
        data = np.load(infile)
        out = {}
        for k in data.files:
            out[k] = [f for f in data[k].flat]
            if len(out[k]) == 1:
                out[k] = out[k].pop()
        return out
    else:
        raise ValueError('Only pickled crashfiles are supported')


def loadpkl(infile):
    """Load a zipped or plain cPickled file
    """
    if infile.endswith('pklz'):
        pkl_file = gzip.open(infile, 'rb')
    else:
        pkl_file = open(infile)
    return pickle.load(pkl_file)


def savepkl(filename, record):
    if filename.endswith('pklz'):
        pkl_file = gzip.open(filename, 'wb')
    else:
        pkl_file = open(filename, 'wb')
    pickle.dump(record, pkl_file)
    pkl_file.close()

rst_levels = ['=', '-', '~', '+']


def write_rst_header(header, level=0):
    return '\n'.join((header, ''.join([rst_levels[level]
                                       for _ in header]))) + '\n\n'


def write_rst_list(items, prefix=''):
    out = []
    for item in items:
        out.append(prefix + ' ' + str(item))
    return '\n'.join(out) + '\n\n'


def write_rst_dict(info, prefix=''):
    out = []
    for key, value in sorted(info.items()):
        out.append(prefix + '* ' + key + ' : ' + str(value))
    return '\n'.join(out) + '\n\n'
