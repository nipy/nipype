""" Utility functions.

fixme: I don't like random collections of utility functions! Where should
this go?

"""


# Standard library imports.
import os
from os.path import basename, dirname, isdir, splitdrive, splitext
from zipfile import is_zipfile, ZipFile


def get_module_name(filename):
    """ Get the fully qualified module name for a filename.

    For example, if the filename is

    /enthought/envisage/core/core_plugin_definition.py

    this method would return

    enthought.envisage.core.core_plugin_definition

    """

    if os.path.exists(filename):
        # Get the name of the module minus the '.py'
        module, ext = os.path.splitext(os.path.basename(filename))

        # Start with the actual module name.
        module_path = [module]

        # If the directory is a Python package then add it to the module path.
        #return self.is_folder and '__init__.py' in os.listdir(self.path)

        parent = dirname(filename)
        while isdir(parent) and '__init__.py' in os.listdir(parent):
            bname = basename(parent)
            module_path.insert(0, splitext(bname)[0])
            parent = dirname(parent)

        module_name = '.'.join(module_path)

    # If the file does not exist then it might be a zip file path.
    else:
        module_name = get_module_name_from_zip(filename)

    return module_name

# fixme: WIP
def get_module_name_from_zip(filename):

    # first, find the zip file in the path
    filepath = filename
    zippath = None
    while not is_zipfile(filepath) and \
              splitdrive(filepath)[1] != '\\' \
              and splitdrive(filepath)[1] != '/':
        filepath, tail = os.path.split(filepath)
        if zippath is not None:
            zippath = tail + '/' + zippath
        else:
            zippath = tail

    if not is_zipfile(filepath):
        return None

    # if the split left a preceding slash on the zippath then remove
    # it
    if zippath.startswith('\\') or zippath.startswith('/'):
        zippath = zippath[1:]

    # replace any backwards slashes with forward slashes
    zippath = zippath.replace('\\', '/')

    # Get the name of the module minus the '.py'
    module, ext = splitext(basename(zippath))

    # Start with the actual module name.
    module_path = [module]

    # to get the module name, we walk through the zippath until we
    # find a parent directory that does NOT have a __init__.py file
    z = ZipFile(filepath)

    parentpath = dirname(zippath)
    while path_exists_in_zip(z, parentpath + '/__init__.py'):
        module_path.insert(0, basename(parentpath))
        parentpath = dirname(parentpath)

    z.close()

    return '.'.join(module_path)

# fixme: WIP
def path_exists_in_zip(zfile, path):

    try:
        zfile.getinfo(path)
        exists = True
    except:
        exists = False

    return exists

# fixme: WIP
def is_zip_path(path):
    """ Returns True if the path refers to a zip file. """

    filepath = path
    while not is_zipfile(filepath) and \
              splitdrive(filepath)[1] != '\\' \
              and splitdrive(filepath)[1] != '/':
        filepath = dirname(filepath)

    return is_zipfile(filepath)

# fixme: WIP
def get_zip_path(filename):
    """ Returns the path to the zip file contained in the filename.

    fixme: An example here would help.

    """

    filepath = filename
    zippath = None
    while not is_zipfile(filepath) and \
              splitdrive(filepath)[1] != '\\' \
              and splitdrive(filepath)[1] != '/':
        filepath, tail = os.path.split(filepath)
        if zippath is not None:
            zippath = tail + '/' + zippath
        else:
            zippath = tail

    return zippath

#### EOF ######################################################################
