#------------------------------------------------------------------------------
# Copyright (c) 2007, Enthought, Inc.
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in enthought/LICENSE.txt and may be redistributed only
# under the conditions described in the aforementioned license.  The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
# Thanks for using Enthought open source!
#
# Author: Enthought, Inc.
# Description: <Enthought statistical distribution package component>
#------------------------------------------------------------------------------

""" Base class representing distribution input variables used for stocastic modeling """

from traits.api import HasTraits, Property, Float, Int
from traitsui.api import View, Item

import numpy

class Distribution(HasTraits):
    """ Base Class for input variables representing a variable which
        produces a range of values

    """

    # the values representing the distribution
    values = Property(Int)
    _values = None

    # how many values should be generated?
    samples = Int(10)

    _state = None

    def _get_values(self):
        """ getter for the values property """
        if self._state is None:
            self._state = numpy.random.RandomState()
        if self._values is None:
            self._values = self._get_value(self.samples)
        return self._values

    def _get_value(self, n):
        """ returns 'n' values for the distribution """
        raise NotImplemented

    def get_state(self):
        """ returns the random state variable """
        if self._state is None:
            self.set_state(None)

        return self._state.get_state()

    def set_state(self, state):
        """ sets the random state. If the argument is None the state
            will be initialized to a new random state. The method
            returns the state that was set

        """
        if state is None:
            self._state = numpy.random.RandomState()
        else:
            self._state.set_state(state)


        #invalidate the cached values
        self._values = None

        return self._state.get_state()

    def _anytrait_changed(self):
        #invalidate the _values so they have to be regenerated
        self._values = None
class Constant(Distribution):
    """ A constant distribution where all values are the same """
    value = Float

    traits_view = View(Item('value'))

    def _get_value(self, n):
        return numpy.repeat(self.value, n)

class Gaussian(Distribution):
    """ A gaussian distribution """
    mean = Float(50.0)
    std = Float(2.0)

    traits_view = View(Item('mean'), Item('std'))

    def _get_value(self, n):
        return self._state.normal(self.mean, self.std, n)

class Triangular(Distribution):
    """ A triangular distribution """
    mode = Float
    low = Float
    high = Float

    traits_view = View(Item('mode'), Item('low'), Item('high'))

    def _get_value(self, n):
        return self._state.triangular(self.low, self.mode, self.high, n)

class Uniform(Distribution):
    """ A uniform distribution """
    low = Float
    high = Float

    view = View(Item('low'), Item('high'))

    def _get_value(self, n):
        return self._state.uniform(self.low, self.high, n)
