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
# Description: <Enthought logger package component>
#------------------------------------------------------------------------------
""" Prints a stack trace every time it is called but does not halt execution
    of the application.

    Copied from Uche Ogbuji's blog
"""

# Standard library imports.
import inspect
from cStringIO import StringIO


def log_point(msg='\n'):
    stack = inspect.stack()
    # get rid of logPoint's part of the stack:
    stack = stack[1:]
    stack.reverse()
    output = StringIO()
    if msg:
        output.write(str(msg) + '\n')
    for stackLine in stack:
        frame, filename, line, funcname, lines, unknown = stackLine
        if filename.endswith('/unittest.py'):
            # unittest.py code is a boring part of the traceback
            continue
        if filename.startswith('./'):
            filename = filename[2:]
        output.write('%s:%s in %s:\n' % (filename, line, funcname))
        if lines:
            output.write('  %s\n' % ''.join(lines)[:-1])
    s = output.getvalue()

    return s

## EOF ##################################################################
