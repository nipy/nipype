#------------------------------------------------------------------------------
# Copyright (c) 2005, Enthought, Inc.
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in enthought/LICENSE.txt and may be redistributed only
# under the conditions described in the aforementioned license.  The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
# Thanks for using Enthought open source!
#
# Author: Enthought, Inc.
# Description: <Enthought util package component>
#------------------------------------------------------------------------------
""" Utility functions for managing and finding resources (ie. images/files etc).

    get_path :           Returns the absolute path of a class or instance

    create_unique_name : Creates a name with a given prefix that is not in a
                         given list of existing names. The separator between the
                         prefix and the rest of the name can also be specified
                         (default is a '_')

    find_resource:       Given a setuptools project specification string
                         ('MyProject>=2.1') and a partial path leading from the
                         projects base directory to the desired resource, will
                         return either an opened file object or, if specified, a
                         full path to the resource.
"""


# Standard library imports.
import inspect, os, sys
from distutils.sysconfig import get_python_lib


def get_path(path):
    """ Returns an absolute path for the specified path.

    'path' can be a string, class or instance.

    """

    if type(path) is not str:
        # Is this a class or an instance?
        if inspect.isclass(path):
            klass = path

        else:
            klass = path.__class__

        # Get the name of the module that the class was loaded from.
        module_name = klass.__module__

        # Look the module up.
        module = sys.modules[module_name]

        if module_name == '__main__':
            dirs = [os.path.dirname(sys.argv[0]), os.getcwd()]
            for d in dirs:
                if os.path.exists(d):
                    path = d
                    break
        else:
            # Get the path to the module.
            path = os.path.dirname(module.__file__)

    return path

def create_unique_name(prefix, names, separator='_'):
    """ Creates a name starting with 'prefix' that is not in 'names'. """

    i = 1

    name = prefix
    while name in names:
        name = prefix + separator + str(i)
        i += 1

    return name

def find_resource(project, resource_path, alt_path=None, return_path=False):
    """ Returns a file object or file path pointing to the desired resource.

    Parameters
    ----------
    project : string
        The name of the project to look for the resource in. Can be the name or
        a requirement string. Ex: 'MyProject', 'MyProject>1.0', 'MyProject==1.1'
    resource_path : string
        The path to the file from inside the package. If the file desired is
        MyProject/data/image.jpg, resource_path would be 'data/image.jpg'.
    alt_path : string
        The path to the resource relative to the location of the application's
        top-level script (the one with __main__). If this function is called in
        code/scripts/myscript.py and the resource is code/data/image.jpg, the
        alt_path would be '../data/image.jpg'. This path is only used if the
        resource cannot be found using setuptools.
    return_path : bool
        Determines whether the function should return a file object or a full
        path to the resource.

    Returns
    -------
    file : file object or file path
        A file object containing the resource. If return_path is True, 'file'
        will be the full path to the resource. If the file is not found or
        cannot be opened, None is returned.

    Description
    -----------
    This function will find a desired resource file and return an opened file
    object. The main method of finding the resource uses the pkg_resources
    resource_stream method, which searches your working set for the installed
    project specified and appends the resource_path given to the project
    path, leading it to the file. If setuptools is not installed or it cannot
    find/open the resource, find_resource will use the sys.path[0] to find the
    resource if alt_path is defined.
    """

    try:
        # Get the image using the pkg_resources resource_stream module, which
        # will find the file by getting the Chaco install path and appending the
        # image path. This method works in all cases as long as setuptools is
        # installed. If setuptools isn't installed, the backup sys.path[0]
        # method is used.
        from pkg_resources import resource_stream, working_set, Requirement

        # Get a requirement for the project
        requirement = Requirement.parse(project)

        if return_path:
            dist = working_set.find(requirement)
            full_path = os.path.join(dist.location, resource_path)

            # If the path exists, return it
            if os.path.exists(full_path):
                return full_path
            else:
                raise
        else:
            return resource_stream(requirement, resource_path)

    except:
        # Setuptools was either not installed, or it failed to find the file.
        # First check to see if the package was installed using egginst by
        # looking for the file at: site-packages\\resouce_path
        full_path = os.path.join(get_python_lib(), resource_path)
        if os.path.exists(full_path):
            if return_path:
                return full_path
            else:
                return open(full_path, 'rb')

        # Get the image using sys.path[0], which is the directory that the
        # running script lives in. The path to the file is then constructed by
        # navigating from the script's location. This method only works if this
        # script is called directly from the command line using
        # 'python %SOMEPATH%/<script>'
        if alt_path is None:
            return
        if return_path:
            return os.path.join(sys.path[0], alt_path)

        # Try to open the file, return None on exception
        try:
            return open(os.path.join(sys.path[0], alt_path), 'rb')
        except:
            return


def store_resource(project, resource_path, filename):
    """ Store the content of a resource, given by the name of the projet
        and the path (relative to the root of the project), into a newly
        created file.

        The first two arguments (project and resource_path) are the same
        as for the function find_resource in this module.  The third
        argument (filename) is the name of the file which will be created,
        or overwritten if it already exists.
        The return value in always None.
    """
    fi = find_resource(project, resource_path)
    if fi is None:
        raise RuntimeError('Resource not found for project "%s": %s' %
                           (project, resource_path))

    fo = open(filename, 'wb')
    fo.write(fi.read())
    fo.close()

    fi.close()


#### EOF ######################################################################
