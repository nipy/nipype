"""Utility function to perform global search and replace in a source tree.

`perlpie` will perform a global search and replace on all files in a
directory recursively.  It's a small python wrapper around the `perl
-p -i -e` functionality, but with easier syntax.  I **strongly
recommend** running `perlpie` on files under source control.  In this
way it's easy to track your changes and if (more likely when) you
discover your regular expression was wrong you can easily revert.  I
also recommend using `grin` to test your regular expressions before
running `perlpie`.

Parameters
----------
oldstring : regular expression
    Regular expression matching the string you want to replace
newstring : string
    The string you would like to replace the oldstring with.  Note
    this is not a regular expression but the exact string. One
    exception to this rule is the at symbol `@`.  This has special
    meaning in perl, so you need an escape character for this.  See
    Examples below.

Requires
--------
perl : The underlying language we're using to perform the search and replace.

`grin <http://pypi.python.org/pypi/grin/>`_ : Grin is a tool written
by Robert Kern to wrap `grep` and `find` with python and easier
command line options.

Example
-------

Replace all occurences of foo with bar::

    perlpie foo bar

Replace numpy.testing with nipy's testing framework::

    perlpie 'from\s+numpy\.testing.*' 'from nipy.testing import *'

Replace all @slow decorators in my code with @dec.super_slow.  Here we
have to escape the @ symbol which has special meaning in perl::
    
    perlpie '\@slow' '\@dec.super_slow'

Remove all occurences of importing make_doctest_suite::

    perlpie 'from\snipy\.utils\.testutils.*make_doctest_suite'

"""

# notes on perl-dash-pie
# perl -p -i -e 's/oldstring/newstring/g' *
# find . -name '*.html' -print0 | xargs -0 perl -pi -e 's/oldstring/newstring/g'

from optparse import OptionParser
import subprocess


def check_deps():
    try:
        import grin
    except ImportError:
        print 'perlpie requires grin to operate.'
        print 'You can find grin in the python package index:'
        print '  http://pypi.python.org/pypi/grin/'
        return False
    # assume they have perl for now
    return True


def perl_dash_pie(oldstr, newstr):
    """Use perl to replace the oldstr with the newstr.

    Examples
    --------

    # To replace all occurences of 'import numpy as N' with 'import numpy as np'
    >>> from nipy.utils import perlpie
    >>> perlpie.perl_dash_pie('import\s+numpy\s+as\s+N', 'import numpy as np')
    grind | xargs perl -pi -e 's/import\s+numpy\s+as\s+N/import numpy as np/g'
    
    """

    cmd = "grind | xargs perl -pi -e 's/%s/%s/g'" % (oldstr, newstr)
    print cmd
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError, err:
        msg = """
        Error while executing perl_dash_pie command:
        %s
        Error:
        %s
        """ % (cmd, str(err))
        raise Exception(msg)


def main():
    param_index = __doc__.index('Parameters')
    description = __doc__[:param_index]
    usage = "usage: %prog [options] oldstring newstring"
    parser = OptionParser(usage=usage, description=description)
    (options, args) = parser.parse_args()

    if not args:
        parser.print_help()
        return

    if check_deps():
        oldstr = args[0]
        newstr = args[1]
        perl_dash_pie(oldstr, newstr)
