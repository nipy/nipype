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

from numpy import arange, sqrt, argmax, zeros, nonzero, take, absolute


def decimate(x, y, tolerance):
    """ Returns decimated x and y arrays.

    This is Douglas and Peucker's algorithm rewritten to use Numeric arrays.
    Tolerance is usually determined by determining the size that a single pixel
    represents in the units of x and y.

    Compression ratios for large seismic and well data sets can be significant.

    """
    # Todo - we could improve the aesthetics by scaling (normalizing) the x and
    # y arrays. eg in a well the curve varies by +/- 1 and the depths by 0,10000
    # This affects the accuracy of the representation in sloping regions.

    keep = zeros(len(x))
    _decimate(x, y, keep, 0, len(x) - 1, tolerance)
    ids = nonzero(keep)
    return take(x,ids), take(y, ids)

def _decimate(x, y, keep, si, ei, tolerance):
    keep[si] = 1
    keep[ei] = 1

    # check if the two data points are adjacent
    if ei  < (si + 2):
        return

    # now find the perp distance to each point
    x0 = x[si+1:ei]
    y0 = y[si+1:ei]

    xei_minux_xsi = x[ei] - x[si]
    yei_minux_ysi = y[ei] - y[si]

    top = absolute( xei_minux_xsi * (y[si] - y0) - (x[si] - x0) * yei_minux_ysi )

    # The algorithm currently does an expensive sqrt operation which is not
    # strictly necessary except that it makes the tolerance correspond to a real
    # world quantity.
    bot = sqrt( xei_minux_xsi*xei_minux_xsi + yei_minux_ysi*yei_minux_ysi)
    dist = top / bot

    # find the point that is furthest from line between points si and ei
    index = argmax(dist)

    if dist[index] > tolerance:
        abs_index = index + (si + 1)
        keep[abs_index] = 1
        _decimate(x, y, keep, si, abs_index, tolerance)
        _decimate(x, y, keep, abs_index, ei, tolerance)

    return

if __name__ == "__main__":
    from numpy.random import random

    x = arange(0,4,0.1)
    y = zeros(len(x))
    y = random(len(x))
    tolerance = .1
    print tolerance
    nx,ny = decimate(x, y, tolerance)

    print 'before ', len(x)
    print 'after ', len(nx)
