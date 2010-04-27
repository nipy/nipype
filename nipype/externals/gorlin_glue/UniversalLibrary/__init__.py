# emacs, this is -*-Python-*- mode

# Copyright (c) 2006, California Institute of Technology
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:

#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.

#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.

#     * Neither the name of the California Institute of Technology nor
#       the names of its contributors may be used to endorse or promote
#       products derived from this software without specific prior
#       written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Author: Andrew Straw
import cbw
import constants
import numpy as N

def _callback(BoardNum, EventType, EventData, UserData):
    """Callback function template"""
    pass
def _callback_print(BoardNum, EventType, EventData, UserData):
    """Callback function template"""
    print BoardNum, EventType, EventData

class Daq(object):
    def __init__(self, Rate, LowChan=0, HighChan=7,
                 Gain=constants.BIP5VOLTS, Board=0,
                 FunctionType=constants.AIFUNCTION,
                 dtype=N.int16):
        self.Board=Board
        self.LowChan = LowChan
        self.HighChan = HighChan
        self.Rate = Rate
        self.Gain = Gain
        self.FunctionType = FunctionType
        self._dtype=dtype
        self.flushBuffer()
        
    @property
    def nchans(self):
        return self.HighChan-self.LowChan+1
    
    def flushBuffer(self, seconds=10):
        """Creates or flushes the buffer"""
        self.__buffer = N.zeros(N.round(seconds*self.Rate)*self.nchans, dtype=self._dtype)
        
    def stopBackground(self):
        cbw.cbStopBackground(self.Board, self.FunctionType)
        
    def startBackground(self, Options=0):
        """Begins AI scanning in background
        :Parameters:
        self.Rate is samples per second per channel
        Options: sent to cbAInScan.  One good one is constants.SINGLEIO if you
          want real-time access to your data (at the cost of bandwidth)
        Returns: numpy array which contains the scanned data.  Call getStatus or 
        getAI to return data from it
        
        """
        cbw.cbAInScan(self.Board, self.LowChan, self.HighChan,
                      self.__buffer.size, self.Rate, self.Gain, self.__buffer, 
                      Options | constants.BACKGROUND | constants.CONTINUOUS)
    def convertData(self, data):
        """Returns voltage values from raw DAQ count
        """
        return N.asarray([cbw.cbToEngUnits(self.Board, self.Gain, int(d)) for d in data], dtype=float)
    
    def getCurrent(self, convert=True):
        """Gets the last updated AI from the buffer, if scanning in background
        Timestamps based on highly accurate rate (nth acquired sample) in seconds since
        beginning of acquisition.  For super accuracy, note that this timestamp is based on
        which channel was just scanned, so the timestamp w.r.t the first acquired channel can be
        delayed up to (n scanned channels - 1)/(total rate)
        Returns (timestamp, numpy array (or zeros if not scanning) where 0th ind is LowChannel)
        """
        status = cbw.cbGetStatus(self.Board, 0, 0, 0, self.FunctionType)
        if status[0]:#Currently scanning
            n = self.nchans
            # Current indeces
            ci = status[2]
            chanindeces = N.arange(ci, ci+n)
            tstamp = status[1]/float(self.Rate*n)
            #print status, chanindeces
            if convert:
                d = self.convertData(self.__buffer[chanindeces])
            else: d = self.__buffer[chanindeces]
            return (tstamp, d)
        Warning('Not currently scanning on board %d'%self.Board)
        return (0, N.zeros(self.nchans, dtype=self._dtype))


    
    def disableEvent(self, EventType=constants.ON_DATA_AVAILABLE):
        cbw.cbDisableEvent(self.Board, EventType)
        
    def enableEvent(self, EventType=constants.ON_DATA_AVAILABLE,
                    EventParam=constants.LATCH_DI, fcn=_callback_print, UserData=None):
        """fcn must be a callable object that takes input of the template callback
        UserData must be castable to a ctypes value
        Likely cannot be called when a background scan is in process
        """
        cbw.cbEnableEvent(self.Board, EventType, EventParam, fcn, UserData)
        
if __name__=="__main__":
    d = Daq(100)
    pass