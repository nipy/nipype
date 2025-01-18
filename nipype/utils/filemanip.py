# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Miscellaneous file manipulation functions
"""
import sys
import pickle
import errno
import subprocess as sp
import gzip
import hashlib
import locale
from hashlib import md5
import os
import os.path as op
import re
import shutil
import contextlib
import posixpath
from pathlib import Path
import simplejson as json
from time import sleep, time
import scipy.io as sio

from .. import logging, config, __version__ as version
from .misc import is_container

fmlogger = logging.getLogger("nipype.utils")

related_filetype_sets = [(".hdr", ".img", ".mat"), (".nii", ".mat"), (".BRIK", ".HEAD")]


# Previously a patch, not worth deprecating
path_resolve = Path.resolve


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
        file extension from fname706

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

    special_extensions = [".nii.gz", ".tar.gz", ".niml.dset"]

    pth = op.dirname(fname)
    fname = op.basename(fname)

    ext = None
    for special_ext in special_extensions:
        ext_len = len(special_ext)
        if (len(fname) > ext_len) and (fname[-ext_len:].lower() == special_ext.lower()):
            ext = fname[-ext_len:]
            fname = fname[:-ext_len]
            break
    if not ext:
        fname, ext = op.splitext(fname)

    return pth, fname, ext


def fname_presuffix(fname, prefix="", suffix="", newpath=None, use_ext=True):
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

    >>> from nipype.interfaces.base import Undefined
    >>> fname_presuffix(fname, 'pre', 'post', Undefined) == \
            fname_presuffix(fname, 'pre', 'post')
    True

    """
    pth, fname, ext = split_filename(fname)
    if not use_ext:
        ext = ""

    # No need for isdefined: bool(Undefined) evaluates to False
    if newpath:
        pth = op.abspath(newpath)
    return op.join(pth, prefix + fname + suffix + ext)


def fnames_presuffix(fnames, prefix="", suffix="", newpath=None, use_ext=True):
    """Calls fname_presuffix for a list of files."""
    return [
        fname_presuffix(fname, prefix, suffix, newpath, use_ext) for fname in fnames
    ]


def hash_rename(filename, hashvalue):
    """renames a file given original filename and hash
    and sets path to output_directory
    """
    path, name, ext = split_filename(filename)
    newfilename = f"{name}_0x{hashvalue}{ext}"
    return op.join(path, newfilename)


def check_forhash(filename):
    """checks if file has a hash in its filename"""
    if isinstance(filename, list):
        filename = filename[0]
    path, name = op.split(filename)
    if re.search("(_0x[a-z0-9]{32})", name):
        hashvalue = re.findall("(_0x[a-z0-9]{32})", name)
        return True, hashvalue
    else:
        return False, None


def hash_infile(afile, chunk_len=8192, crypto=hashlib.md5, raise_notfound=False):
    """
    Computes hash of a file using 'crypto' module

    >>> hash_infile('smri_ants_registration_settings.json')
    'f225785dfb0db9032aa5a0e4f2c730ad'

    >>> hash_infile('surf01.vtk')
    'fdf1cf359b4e346034372cdeb58f9a88'

    >>> hash_infile('spminfo')
    '0dc55e3888c98a182dab179b976dfffc'

    >>> hash_infile('fsl_motion_outliers_fd.txt')
    'defd1812c22405b1ee4431aac5bbdd73'


    """
    if not op.isfile(afile):
        if raise_notfound:
            raise RuntimeError('File "%s" not found.' % afile)
        return None

    crypto_obj = crypto()
    with open(afile, "rb") as fp:
        while True:
            data = fp.read(chunk_len)
            if not data:
                break
            crypto_obj.update(data)
    return crypto_obj.hexdigest()


def hash_timestamp(afile):
    """Computes md5 hash of the timestamp of a file"""
    md5hex = None
    if op.isfile(afile):
        md5obj = md5()
        stat = os.stat(afile)
        md5obj.update(str(stat.st_size).encode())
        md5obj.update(str(stat.st_mtime).encode())
        md5hex = md5obj.hexdigest()
    return md5hex


