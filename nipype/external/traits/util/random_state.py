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
""" The two classes here help keep up with the current "state" of the
    random number generators in scipy.stats and random.  They can be
    used to save the current state of the random number generators to
    be used in the future to ensure identical results between calls.
    The RandomStateManager works as a stack with save_state, set_state
    and restore_state methods that allow you to keep a stack of states
    available.  A common usage is as follows:

    >>> # save the current state in a variable named "old_state"
    >>> old_state = RandomState()

    Perform some stochastic calculation...

    >>> # Now if you want to have stochastic_calculation() return identical
    >>> # results without disrupting other calculations that use random values
    >>> # do the following:
    >>> rsm = RandomStateManager()
    >>> rsm.save_state()
    >>> rsm.set_state(old_state)

    Perform some stochastic calculation...

    >>> rsm.restore_state()

    Note that these routines currently only support the state of random and
    scipy.stats.  If you use other random number generators, their states
    will not be managed correctly.
"""
import random
from numpy.random import get_state as get_seed
from numpy.random import set_state as set_seed

class RandomState:
    def __init__(self):
        self.update()
    def update(self):
        self.stats_seed = get_seed()
        self.random_state = random.getstate()

class RandomStateManager:

    # todo - does it make any sense to use a stack structure?
    # we currently store the seeds elsewhere anyway so the stack only
    # ever has one element in it.
    #

    def __init__(self):
        self.state_stack = []

    def save_state(self):
        current_state = RandomState()
        self.state_stack.append(current_state)

    def set_state(self, random_state):
        seed = random_state.stats_seed
        set_seed(seed)
        state = random_state.random_state
        random.setstate(state)

    def restore_state(self):
        try:
            previous_state = self.state_stack.pop(-1)
            self.set_state(previous_state)
        except:

            raise IndexError("trying to call restore_state without matching"
                             " call to save_state")


if __name__ == '__main__':
    import doctest
    doctest.testmod()
