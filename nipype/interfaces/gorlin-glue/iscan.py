
import serial
from multicast import MultiReceive, MultiSend, socket
from struct import Struct
from timeit import default_timer as time # Between time.time and time.clock
from time import sleep
try:
    import multiprocessing
    from multiprocessing import Value
except ImportError:# Python <v2.5
    class Value(object):
        """A nonfunctional replacement for multiprocessing.Value
        This servers just to unify the api for python 2.5 servers
        """
        def __init__(self, typecode_or_type, val):
            self.value=val
"""Module enabling real-time communication with an iSCAN computer 

depends on:
multiprocessing (python 2.6) for client
pyserial

Ensure that iSCAN is set to output binary data over serial port
"""

EYEGROUP = '225.0.0.250'
MYPORT = 8123
#_BAUDRATE = 115200

# Basics to help out
def serve(**kwargs):
    return iSCAN().serve(**kwargs)

#def _convert(b):
    #try:
        #return float(b[0] + (b[1] << 8))
    #except ValueError:
        #return None
    
#def _serial(**serialkwds):
    #return serial.Serial(**serialkwds)

# Multiprocessors
#def _run_server(chan1, chan2, **serialkwds):
    #s = _serial(**serialkwds)
    #raise NotImplementedError()
def _run_ve(chan1, chan2):
    from VisionEgg.Core import Viewport, Screen, OrthographicProjection, FixationSpot, Presentation, FunctionController
    size=(640, 480)
    screen = Screen(size=size, fullscreen=False, sync_swap=True, bgcolor=(.5, .5, .5))
    projection = OrthographicProjection(left=-20, right=20, top=20, bottom=-20)
    fix = FixationSpot(position=(0,0), size=(.5, .5))
    viewport = Viewport(projection=projection, screen=screen, stimuli=[fix])
    def getPosition(t):
        return (chan1.value, chan2.value)
    p = Presentation(go_duration=('forever',), viewports=[viewport])
    p.add_controller(fix, 'position', FunctionController(during_go_func=getPosition))
    
    p.go()

def _run_client(chan1, chan2, **serialkwds):
    # Init serial port
    #s = _serial(**serialkwds)
    recv = MultiReceive(EYEGROUP)
    #import array
    #magic = array.array('f', 'DDDD')[0]
    #data = array.array('h', [0]*6)
    # Flushes serial port, lines up with stream
    #s.flushInput()
    #synced = False
    #while not synced:
        #count=0
        #while count < 4 and s.read(1)=='D':
            #count+=1
            #synced = count == 4
        
    #s.read(8)
    # Read loop
    while True:
        #data = array.array('f', s.read(12))
        (t, x, y) = recv.decode(iSCAN.EYE_STRUCT)
        #assert data[0]==magic # This should always be true, but let's not waste time
        chan1.value=x#data[1]
        chan2.value=y#data[2]
        