def _parse_mount_table(exit_code, output):
    """Parses the output of ``mount`` to produce (path, fs_type) pairs

    Separated from _generate_cifs_table to enable testing logic with real
    outputs
    """
    # Not POSIX
    if exit_code != 0:
        return []

    # Linux mount example:  sysfs on /sys type sysfs (rw,nosuid,nodev,noexec)
    #                          <PATH>^^^^      ^^^^^<FSTYPE>
    # OSX mount example:    /dev/disk2 on / (hfs, local, journaled)
    #                               <PATH>^  ^^^<FSTYPE>
    pattern = re.compile(r".*? on (/.*?) (?:type |\()([^\s,\)]+)")

    # Keep line and match for error reporting (match == None on failure)
    # Ignore empty lines
    matches = [(l, pattern.match(l)) for l in output.strip().splitlines() if l]

    # (path, fstype) tuples, sorted by path length (longest first)
    mount_info = sorted(
        (match.groups() for _, match in matches if match is not None),
        key=lambda x: len(x[0]),
        reverse=True,
    )
    cifs_paths = [path for path, fstype in mount_info if fstype.lower() == "cifs"]

    # Report failures as warnings
    for line, match in matches:
        if match is None:
            fmlogger.debug("Cannot parse mount line: '%s'", line)

    return [
        mount
        for mount in mount_info
        if any(mount[0].startswith(path) for path in cifs_paths)
    ]


def _generate_cifs_table():
    """Construct a reverse-length-ordered list of mount points that
    fall under a CIFS mount.

    This precomputation allows efficient checking for whether a given path
    would be on a CIFS filesystem.

    On systems without a ``mount`` command, or with no CIFS mounts, returns an
    empty list.
    """
    exit_code, output = sp.getstatusoutput("mount")
    return _parse_mount_table(exit_code, output)


_cifs_table = _generate_cifs_table()


def on_cifs(fname):
    """
    Checks whether a file path is on a CIFS filesystem mounted in a POSIX
    host (i.e., has the ``mount`` command).

    On Windows, Docker mounts host directories into containers through CIFS
    shares, which has support for Minshall+French symlinks, or text files that
    the CIFS driver exposes to the OS as symlinks.
    We have found that under concurrent access to the filesystem, this feature
    can result in failures to create or read recently-created symlinks,
    leading to inconsistent behavior and ``FileNotFoundError``.

    This check is written to support disabling symlinks on CIFS shares.

    """
    # Only the first match (most recent parent) counts
    for fspath, fstype in _cifs_table:
        if fname.startswith(fspath):
            return fstype == "cifs"
    return False


