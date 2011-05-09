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
import time
import unittest

from traits.util.Worker import Worker

def slow_eval(worker, sleep_time):
    for i in range(10):
        if worker.abort():
            return
        else:
            # pretend to do some intensive computation
            time.sleep(sleep_time)
            print worker.getName(),' sleeping for: ', sleep_time
    return sleep_time

snooze = 0.1

class test_worker_thread(unittest.TestCase):

    def test_cancel(self):
        start = time.time()
        worker = Worker(name = "First EnVisage worker thread")
        worker.perform_work(slow_eval, snooze)
        worker.start()
        time.sleep(3 * snooze)
        worker.cancel()

        worker = Worker(name = "Second EnVisage worker thread")
        worker.perform_work(slow_eval, snooze)
        worker.start()
        time.sleep(2 * snooze)
        worker.cancel()

        duration = time.time() - start
        self.assert_(duration >= 5.0 * snooze)
        self.assert_(duration < 10.0 * snooze)

    def test_concurrent(self):
        start = time.time()

        worker = Worker(name = "First EnVisage worker thread")
        worker.perform_work(slow_eval, snooze)
        worker.start()

        worker = Worker(name = "Second EnVisage worker thread")
        worker.perform_work(slow_eval, snooze)
        worker.start()

        duration = time.time() - start
        print duration

        # !! todo block on completion and check it is less than twice
        # the time for a single thread
