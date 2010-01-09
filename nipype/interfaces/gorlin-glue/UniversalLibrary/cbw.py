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

"""
PyUniversalLibrary is a Python wrapper for Measurement Computing's
Universal Library for data acquisition on Microsoft Windows operating
systems.


Functions not wrapped because the Python UniversalLibrary module
should eliminate the need to call them:

cbErrHandling()
cbDeclareRevision()

This module provides a low-level wrap of cbw32.dll which implements the 
Universal Library.  The API is directly copied in a sometimes very un-Pythonic
manner, so it's probably better to use the Daq wrapper class directly

"""

import ctypes
from ctypes import byref
import numpy
#from constants import NOERRORS, ERRSTRLEN
import constants # PyUL contants
#from constants import * # PyUL contants
import sys
TESTMODE=True
try:
    assert sys.platform == 'win32'
    cbw = ctypes.windll.cbw32 # open CBW32.DLL
    TESTMODE = False
except AssertionError:
    Warning('UniversalLibrary only runs on Win32 platforms')
except:
    Warning('Unknown error loading UniversalLibrary.  Is it installed?')

#all_constants = [attr for attr in constants.__dict__
                 #if not attr.startswith('__')]

#__all__ = ['UniversalLibraryBaseError',
           #'UniversalLibraryError',
           #'UniversalLibraryBaseError',
           #'cbAConvertData',
           #'cbAConvertPretrigData',
           #'cbACalibrateData',
           #'cbAIn',
           #'cbAInScan',
           #'cbALoadQueue',
           #'cbAOut',
           #'cbAOutScan',
           #'cbAPretrig',
           #'cbATrig',

           #'cbGetConfig',
           #'cbGetSignal',
           #'cbSelectSignal',
           #'cbSetConfig',
           #'cbSetTrigger',
           
           #'cbDBitIn',
           #'cbDBitOut',
           #'cbDConfigBit',
           #'cbDConfigPort',
           #'cbDIn',
           #'cbDInScan',
           #'cbDOut',
           #'cbDOutScan',

           #'cbGetRevision',

           #'cbTIn',
           #'cbTInScan',
           
           #'cbFromEngUnits',
           #'cbToEngUnits',
           #'cbGetStatus',
           #'
           #] + all_constants

#__version__ = '20061020'

class UniversalLibraryBaseError( Exception ):
    """base class for all UniversalLibrary exceptions"""
    pass

class UniversalLibraryError( UniversalLibraryBaseError ):
    """error occurred within the C layer of Universal Library"""
    def __init__(self, UDStat):
        errstr = 'Error %d: %s'%(UDStat,_get_error_message(UDStat))
        self.errno = UDStat
        Exception.__init__(self, errstr)

class UniversalLibraryPythonError( UniversalLibraryBaseError ):
    """error occurred within the Python layer of Universal Library"""
    pass

def _get_error_message(UDStat):
    err_msg = ctypes.create_string_buffer(constants.ERRSTRLEN)
    err2 = cbw.cbGetErrMsg(UDStat,err_msg)
    if err2:
        raise SystemError(
            'Error %d while getting error message for error %d'%(err2,UDStat))
    origerrstr = err_msg.value
    return origerrstr

def CHK(UDStat):
    """raise appropriate exception if error occurred"""
    if UDStat != constants.NOERRORS:
        raise UniversalLibraryError(UDStat)
    
def CHK_ARRAY( arr, N, nxtype ):
    if not hasattr(arr,'shape'):
        raise UniversalLibraryPythonError("input argument is not an array")
    if len(arr.shape) != 1:
        raise UniversalLibraryPythonError("array is not rank 1")
    if arr.dtype != nxtype:
        raise UniversalLibraryPythonError("array is not correct data type '%s'"%str(nxtype))
    if len(arr) < N:
        raise UniversalLibraryPythonError("array is not large enough")
    if not arr.flags['CONTIGUOUS']:
        raise UniversalLibraryPythonError("array is not contiguous")
    return arr
    