def copyfile(
    originalfile,
    newfile,
    copy=False,
    create_new=False,
    hashmethod=None,
    use_hardlink=False,
    copy_related_files=True,
):
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
    copy_related_files : Bool
        specifies whether to also operate on related files, as defined in
        ``related_filetype_sets``

    Returns
    -------
    None

    """
    newhash = None
    orighash = None
    fmlogger.debug(newfile)

    if create_new:
        while op.exists(newfile):
            base, fname, ext = split_filename(newfile)
            s = re.search("_c[0-9]{4,4}$", fname)
            i = 0
            if s:
                i = int(s.group()[2:]) + 1
                fname = fname[:-6] + "_c%04d" % i
            else:
                fname += "_c%04d" % i
            newfile = base + os.sep + fname + ext

    if hashmethod is None:
        hashmethod = config.get("execution", "hash_method").lower()

    # Don't try creating symlinks on CIFS
    if copy is False and on_cifs(newfile):
        copy = True

    # Existing file
    # -------------
    # Options:
    #   symlink
    #       to regular file originalfile            (keep if symlinking)
    #       to same dest as symlink originalfile    (keep if symlinking)
    #       to other file                           (unlink)
    #   regular file
    #       hard link to originalfile               (keep)
    #       copy of file (same hash)                (keep)
    #       different file (diff hash)              (unlink)
    keep = False
    if op.lexists(newfile):
        if op.islink(newfile):
            if all(
                (
                    os.readlink(newfile) == op.realpath(originalfile),
                    not use_hardlink,
                    not copy,
                )
            ):
                keep = True
        elif posixpath.samefile(newfile, originalfile):
            keep = True
        else:
            if hashmethod == "timestamp":
                hashfn = hash_timestamp
            elif hashmethod == "content":
                hashfn = hash_infile
            else:
                raise AttributeError("Unknown hash method found:", hashmethod)
            newhash = hashfn(newfile)
            fmlogger.debug(
                "File: %s already exists,%s, copy:%d", newfile, newhash, copy
            )
            orighash = hashfn(originalfile)
            keep = newhash == orighash
        if keep:
            fmlogger.debug(
                "File: %s already exists, not overwriting, copy:%d", newfile, copy
            )
        else:
            os.unlink(newfile)

    # New file
    # --------
    # use_hardlink & can_hardlink => hardlink
    # ~hardlink & ~copy & can_symlink => symlink
    # ~hardlink & ~symlink => copy
    if not keep and use_hardlink:
        try:
            fmlogger.debug("Linking File: %s->%s", newfile, originalfile)
            # Use realpath to avoid hardlinking symlinks
            os.link(op.realpath(originalfile), newfile)
        except OSError:
            use_hardlink = False  # Disable hardlink for associated files
        else:
            keep = True

    if not keep and not copy and os.name == "posix":
        try:
            fmlogger.debug("Symlinking File: %s->%s", newfile, originalfile)
            os.symlink(originalfile, newfile)
        except OSError:
            copy = True  # Disable symlink for associated files
        else:
            keep = True

    if not keep:
        try:
            fmlogger.debug("Copying File: %s->%s", newfile, originalfile)
            shutil.copyfile(originalfile, newfile)
        except shutil.Error as e:
            fmlogger.warning(str(e))

    # Associated files
    if copy_related_files:
        related_file_pairs = (
            get_related_files(f, include_this_file=False)
            for f in (originalfile, newfile)
        )
        for alt_ofile, alt_nfile in zip(*related_file_pairs):
            if op.exists(alt_ofile):
                copyfile(
                    alt_ofile,
                    alt_nfile,
                    copy,
                    hashmethod=hashmethod,
                    use_hardlink=use_hardlink,
                    copy_related_files=False,
                )

    return newfile


def get_related_files(filename, include_this_file=True):
    """Returns a list of related files, as defined in
    ``related_filetype_sets``, for a filename. (e.g., Nifti-Pair, Analyze (SPM)
    and AFNI files).

    Parameters
    ----------
    filename : str
        File name to find related filetypes of.
    include_this_file : bool
        If true, output includes the input filename.
    """
    path, name, this_type = split_filename(filename)
    related_files = [
        op.join(path, f"{name}{related_type}")
        for type_set in related_filetype_sets
        if this_type in type_set
        for related_type in type_set
        if include_this_file or related_type != this_type
    ]
    if not related_files:
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
    outfiles = ensure_list(dest)
    newfiles = []
    for i, f in enumerate(ensure_list(filelist)):
        if isinstance(f, list):
            newfiles.insert(i, copyfiles(f, dest, copy=copy, create_new=create_new))
        else:
            if len(outfiles) > 1:
                destfile = outfiles[i]
            else:
                destfile = fname_presuffix(f, newpath=outfiles[0])
            destfile = copyfile(f, destfile, copy, create_new=create_new)
            newfiles.insert(i, destfile)
    return newfiles


def ensure_list(filename):
    """Returns a list given either a string or a list"""
    if isinstance(filename, (str, bytes)):
        return [filename]
    elif isinstance(filename, list):
        return filename
    elif is_container(filename):
        return list(filename)
    else:
        return None


def simplify_list(filelist):
    """Returns a list if filelist is a list of length greater than 1,
    otherwise returns the first element
    """
    if len(filelist) > 1:
        return filelist
    else:
        return filelist[0]


filename_to_list = ensure_list
list_to_filename = simplify_list


def check_depends(targets, dependencies):
    """Return true if all targets exist and are newer than all dependencies.

    An OSError will be raised if there are missing dependencies.
    """
    tgts = ensure_list(targets)
    deps = ensure_list(dependencies)
    return all(map(op.exists, tgts)) and min(map(op.getmtime, tgts)) > max(
        list(map(op.getmtime, deps)) + [0]
    )


def save_json(filename, data):
    """Save data to a json file

    Parameters
    ----------
    filename : str
        Filename to save data in.
    data : dict
        Dictionary to save in json file.

    """
    mode = "w"
    with open(filename, mode) as fp:
        json.dump(data, fp, sort_keys=True, indent=4)


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

    with open(filename) as fp:
        data = json.load(fp)
    return data


def loadcrash(infile, *args):
    if infile.endswith(("pkl", "pklz")):
        return loadpkl(infile)
    else:
        raise ValueError("Only pickled crashfiles are supported")


def loadpkl(infile):
    """Load a zipped or plain cPickled file."""
    infile = Path(infile)
    fmlogger.debug("Loading pkl: %s", infile)
    pklopen = gzip.open if infile.suffix == ".pklz" else open

    t = time()
    timeout = float(config.get("execution", "job_finished_timeout"))
    timed_out = True
    while (time() - t) < timeout:
        if infile.exists():
            timed_out = False
            break
        fmlogger.debug(f"'{infile}' missing; waiting 2s")
        sleep(2)
    if timed_out:
        error_message = (
            "Result file {} expected, but "
            "does not exist after ({}) "
            "seconds.".format(infile, timeout)
        )
        raise OSError(error_message)

    with pklopen(str(infile), "rb") as pkl_file:
        pkl_contents = pkl_file.read()

    pkl_metadata = None

    # Look if pkl file contains version metadata
    idx = pkl_contents.find(b"\n")
    if idx >= 0:
        try:
            pkl_metadata = json.loads(pkl_contents[:idx])
        except (UnicodeDecodeError, json.JSONDecodeError):
            # Could not get version info
            pass
        else:
            # On success, skip JSON metadata
            pkl_contents = pkl_contents[idx + 1 :]

    # Pickle files may contain relative paths that must be resolved relative
    # to the working directory, so use indirectory while attempting to load
    unpkl = None
    try:
        with indirectory(infile.parent):
            unpkl = pickle.loads(pkl_contents)
    except UnicodeDecodeError:
        # Was this pickle created with Python 2.x?
        with indirectory(infile.parent):
            unpkl = pickle.loads(pkl_contents, fix_imports=True, encoding="utf-8")
        fmlogger.info("Successfully loaded pkl in compatibility mode.")
    # Unpickling problems
    except Exception as e:
        if pkl_metadata and "version" in pkl_metadata:
            if pkl_metadata["version"] != version:
                fmlogger.error(
                    """\