class iSCAN(object):

    EYE_STRUCT=Struct('!ddd') # Network-format, 3 doubles (time, x, y)
    
    def __init__(self, port=0, receiveTimeout=0.003, serialkwds={}):
        #self.__serialkwds = serialkwds
        #self.__serialkwds['port'] = port
        #self.__serialkwds['baudrate']=_BAUDRATE
        self.__p = None
        self.__chan1 = Value('d', 0)
        self.__chan2 = Value('d', 0)
        self.__send = MultiSend(EYEGROUP)
        self.__rttl = receiveTimeout
        self.__receive = MultiReceive(EYEGROUP)
        self.__serialkwds = serialkwds

    @property
    def x(self):
        return self.__chan1.value
    @property
    def y(self):
        return self.__chan2.value
    
    def getXY(self):
        """Polls current (t, (x,y)) of eye position once and returns
        (will block if no x,y is being sen, or timeout)
        Flushes the UDP buffer to ensure current data.  It is important to do
        this before any non-continuous acquisition since the udp buffer size 
        cannot be set to 0
        """
        self.__receive.flush()
        self.__receive._s.settimeout(self.__rttl)
        try:
            t, x, y = self.__receive.decode(iSCAN.EYE_STRUCT)
        except socket.timeout:
            t, x, y = (time(),0,0)
        return (t, (x,y))
    
    def start(self):
        """Starts a multiprocess (nonblocking) poll so that self.x, self.y are
        always accessible (but hogs resources)
        """
        self.stop()
        self.__p = multiprocessing.Process(target=_run_client,
                                           args=(self.__chan1, self.__chan2),
                                           kwargs=self.__serialkwds)
        self.__p.start()
        
    def stop(self):
        try:
            self.__p.terminate()
        except AttributeError:
            pass
        
    def __delete__(self):
        try:
            self.__serial.close()
        except AttributeError:
            pass
        try:
            self.__ve.terminate()
        except AttributeError:
            pass
        try:
            self.__screen.close()
        except AttributeError:
            pass
        
        self.stop()
        
    def serve(self, samples=None, demo=False):
        from array import array
        #self.__serial = _serial(**self.__serialkwds)
        #data = array('f', [array('f', 'DDDD')[0], 0,0])
        chanx = 3; chany = 4;
        
        try:
            from glue.UniversalLibrary import Daq, cbw, constants
            if demo or cbw.TESTMODE: raise ImportError()
            daq = Daq(1000, LowChan=3, HighChan=4)
            getChannels = daq.getCurrent
            daq.startBackground(Options=constants.SINGLEIO)#Default DMA option has too much latency for low IO rates
        except ImportError:
            def getChannels(): # Fake data for debugging
                import numpy as N
                from time import time
                t = time()
                return (t, (5*N.cos(2*N.pi*(t + N.arange(2)/4.))))
        count = 0
        t0=time()

        while True:
            t, xy = getChannels()
            self.__send.encode(self.EYE_STRUCT, t, *(4*xy))
            #self.__serial.write(data.tostring())
            count += 1
            if samples and count >= samples:
                break
            sleep(.001)
        return samples/(time()-t0)
            
    def startVE(self):
        import pygame
        from pygame.locals import QUIT, KEYDOWN, K_ESCAPE
        from VisionEgg.Core import Viewport, Screen, OrthographicProjection, FixationSpot, swap_buffers
        from VisionEgg.Textures import FixationCross
        size=(800, 600)
        ppd = size[1]/40.
        
        screen = Screen(size=size, fullscreen=False, sync_swap=True, bgcolor=(.5, .5, .5))
        projection = OrthographicProjection(left=-size[0]/(2*ppd),
                                            right=size[0]/(2*ppd),
                                            top=size[1]/(2*ppd),
                                            bottom=-size[1]/(2*ppd))
        fix = FixationSpot(position=(0,0), size=(.5, .5))
        gridvals = [-20, -10, -5, -1, 0, 1, 5, 10, 20]
        grid = [FixationSpot(size=(.1,.1), position=(x,y), color=(0,0,0)) for x in gridvals for y in gridvals]
        viewport = Viewport(projection=projection, screen=screen, stimuli=grid+[FixationCross(size=(2,2), position=(0,0)), fix])
        #def getPosition(t):
            #return self.getXY()
        #p = Presentation(go_duration=('forever',), viewports=[viewport])
        #p.add_controller(fix, 'position', FunctionController(during_go_func=getPosition))
        
        #p.go()
        quit_now=False
        while not quit_now:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key in [K_ESCAPE]):
                    quit_now = True
                    break
            screen.clear()
            (t,xy)= self.getXY()
            fix.parameters.position = xy
            viewport.draw()
            swap_buffers() # display what we've drawn
            
        screen.close()


def testServer():
    print iSCAN().serve(samples=50000)
def testVE():
    iSCAN().startVE()
def testClient():
    i = iSCAN()
    t1 = time()
    i.start()
    print time()-t1
    #N=1000000
    #x = pylab.zeros(N); y = pylab.zeros(N); t = pylab.zeros(N);
    #for n in range(N):
        #x[n] = i.x; y[n] = i.y; t[n] = time()
    count=0
    t0 = time()
    while time() - t1 < 15:
        #i.scatter()
        count+=1
        print i.x, i.y
    i.stop()
    #pylab.plot(x, y)
    print count/(time()-t0)
    #pylab.show()
    #pylab.show()
    print 'done!'
    
if __name__ == '__main__':
    #testServer()

    testVE()
