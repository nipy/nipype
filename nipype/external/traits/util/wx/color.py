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
""" Color utilities. """


from numpy import asarray, array


# fixme: This should move into enable.
def wx_to_enable_color(color):
    """ Convert a wx color spec. to an enable color spec. """

    enable_color = array((1.0,1.0,1.0,1.0))
    enable_color[:3] = asarray(color.Get())/255.

    return tuple(enable_color)

#### EOF ######################################################################
