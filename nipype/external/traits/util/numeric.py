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
"""
This module was a placeholder for numeric functions that are not yet
implemented in SciPy, and to wrap modules some functions to handle
empty arrays properly.

This module is deprecated and should no longer be used.  It will be removed
from ETS around the 3.5 release.
"""

import warnings
warnings.warn("The traits.util.numeric module is deprecated and will " \
        "be removed from ETS in a future release.", DeprecationWarning)

import numpy
from scipy import stats

"""
The following safe_ methods were written to handle both arrays amd scalars to
save the developer of numerical methods having to clutter their code with tests
to determine the type of the data.
"""

def safe_take(a,indices):
    # Slice the input if it is an array but not if it is a scalar
    try:
        a = numpy.take(a,indices)
    except ValueError:
        # a is scalar
        pass
    return a

def safe_copy(a):
    # Return a copy for both scalar and array input
    try:
        b = a.copy()
    except AttributeError:
        # a is a scalar
        b = a
    return b

# Note: if x is a scalar and y = asarray(x), amin(y) FAILS but min(y) works
# Note: BUT IF z=convert(y,frac,frac), THEN min(z) FAILS!!!
def safe_min(a):
    # Return the minimum of the input array or the input if it is a scalar
    b = discard_nans(a)
    try:
        safemin = numpy.amin(b)
    except:
        safemin = b
    return safemin

def safe_max(a):
    # Return the maximum of the input array or the input if it is a scalar
    b = discard_nans(a)
    try:
        safemax = numpy.amax(b)
    except:
        safemax = b
    return safemax

def safe_mean(a):
    # Return the mean of the input array or the input if it is a scalar
    b = discard_nans(a)
    try:
        safemean = numpy.mean(b)
    except:
        safemean = b
    return safemean

def safe_std(a):
    # Return the std of the input array or the input if it is a scalar
    b = discard_nans(a)
    try:
        safestd = numpy.std(b)
    except:
        safestd = 0.
    return safestd

def safe_len(a):
    # Return the length of the input array or 1 if it is a scalar
    try:
        safelen = len(a)
    except:
        safelen = 1
    return safelen

def safe_flat(a):
    """ Return a flat version of the input array or input if it is a scalar
    """
    try:
        safeflat = a.flatten()
    except:
        safeflat = a
    return safeflat

def safe_nonzero(a):
    """ Gracefully handle the case where the input is a scalar
    """
    a = numpy.atleast_1d(a)
    result = numpy.nonzero(a)[0]
    return result

def discard_nans(a):
    """
    Return input sans nans and infs.  If a is scalar nan, return 0. If a is all
    nans, then return an empty array.
    """
    result = safe_copy(a)
    try:
        np = len(a)
    except:
        # scalar
        if numpy.isnan(a):
            return  0
        return a
    # array
    # isnan(a) ignores Infs, so use isfinite(a)

    ids = numpy.nonzero(numpy.isfinite(a))[0]
    nids = safe_len(ids)
    if nids == np:
        # everything is finite
        pass
    elif nids == 0:
        # everything is nans, no finites
        result = numpy.array([])
    else:
        # found some nans
        result = result[ids]
    return result



#### Miscellaneous math functions .....

def concatenate(arys, axis=0):
    """ This used to replace Numeric.concatenate to work around Numeric's old
    behavior of not handling 0-element arrays.

    numpy exhibits the desired behavior, so this function is deprecated.
    """
    warnings.warn("This function is no longer necessary. Use numpy.concatenate instead.",
        DeprecationWarning)
    result = numpy.concatenate(arys, axis=axis)
    return result

def pretty_print(arrays, header=None, max_record=0, line_number=True):
    """ Returns a string representation of a list of arrays

        Parameters
        ----------
        arrays
            a List of equal length arrays
        header
            a List of column names of the same length as the arrays
    """
    COL_WIDTH = 10

    # add a new column to the front of the list
    if line_number:
        lines = numpy.arange(0, len(arrays[0]), 1)
        arrays.insert(0, lines)
    # construct an underline bar - =======
    UNDER_LINE = '=' * (COL_WIDTH * len(arrays))

    result = UNDER_LINE + '\n'

    # label each column along the top of the table
    if header is not None:
        if line_number:
            line = "    record"
        else:
            line = ""
        for name in header:
            line = '%s%10s' % (line, name)
        result = result + line + '\n'

    #if (2 * max_record) < len(arrays[0]):
        # print 'Not implemented - only show beginning and end of data'
        # to do implement this

    for i in arrays[0]:
        line = ""
        for record in arrays:
            try:
                line = '%s%10g' % (line, record[i])
            except TypeError: # it wasn't a number so try as a String ...
                line = '%s%10s' % (line, record[i])
            except Exception, details:
                line = '%s%s' % (line, details)
        result = result + line + '\n'

    result = result + '\n' + UNDER_LINE
    return  result


def string_to_array(data):
    """ Converts a sequence of strings into a 1-D array of strings instead of a
        2-D character array. If the input data is not a String or a sequence of
        Strings return the original data object.
    """
    if isinstance(data, basestring):
        # handle a single string as input.
        data = numpy.asarray((data,), dtype=object)
    else:
        try:
            # handle a sequence of strings
            if isinstance(data[0], basestring):
                data = numpy.asarray(data, dtype=object)
        except TypeError:
            # if data wasn't a string or sequence of strings, an
            # unchanged data is returned.
            pass
    return data


#### Distribution functions ... ################################################


def single_norm(meanval, std):
    return numpy.random.normal(meanval, std)

def single_trunc_norm(mean, std, min, max):
    # Need to scale the clipping values ....
    a = (min - mean) / float(std)
    b = (max - mean) / float(std)

    value = stats.truncnorm(a, b, loc=mean, scale=std).rvs()[0]
    return value


def single_triang(ratio, start, width):
    value = stats.triang(ratio, start, width).rvs()[0]
    return value


def single_uniform(min, max):
    return numpy.random.uniform(min, max)


def nearest_index(index_array, value):
    """Find the position in an increasing array nearest a given value."""

    # find the index of the last data point that is smaller than the 'value'
    # we are looking for ....
    ind1 = len(index_array.compress(index_array < value))

    # if we are at the very end of the array then this is our best estimate ...
    if ind1 == len(index_array)-1:
        ind = ind1
    # otherwise, which of the two points is closer?
    else:
        val1 = index_array[ind1]
        val2 = index_array[ind1+1]
        if val2-value > value-val1:
            ind = ind1
        else:
            ind = ind1+1

    return ind