Attempted to open a results file generated by Nipype version %s, \
with an incompatible Nipype version (%s)""",
                    pkl_metadata["version"],
                    version,
                )
                raise e
        fmlogger.warning(
            """\
No metadata was found in the pkl file. Make sure you are currently using \
the same Nipype version from the generated pkl."""
        )
        raise e

    if unpkl is None:
        raise ValueError("Loading %s resulted in None." % infile)

    return unpkl


def crash2txt(filename, record):
    """Write out plain text crash file"""
    with open(filename, "w") as fp:
        if "node" in record:
            node = record["node"]
            fp.write(f"Node: {node.fullname}\n")
            fp.write(f"Working directory: {node.output_dir()}\n")
            fp.write("\n")
            fp.write(f"Node inputs:\n{node.inputs}\n")
        fp.write("".join(record["traceback"]))


def read_stream(stream, logger=None, encoding=None):
    """
    Robustly reads a stream, sending a warning to a logger
    if some decoding error was raised.

    >>> read_stream(bytearray([65, 0xc7, 65, 10, 66]))  # doctest: +ELLIPSIS
    ['A...A', 'B']


    """
    default_encoding = encoding or locale.getpreferredencoding(do_setlocale=False)
    logger = logger or fmlogger
    try:
        out = stream.decode(default_encoding)
    except UnicodeDecodeError as err:
        out = stream.decode(default_encoding, errors="replace")
        logger.warning("Error decoding string: %s", err)
    return out.splitlines()


def savepkl(filename, record, versioning=False):
    from io import BytesIO

    with BytesIO() as f:
        if versioning:
            metadata = json.dumps({"version": version})
            f.write(metadata.encode("utf-8"))
            f.write(b"\n")
        pickle.dump(record, f)
        content = f.getvalue()

    pkl_open = gzip.open if filename.endswith(".pklz") else open
    tmpfile = filename + ".tmp"
    with pkl_open(tmpfile, "wb") as pkl_file:
        pkl_file.write(content)
    for _ in range(5):
        try:
            os.rename(tmpfile, filename)
            break
        except FileNotFoundError as e:
            last_e = e
            fmlogger.debug(str(e))
            sleep(2)
    else:
        raise last_e


rst_levels = ["=", "-", "~", "+"]


def write_rst_header(header, level=0):
    return "\n".join((header, "".join([rst_levels[level] for _ in header]))) + "\n\n"


def write_rst_list(items, prefix=""):
    return "\n".join(f"{prefix} {item}" for item in ensure_list(items)) + "\n\n"


def write_rst_dict(info, prefix=""):
    return "\n".join(f"{prefix}* {k} : {v}" for k, v in sorted(info.items())) + "\n\n"


def dist_is_editable(dist):
    """Is distribution an editable install?

    Parameters
    ----------
    dist : string
        Package name

    # Borrowed from `pip`'s' API
    """
    for path_item in sys.path:
        egg_link = op.join(path_item, dist + ".egg-link")
        if op.isfile(egg_link):
            return True
    return False


def emptydirs(path, noexist_ok=False):
    """
    Empty an existing directory, without deleting it. Do not
    raise error if the path does not exist and noexist_ok is True.

    Parameters
    ----------
    path : directory that should be empty

    """
    fmlogger.debug("Removing contents of %s", path)

    if noexist_ok and not op.exists(path):
        return True

    if op.isfile(path):
        raise OSError('path "%s" should be a directory' % path)

    try:
        shutil.rmtree(path)
    except OSError as ex:
        elcont = [
            Path(root) / file
            for root, _, files in os.walk(path)
            for file in files
            if not file.startswith(".nfs")
        ]
        if ex.errno in [errno.ENOTEMPTY, errno.EBUSY] and not elcont:
            fmlogger.warning(
                "An exception was raised trying to remove old %s, but the path"
                " seems empty. Is it an NFS mount?. Passing the exception.",
                path,
            )
        elif ex.errno == errno.ENOTEMPTY and elcont:
            fmlogger.debug("Folder %s contents (%d items).", path, len(elcont))
            raise ex
        else:
            raise ex

    os.makedirs(path, exist_ok=True)


def silentrm(filename):
    """
    Equivalent to ``rm -f``, returns ``False`` if the file did not
    exist.

    Parameters
    ----------

    filename : str
        file to be deleted

    """
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise
        return False
    return True


def which(cmd, env=None, pathext=None):
    """
    Return the path to an executable which would be run if the given
    cmd was called. If no cmd would be called, return ``None``.

    Code for Python < 3.3 is based on a code snippet from
    http://orip.org/2009/08/python-checking-if-executable-exists-in.html

    """

    if pathext is None:
        pathext = os.getenv("PATHEXT", "").split(os.pathsep)
        pathext.insert(0, "")

    path = os.getenv("PATH", os.defpath)
    if env and "PATH" in env:
        path = env.get("PATH")

    for ext in pathext:
        filename = shutil.which(cmd + ext, path=path)
        if filename:
            return filename
    return None


def get_dependencies(name, environ):
    """Return library dependencies of a dynamically linked executable

    Uses otool on darwin, ldd on linux. Currently doesn't support windows.

    """
    command = None
    if sys.platform == "darwin":
        command = "otool -L `which %s`" % name
    elif "linux" in sys.platform:
        command = "ldd `which %s`" % name
    else:
        return "Platform %s not supported" % sys.platform

    deps = None
    try:
        proc = sp.Popen(
            command, stdout=sp.PIPE, stderr=sp.PIPE, shell=True, env=environ
        )
        o, e = proc.communicate()
        deps = o.rstrip()
    except Exception as ex:
        deps = f"{command!r} failed"
        fmlogger.warning(f"Could not get dependencies of {name}s. Error:\n{ex}")
    return deps


def canonicalize_env(env):
    """Windows requires that environment be dicts with str as keys and values
    This function converts any unicode entries for Windows only, returning the
    dictionary untouched in other environments.

    Parameters
    ----------
    env : dict
        environment dictionary with unicode or bytes keys and values

    Returns
    -------
    env : dict
        Windows: environment dictionary with str keys and values
        Other: untouched input ``env``
    """
    if os.name != "nt":
        return env

    out_env = {}
    for key, val in env.items():
        if not isinstance(key, str):
            key = key.decode("utf-8")
        if not isinstance(val, str):
            val = val.decode("utf-8")
        out_env[key] = val
    return out_env


def relpath(path, start=None):
    """Return a relative version of a path"""

    try:
        return op.relpath(path, start)
    except AttributeError:
        pass

    if start is None:
        start = os.curdir
    if not path:
        raise ValueError("no path specified")
    start_list = op.abspath(start).split(op.sep)
    path_list = op.abspath(path).split(op.sep)
    if start_list[0].lower() != path_list[0].lower():
        unc_path, rest = op.splitunc(path)
        unc_start, rest = op.splitunc(start)
        if bool(unc_path) ^ bool(unc_start):
            raise ValueError(f"Cannot mix UNC and non-UNC paths ({path} and {start})")
        else:
            raise ValueError(
                f"path is on drive {path_list[0]}, start on drive {start_list[0]}"
            )
    # Work out how much of the filepath is shared by start and path.
    for i in range(min(len(start_list), len(path_list))):
        if start_list[i].lower() != path_list[i].lower():
            break
    else:
        i += 1

    rel_list = [op.pardir] * (len(start_list) - i) + path_list[i:]
    if not rel_list:
        return os.curdir
    return op.join(*rel_list)


@contextlib.contextmanager
def indirectory(path):
    cwd = os.getcwd()
    os.chdir(str(path))
    try:
        yield
    finally:
        os.chdir(cwd)


def load_spm_mat(spm_mat_file, **kwargs):
    try:
        mat = sio.loadmat(spm_mat_file, **kwargs)
    except NotImplementedError:
        import h5py
        import numpy as np

        mat = dict(SPM=np.array([[sio.matlab.mat_struct()]]))

        # Get Vbeta, Vcon, and Vspm file names
        with h5py.File(spm_mat_file, "r") as h5file:
            fnames = dict()
            try:
                fnames["Vbeta"] = [
                    u"".join(chr(c[0]) for c in h5file[obj_ref[0]])
                    for obj_ref in h5file["SPM"]["Vbeta"]["fname"]
                ]
            except Exception:
                fnames["Vbeta"] = []
            for contr_type in ["Vcon", "Vspm"]:
                try:
                    fnames[contr_type] = [
                        u"".join(chr(c[0]) for c in h5file[obj_ref[0]]["fname"])
                        for obj_ref in h5file["SPM"]["xCon"][contr_type]
                    ]
                except Exception:
                    fnames[contr_type] = []

        # Structure Vbeta as returned by scipy.io.loadmat
        obj_list = []
        for i in range(len(fnames["Vbeta"])):
            obj = sio.matlab.mat_struct()
            setattr(obj, "fname", np.array([fnames["Vbeta"][i]]))
            obj_list.append(obj)
        if len(obj_list) > 0:
            setattr(mat["SPM"][0, 0], "Vbeta", np.array([obj_list]))
        else:
            setattr(mat["SPM"][0, 0], "Vbeta", np.empty((0, 0), dtype=object))

        # Structure Vcon and Vspm as returned by scipy.io.loadmat
        obj_list = []
        for i in range(len(fnames["Vcon"])):
            obj = sio.matlab.mat_struct()
            for contr_type in ["Vcon", "Vspm"]:
                temp = sio.matlab.mat_struct()
                setattr(temp, "fname", np.array([fnames[contr_type][i]]))
                setattr(obj, contr_type, np.array([[temp]]))
            obj_list.append(obj)
        if len(obj_list) > 0:
            setattr(mat["SPM"][0, 0], "xCon", np.array([obj_list]))
        else:
            setattr(mat["SPM"][0, 0], "xCon", np.empty((0, 0), dtype=object))

    return mat