def __declare_revlevel__():
    RevLevel = ctypes.c_float(constants.CURRENTREVNUM)
    CHK(cbw.cbDeclareRevision(ctypes.byref(RevLevel)))

###############################
#
# Analog I/O functions for UL
#
###############################

def cbAConvertData (BoardNum, NumPoints, ADData, 
                    ChanTags):
    """Convert data collected by cbAInScan()

    Inputs
    ------
    BoardNum
    NumPoints
    ADData --  modified to contain the data array
    ChanTags --  modified to contain the channel tag array

    """
    CHK_ARRAY( ADData, NumPoints, numpy.uint16 )
    CHK_ARRAY( ChanTags, NumPoints, numpy.uint16 )
    CHK( cbw.cbAConvertData(BoardNum, NumPoints, ADData.ctypes.data, 
                            ChanTags.ctypes.data))
    
def cbAConvertPretrigData(BoardNum, PreTrigCount, 
                          TotalCount, ADData, 
                          ChanTags):
    """Convert data collected by cbAPretrig().

    Inputs
    ------
    BoardNum
    PreTrigCount
    TotalCount
    ADData --  modified to contain the data array
    ChanTags --  modified to contain the channel tag array

    """
    CHK_ARRAY( ADData, NumPoints, numpy.uint16 )
    CHK_ARRAY( ChanTags, NumPoints, numpy.uint16 )
    CHK( cbw.cbAConvertPretrigData(BoardNum, PreTrigCount, 
                                   TotalCount, ADData.ctypes.data, 
                                   ChanTags.ctypes.data))

def cbACalibrateData(BoardNum, NumPoints, Gain, 
                     ADData):
    CHK( cbw.cbACalibrateData ( BoardNum, NumPoints, Gain, 
                                ADData.ctypes.data))

def cbAIn( BoardNum,  Chan, Gain, DataValue=0):
    """Read A/D input channel

    Inputs
    ------
    
    BoardNum
    Chan
    Gain
    DataValue

    Outputs
    -------
    DataValue
    
    """
    cDataValue = ctypes.c_ushort(DataValue)
    CHK(cbw.cbAIn(BoardNum, Chan, Gain, ctypes.byref(cDataValue)))
    return cDataValue.value

def cbAInScan(BoardNum, LowChan, HighChan, Count,
              Rate, Gain, ADData,
              Options):
    """Scan range of A/D channels and store samples in an array

    Inputs
    ------

    BoardNum
    LowChan
    HighChan
    Count
    Rate
    Gain
    ADData -- pointer from cbWinBufAlloc #modified to contain the sampled data
    Options

    Outputs
    -------
    
    Rate
    
    """
    Rate = ctypes.c_long(Rate)
    CHK_ARRAY( ADData, Count, numpy.int16 )
    CHK(cbw.cbAInScan(BoardNum, LowChan, HighChan, Count,
                      byref(Rate), Gain, ADData.ctypes.data, Options))
    return Rate.value

def cbALoadQueue ( BoardNum, ChanArray, GainArray, 
                   NumChans):
    CHK_ARRAY( ChanArray, NumChans, numpy.int16 )
    CHK_ARRAY( GainArray, NumChans, numpy.int16 )
    CHK(cbw.cbALoadQueue(BoardNum, ChanArray.ctypes.data,
                         GainArray.ctypes.data, NumChans))
    
def cbAOut(BoardNum, Chan, Gain, DataValue):
    CHK( cbw.cbAOut(BoardNum, Chan, Gain, DataValue))

def cbAOutScan(BoardNum, LowChan, HighChan, 
               Count, Rate, Gain, 
               MemHandle, Options):
    CHK_ARRAY( MemHandle, Count, numpy.int16 )
    Rate = ctypes.c_long(Rate)
    CHK(cbw.cbAOutScan( BoardNum, LowChan, HighChan, 
                        Count, byref(Rate), Gain, 
                        MemHandle.ctypes.data, Options))
    return Rate.value
    
