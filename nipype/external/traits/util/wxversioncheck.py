"""
Implements the wx ensureMinimal utility function.  This is re-defined here
because the original did not allow users to call it more than once...that is a
problem when package developers include it in their packages and app developers
want to use multiple packages, all with calls in them.  Also in this module is a
platform check.  Currently, Enthon on Windows does not include wxversion.py, and
since this particular module is in place primarily for Enthought apps,
ensureMinimal() is skipped on Windows.  THE PLATFORM CHECK IS TEMPORARY and will
go away when the apps include wxversion.py in their wx distributions.
"""


import sys
if sys.platform == 'win32' :
    # wxversion is not available on all platforms (Windows)
    def ensureMinimal(minVersion, optionsRequired=False):
        return


#
# taken from wxversion.py, but removed exception raising if wx had been
# previously imported and the attempt to bring up a wx dialog prompting
# the user to download a newer version.
#
else :
    import wxversion

    def ensureMinimal(minVersion, optionsRequired=False):
        """
        Checks to see if the default (as defined by sys.path) version of wx is
        >= minVersion.  This was taken from the wx 2.6 package and modified for
        use with Enthought packages.  The modifications were made since it
        cannot easily be assumed that wx was not imported prior to calling this
        method, mainly due to the numerous side-effects of putting lots of code
        in package __init__ files.

        Here is the original docstring:

        Checks to see if the default version of wxPython is greater-than
        or equal to `minVersion`.  If not then it will try to find an
        installed version that is >= minVersion.  If none are available
        then a message is displayed that will inform the user and will
        offer to open their web browser to the wxPython downloads page,
        and will then exit the application.

        As mentioned above, the function used to also ensure that wxPython had
        not been imported yet.

        Now, the function simply checks if the default version is >= minVersion
        and raises an exception if not.
        """
        assert isinstance(minVersion, basestring)

        bestMatch = None
        errString = "A minimum wx version of %s is required" % minVersion

        # this code is in a try-finally since it cannot be guaranteed that
        # the version of wxversion.py installed has the same API as assumed
        try :
            minv = wxversion._wxPackageInfo(minVersion)

            # check the default version first
            defaultPath = wxversion._find_default()
            if defaultPath:
                defv = wxversion._wxPackageInfo(defaultPath, True)
                if defv >= minv and minv.CheckOptions(defv, optionsRequired):
                    bestMatch = defv

            if bestMatch is None:
                errString += "\nThis is what was found:\n" + \
                    "version: %s\n" % `defv.version` + \
                    "wx location: %s\n" % defv.pathname + \
                    "PYTHONPATH: %s" % sys.path

        finally :
            # if no match then bail out
            if bestMatch is None:
                raise wxversion.VersionError( errString )

            global _selected
            _selected = bestMatch

