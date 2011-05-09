#------------------------------------------------------------------------------
# Copyright (c) 2005, 2006 by Enthought, Inc.
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
import os

def get_home_directory():
    """ Determine the user's home directory."""

    # 'HOME' should work on most Unixes, and 'USERPROFILE' works on at
    # least Windows XP ;^)
    #
    # FIXME: Is this really better than the following??
    #       path = os.path.expanduser('~')
    # The above seems to work on both Windows and Unixes though the docs
    # indicate it might not work as well on Macs.
    for name in ['HOME', 'USERPROFILE']:
        if os.environ.has_key(name):
            # Make sure that the path ends with a path seperator.
            path = os.environ[name]
            if path[-1] != os.path.sep:
                path += os.path.sep

            break

    # If all else fails, the current directory will do.
    else:
        path = ''

    return path
