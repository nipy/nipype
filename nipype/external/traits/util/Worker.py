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
import threading

class Worker(threading.Thread):
    """ Performs numerically intensive computations on a separate thread.

    Computations that take more than ~0.1 second should not be run in the
    same thread as the user interface.

    Typical usage:

    >>> worker = Worker(name = "my worker thread")
    >>> worker.perform_work(my_function_name, args)
    >>> worker.start()
    >>> worker.cancel()
    """

    def __init__(self, **kwds):
        """ Passes the thread constructor a name for the thread.

        Naming threads makes debugging less impossible. The thread is set to be
        a daemon thread, which means that if is the only remaining executing
        thread the program will terminate.
        """
        self._stopevent = threading.Event()
        threading.Thread.__init__(self, **kwds)
        self.setDaemon(True)

    def perform_work(self, callable, *args, **kwds):
        """ Indicates to the thread the method or function and it's arguments.

        When the thread begins to run it will execute 'callable' and pass it
        'args' and 'kwds'
        """
        self.callable = callable
        self.args = args
        self.kwds = kwds

    def run(self):
        """ Private method - used only by the threading.Thread module.

        Users signal a thread should start to run by calling start().
        """
        self.callable(self, *self.args, **self.kwds)

    def cancel(self, timeout = None):
        """ Signals to the worker thread that it should stop computing.

        Calling this method before the thread is started generates an
        exception.
        """
        self._stopevent.set()
        threading.Thread.join(self, timeout)

    def abort(self):
        """ should the algorithm stop computing?
        """
        return self._stopevent.isSet()