def cbAPretrig(BoardNum, LowChan, HighChan,
               PreTrigCount, TotalCount, Rate, 
               Gain, ADData, Options):
    """Acquire analog data upon being triggered.

    Inputs
    ------
    
    BoardNum
    LowChan
    HighChan
    PreTrigCount
    TotalCount
    Rate
    Gain
    ADData -- modified to contain the sampled data
    Options

    Outputs
    -------

    PreTrigCount
    TotalCount
    Rate

    """
    
    CHK_ARRAY( ADData, TotalCount+512, numpy.int16 )
    PreTrigCount = ctypes.c_long(PreTrigCount)
    TotalCount = ctypes.c_long(TotalCount)
    Rate = ctypes.c_long(Rate)
    CHK(cbw.cbAPretrig( BoardNum, LowChan, HighChan,
                          byref(PreTrigCount), byref(TotalCount),
                          byref(Rate), 
                          Gain, ADData.ctypes.data, Options))
    return PreTrigCount.value, TotalCount.value, Rate.value

def cbATrig(BoardNum, Chan, TrigType, 
            TrigValue, Gain, DataValue):
    DataValue = ctypes.c_ushort(DataValue)
    CHK(cbw.cbATrig( BoardNum, Chan, TrigType, 
                     TrigValue, Gain, byref(DataValue)))
    return DataValue.value

###################################
#
# Configuration functions for UL
#
###################################

def cbGetConfig(InfoType, BoardNum, DevNum, 
                ConfigItem, ConfigVal):
    """Return a configuration option for a card.

    Inputs
    ------
    InfoType
    BoardNum
    DevNum
    ConfigItem
    ConfigVal

    Outputs
    -------
    ConfigVal
    """
    ConfigVal = ctypes.c_int(ConfigVal)
    CHK( cbw.cbGetConfig(InfoType, BoardNum, DevNum, 
                          ConfigItem, byref(ConfigVal)))
    return ConfigVal.value

def cbGetSignal(BoardNum, Direction, Signal, Index, Connection, Polarity):
    """Retrieve the information for the specified timing and control signal

    Inputs
    ------

    BoardNum
    Direction
    Signal
    Index
    Connection
    Polarity

    Outputs
    -------

    Connection
    Polarity
    
    """
    Connection = ctypes.c_int(Connection)
    Polarity = ctypes.c_int(Polarity)
    CHK(cbw.cbGetSignal(BoardNum, Direction, Signal, Index,
                        byref(Connection),byref(Polarity)))
    return Connection.value, Polarity.value

def cbSelectSignal(BoardNum, Direction, Signal, Connection, Polarity):
    """Configure timing and control signal to use specific connections
    as a source or destination.

    Inputs
    ------
    
    BoardNum
    Direction
    Signal
    Connection
    Polarity
    
    """
    CHK(cbw.cbSelectSignal(BoardNum, Direction, Signal, Connection, Polarity))

def cbSetConfig(InfoType, BoardNum, DevNum, 
                ConfigItem, ConfigVal):
    """Set configuration option for a card.

    Inputs
    ------
    InfoType
    BoardNum
    DevNum
    ConfigItem
    ConfigVal
    """
    CHK(cbw.cbSetConfig(InfoType,BoardNum,DevNum, ConfigItem,ConfigVal))
    
def cbSetTrigger(BoardNum, TrigType, LowThreshold, 
                 HighThreshold):
    """Selects trigger source and sets up parameters

    Inputs
    ------
    
    BoardNum
    TrigType
    LowThreshold
    HighThreshold
    
    """
    CHK( cbw.cbSetTrigger(BoardNum,TrigType,LowThreshold,HighThreshold))

################################
#
# Digital I/O functions for UL
#
################################

