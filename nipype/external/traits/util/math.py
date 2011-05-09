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
""" A placeholder for math functionality that is not implemented in SciPy.
"""

import numpy

def is_monotonic(array):
    """ Does the array increase monotonically?

    >>> is_monotonic(array((1, 2, 3, 4)))
    True
    >>> is_monotonic(array((1, 2, 3, 0, 5)))
    False

    This may not be the desired response but:

    >>> is_monotonic(array((1)))
    False
    """

    try:
        min_increment = numpy.amin(array[1:] - array[:-1])
        if min_increment >= 0:
            return True
    except Exception:
            return False
    return False;


def brange(min_value, max_value, increment):
    """ Returns an inclusive version of arange().

    The usual arange() gives:

    >>> arange(1, 4, 1)
    array([1, 2, 3])

    However brange() returns:

    >>> brange(1, 4, 1)
    array([ 1.,  2.,  3.,  4.])
    """

    return numpy.arange(min_value, max_value + increment / 2.0, increment)


def norm(mean, std):
    """ Returns a single random value from a normal distribution. """

    return numpy.random.normal(mean, std)


def discrete_std (counts, bin_centers):
    """ Returns a standard deviation from binned data. """

    mean = numpy.sum(counts * bin_centers)/numpy.sum(counts)

    return numpy.sqrt((numpy.sum((counts-mean)**2))/len(counts))
