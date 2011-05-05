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
""" Modifications to the standard profile.py API.

    The standard profile.run() method in the Python library does not provide
    access to variables available to the code snippet during a run.  For
    example, the following fails:

        a = 1
        profile.run("main(a)")

    This is because the variable 'a' will not properly be found.  This function
    fixes the problem.
"""

import profile

def run(statement, filename=None):
    """ Runs 'statement' under profiler, optionally saving results in
    'filename'.

    This function takes a single argument that can be passed to the
    "exec" statement, and an optional file name.  In all cases this
    routine attempts to "exec" its first argument and gather profiling
    statistics from the execution. If no file name is present, then this
    function automatically prints a simple profiling report, sorted by the
    standard name string (file/line/function-name) that is presented in
    each line.
    """
    prof = profile.Profile()
    try:
        import sys
        fr = sys._getframe().f_back
        prof = prof.runctx(statement, fr.f_globals, fr.f_locals)
    except SystemExit:
        pass
    if filename is not None:
        prof.dump_stats(filename)
    else:
        return prof.print_stats()


