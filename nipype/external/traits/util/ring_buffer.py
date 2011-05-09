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
Copied from Python Cookbook.

"""

class RingBuffer:
    def __init__(self,size_max):
        self.max = size_max
        self.data = []
    def append(self,x):
        """append an element at the end of the buffer"""
        self.data.append(x)
        if len(self.data) == self.max:
            self.cur = 0
            self.__class__ = RingBufferFull
    def get(self):
        """ return a list of elements from the oldest to the newest"""
        return self.data


class RingBufferFull:
    def __init__(self,n):
        raise Exception("you should use RingBuffer")
    def append(self,x):
        self.data[self.cur]=x
        self.cur=(self.cur+1) % self.max
    def get(self):
        return self.data[self.cur:]+self.data[:self.cur]


# sample of use
"""x=RingBuffer(5)
x.append(1); x.append(2); x.append(3); x.append(4)
print x.__class__,x.get()
x.append(5)
print x.__class__,x.get()
x.append(6)
print x.data,x.get()
x.append(7); x.append(8); x.append(9); x.append(10)
print x.data,x.get()"""
