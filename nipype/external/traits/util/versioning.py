"""
This module defines functions for extracting/defining version information for
packages.  Functions for retrieving version/branch info from SVN, as well as
those for formatting version strings and finding packages with predefined
version info are defined in this module.
"""
# author: Rick Ratzel
# created: 8/9/05


import sys
import os
from os import path
import re
import glob


def get_all_component_versions() :
    """
    returns a list of tuples containing (<module name>, <version string>,
    <branch name or None if trunk>) for each package containing an appropriate
    <module>_version.py file in the package dir.  The modules checked are those
    present in sys.modules
    """
    retList = []
    #
    # check each module which is in sys.modules that has a <mod>_version.py file
    #
    for modName in get_all_versioned_modules() :
        #
        # import the module to get the version info
        #
        mod = __import__( "%s.%s_version" % (modName, modName),
                          globals(), locals(),
                          ["%s_version" % modName] )
        #
        # extract the version string...check two names
        # ...if no version was defined, create one using other info if present
        # in the version file
        #
        if( hasattr( mod, "%s_version" % modName ) ) :
            verString = getattr( mod, "%s_version" % modName )
        elif( hasattr( mod, "version" ) ) :
            verString = getattr( mod, "version" )
        else :
            if( hasattr( mod, "major" ) and hasattr( mod, "minor" ) and
                hasattr( mod, "micro" ) and hasattr( mod, "release_level" ) and
                hasattr( mod, "revision" ) ) :
                verString = create_version_string(
                    getattr( mod, "major" ), getattr( mod, "minor" ),
                    getattr( mod, "micro" ), getattr( mod, "release_level"),
                    getattr( mod, "revision" ), mod.__file__ )
            else :
                verString = None
        #
        # extract the branch name if defined, else try to find it...set to None
        # if not a branch
        #
        if( hasattr( mod, "branch" ) ) :
            branch = getattr( mod, "branch" )
        else :
            branch = get_svn_branch( path.dirname( mod.__file__ ) )

        retList.append( (modName, verString, branch) )
    #
    # finally, include the Python version info
    #
    retList.append( (path.basename( sys.executable ), sys.version, None) )

    return retList


def create_version_string( major, minor, micro, release_level, revision,
                           version_file=None ) :
    """ Return a string representing the current version, based on various
    attributes of the intended release """

    if release_level:
        rl = "_" + release_level
    else:
        rl = ""

    verString = "%d.%d.%d%s" % (major, minor, micro, rl)

    #
    # if the revision had not been supplied by a build, try to find it now
    # ...version_file is used simply as a way to get a directory in the package
    # which may have an .svn/entries file for extracting version info
    #
    if( (revision is None) and not( version_file is None ) ) :
        revision = get_svn_revision( path.dirname( version_file ) )
        verString += "_%s" % revision

    return verString


def get_svn_revision( dir_path ) :
    """
    return the SVN revision number for the specified dir.  This is used when a
    revision has not been supplied by a build.

    """

    revision = None

    # For SVN prior to v1.4, the revision number could be pulled from the
    # entries file using a regular expression.
    entries = path.join( dir_path, ".svn", "entries" )
    if path.isfile( entries ) :
        fh = open( entries )
        match = re.search( r'revision="(?P<revision>\d+)"', fh.read() )
        fh.close()
        if( match ) :
            revision = int( match.group( "revision" ) )

    # For latter versions, we prefer to rely on the svnversion command.
    if revision is None:
        cmd = 'cd %s && svnversion' % dir_path
        result = os.popen(cmd).read()
        match = re.search( r'\s*(\S+)', result)
        if match:
            revision = match.group(1)

    # If that doesn't work, try the svn info command.
    if revision is None:
        cmd = 'cd %s && svn info' % dir_path
        result = os.popen(cmd).read()
        match = re.search( r'Revision: (\d+)', result)
        if match:
            revision = match.group(1)

    return revision


def get_svn_branch( dir_path ) :
    """
    return the SVN branch name for the specified dir.  This is used when a
    branch name has not been supplied by a build.
    """
    entries = path.join( dir_path, ".svn", "entries" )
    branch = None

    if path.isfile( entries ) :
        fh = open( entries )
        #
        # get the branch name from the url
        #
        match = re.search( r'url="(?P<url>.+)"', fh.read() )
        fh.close()
        if( match ) :
            url = match.group( "url" )
            if( "branches" in url ) :
                tail = url.split( "branches" )[-1]
                branch = tail.split( "/" )[1]

    return branch


def get_all_versioned_modules() :
    """
    returns a list of importable modules names currently in sys.modules which
    have the necessary version files used by the functions in this module for
    getting version info
    """
    retList = []

    #
    # THIS ONLY CHECK MODULES ALREADY IMPORTED
    #
    for modName in sys.modules.keys() :
        #
        # if module has a __path__ attr, then it is a package, and packages are
        # currently the only things that have the required version files
        #
        if( hasattr( sys.modules[modName], "__path__" ) ) :
            dir = path.dirname( sys.modules[modName].__file__ )
            #
            # finally, check if the dir making up the package has a version file
            #
            if( (path.exists( path.join( dir, "%s_version.py" % modName ) )) or
                (glob.glob( path.join( dir, "%s_version.py[co]" % modName ))) ) :
                retList.append( modName )

    return retList