def cbDBitIn(BoardNum, PortType, BitNum, BitValue):
    """Read state of a single digital input bit.

    Inputs
    ------
    
    BoardNum
    PortType
    BitNum
    BitValue

    Outputs
    -------

    BitValue

    """
    BitValue = ctypes.c_ushort(BitValue)
    CHK(cbw.cbDBitIn(BoardNum, PortType, BitNum, byref(BitValue)))
    return BitValue.value

def cbDBitOut(BoardNum, PortType, BitNum, BitValue):
    """Set state of a single digital output bit.

    Inputs
    ------
    
    BoardNum
    PortType
    BitNum
    BitValue
    
    """
    CHK( cbw.cbDBitOut( BoardNum, PortType, BitNum, BitValue))

def cbDConfigBit(BoardNum, PortNum, BitNum, Direction):
    """Configure a digital bit as Input or Output.

    Inputs
    ------
    BoardNum
    PortNum
    BitNum
    Direction

    """
    CHK(cbw.cbDConfigBit(BoardNum, PortNum, BitNum, Direction))

def cbDConfigPort(BoardNum, PortNum, Direction):
    """Configure digital port as input or output.

    Inputs
    ------
    BoardNum
    PortNum
    Direction
    
    """
    CHK( cbw.cbDConfigPort( BoardNum, PortNum, Direction))

def cbDIn(BoardNum, PortNum, DataValue):
    """Read a digital port

    Inputs
    ------
    BoardNum
    PortNum
    DataValue

    Outputs
    -------
    DataValue

    """
    DataValue = ctypes.c_ushort(DataValue)
    CHK(cbw.cbDIn(BoardNum, PortNum, byref(DataValue)))
    return DataValue.value

def cbDInScan( BoardNum, PortNum, Count, Rate,
               MemHandle, Options):
    """Multiple reads of a digital port

    Inputs
    ------

    BoardNum
    PortNum
    Count
    Rate
    MemHandle -- modified to contain the sampled data
    Options

    Outputs
    -------

    Rate

    """
    CHK_ARRAY( MemHandle, Count, numpy.uint8 )
    Rate = ctypes.c_long(Rate)
    CHK(cbw.cbDInScan( BoardNum, PortNum, Count, byref(Rate),
                       MemHandle.ctypes.data, Options))
    return Rate

def cbDOut(BoardNum, PortNum, DataValue):
    """Write to digital output

    Inputs
    ------
    BoardNum
    PortNum
    DataValue
    
    """
    CHK(cbw.cbDOut(BoardNum, PortNum, DataValue))

def cbDOutScan(BoardNum, PortNum, Count, Rate,
               MemHandle, Options):
    """Perform multiple writes to digital output

    Inputs
    ------
    
    BoardNum
    PortNum
    Count
    Rate
    MemHandle -- modified to contain the sampled data
    Options

    Outputs
    -------

    Rate

    """
    CHK_ARRAY( MemHandle, Count, numpy.uint8 )
    Rate = ctypes.c_long(Rate)
    CHK(cbw.cbDOutScan( BoardNum, PortNum, Count, byref(Rate),
                        MemHandle.ctypes.data, Options))
    return Rate.value

#####################################
#
# Revision Control functions for UL
#
#####################################

def cbGetRevision():
    """Doesn't actually do anything in library? Tech support claims they
    never implemented this in any significant way"""
    RevNum = ctypes.c_float()
    VxDRevNum = ctypes.c_float()
    cbw.cbGetRevision (byref(RevNum), byref(VxDRevNum))
    return RevNum.value, VxDRevNum.value

###############################
#
# Temperature Input Functions
#
###############################

def cbTIn(BoardNum, Chan, Scale, TempValue, Options):
    """Read temperature.

    Inputs
    ------

    BoardNum
    Chan
    Scale
    TempValue
    Options

    Outputs
    -------
    
    TempValue

    """
    TempValue = ctypes.c_float(TempValue)
    CHK( cbw.cbTIn( BoardNum, Chan, Scale, byref(TempValue), Options))
    return TempValue.value

def cbTInScan(BoardNum, LowChan, HighChan, Scale,
              DataBuffer, Options):
    """Read a range of temperature channels

    Inputs
    ------

    BoardNum
    LowChan
    HighChan
    Scale
    DataBuffer -- modified to contain the sampled data
    Options

    """
    CHK_ARRAY( DataBuffer, HighChan - LowChan + 1, numpy.float32 )
    CHK(cbw.cbTInScan(BoardNum, LowChan, HighChan, Scale,
                      DataBuffer.ctypes.data, Options))
    
###############################
#
# Miscellaneous functions
#
###############################

def cbFromEngUnits(BoardNum, Range, EngUnits, DataVal):
    """Convert a voltage or current to an A/D count value
    
    Inputs
    ------
    
    BoardNum
    Range
    EngUnits
    DataVal
    
    Outputs
    -------

    DataVal
    
    """
    DataVal = ctypes.c_ushort(DataVal)
    EngUnits = ctypes.c_float(EngUnits)
    CHK(cbw.cbFromEngUnits(BoardNum, Range, EngUnits, byref(DataVal)))
    return DataVal.value

def cbToEngUnits(BoardNum, Range, DataVal, EngUnits=0.0):
    """Converts an A/D count value to voltage value

    Inputs
    ------

    BoardNum
    Range
    DataVal
    EngUnits

    Outputs
    -------

    EngUnits

    """
    EngUnits = ctypes.c_float(EngUnits)
    CHK(cbw.cbToEngUnits(BoardNum, Range, DataVal, byref(EngUnits)))
    return EngUnits.value
    
def cbGetStatus(BoardNum, Status, CurCount,
                CurIndex, FunctionType):
    """Returns status about potentially currently running background operation
    
    Returns: (Status, CurrentCount, CurrentIndex)
    """
    Status = ctypes.c_short(Status)
    CurCount = ctypes.c_long(CurCount)
    CurIndex = ctypes.c_long(CurIndex)
    # Error in documentation - cbGetStatus has slightly different API, and
    # undocumented cbGetIOStatus has the published API
    CHK( cbw.cbGetIOStatus(BoardNum, byref(Status), byref(CurCount), 
                           byref(CurIndex), FunctionType))
    return Status.value, CurCount.value, CurIndex.value

def cbStopBackground(BoardNum, FunctionType):
    """Stops any scanning in background"""
    # Error in documentation - cbStopBackground has slightly different API,
    # and undocumented cbStopIOBackround has the published API
    CHK( cbw.cbStopIOBackground(BoardNum, FunctionType) ) 

UserCallback = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p)
def cbEnableEvent(BoardNum, EventType, EventParam, CallbackFunc, UserData):
    CHK( cbw.cbEnableEvent(BoardNum, EventType, EventParam, UserCallback(CallbackFunc), byref(ctypes.c_void_p(UserData))) )
def cbDisableEvent(BoardNum, EventType):
    CHK( cbw.cbDisableEvent(BoardNum, EventType) )
    
###############################
#
# Memory allocation
#
###############################

def cbWinBufAlloc(NumPoints):
    """Allocates N 16-bit integers and returns a pointer to the array,
    or 0 if failed"""
    return cbw.cbWinBufAlloc(NumPoints)
def cbScaledWinBufAlloc(NumPoints):
    """Allocated N double floating points in a win buffer"""
    return cbw.cbScaledWinBufAlloc(NumPoints)
def cbWinBufToArray(MemHandle, DataArray, FirstPoint, Count):
    CHK_ARRAY( DataArray, Count, numpy.uint16 )
    CHK( cbw.cbWinBufToArray(MemHandle, byref(DataArray), FirstPoint, Count) )
    return DataArray
def cbWinBufFree(MemHandle):
    CHK(cbw.cbWinBufFree(MemHandle))



