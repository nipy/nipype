# -*- coding: utf-8 -*-
# portalocker.py - Cross-platform (posix/nt) API for flock-style file locking.
#                  Requires python 1.5.2 or better.
'''Cross-platform (posix/nt) API for flock-style file locking.

Synopsis:

   import portalocker
   file = open('somefile', 'r+')
   portalocker.lock(file, portalocker.LOCK_EX)
   file.seek(12)
   file.write('foo')
   file.close()

If you know what you're doing, you may choose to

   portalocker.unlock(file)

before closing the file, but why?

Methods:

   lock( file, flags )
   unlock( file )

Constants:

   LOCK_EX
   LOCK_SH
   LOCK_NB

Exceptions:

    LockException

Notes:

For the 'nt' platform, this module requires the Python Extensions for Windows.
Be aware that this may not work as expected on Windows 95/98/ME.

History:

I learned the win32 technique for locking files from sample code
provided by John Nielsen <nielsenjf@my-deja.com> in the documentation
that accompanies the win32 modules.

Author: Jonathan Feinberg <jdf@pobox.com>,
        Lowell Alleman <lalleman@mfps.com>
Version: $Id: portalocker.py 5474 2008-05-16 20:53:50Z lowell $

'''
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import open

__all__ = [
    'lock',
    'unlock',
    'LOCK_EX',
    'LOCK_SH',
    'LOCK_NB',
    'LockException',
]

import os


class LockException(Exception):
    # Error codes:
    LOCK_FAILED = 1


if os.name == 'nt':
    import win32con
    import win32file
    import pywintypes
    LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
    LOCK_SH = 0  # the default
    LOCK_NB = win32con.LOCKFILE_FAIL_IMMEDIATELY
    # is there any reason not to reuse the following structure?
    __overlapped = pywintypes.OVERLAPPED()
elif os.name == 'posix':
    import fcntl
    LOCK_EX = fcntl.LOCK_EX
    LOCK_SH = fcntl.LOCK_SH
    LOCK_NB = fcntl.LOCK_NB
else:
    raise RuntimeError('PortaLocker only defined for nt and posix platforms')

if os.name == 'nt':

    def lock(file, flags):
        hfile = win32file._get_osfhandle(file.fileno())
        try:
            win32file.LockFileEx(hfile, flags, 0, -0x10000, __overlapped)
        except pywintypes.error as exc_value:
            # error: (33, 'LockFileEx', 'The process cannot access the file
            # because another process has locked a portion of the file.')
            if exc_value[0] == 33:
                raise LockException(LockException.LOCK_FAILED, exc_value[2])
            else:
                # Q: Are there exceptions/codes we should be dealing with here?
                raise

    def unlock(file):
        hfile = win32file._get_osfhandle(file.fileno())
        try:
            win32file.UnlockFileEx(hfile, 0, -0x10000, __overlapped)
        except pywintypes.error as exc_value:
            if exc_value[0] == 158:
                # error: (158, 'UnlockFileEx', 'The segment is already
                # unlocked.') To match the 'posix' implementation, silently
                # ignore this error
                pass
            else:
                # Q: Are there exceptions/codes we should be dealing with here?
                raise

elif os.name == 'posix':

    def lock(file, flags):
        try:
            fcntl.flock(file.fileno(), flags)
        except IOError as exc_value:
            # The exception code varies on different systems so we'll catch
            # every IO error
            raise LockException(*exc_value)

    def unlock(file):
        fcntl.flock(file.fileno(), fcntl.LOCK_UN)


if __name__ == '__main__':
    from time import time, strftime, localtime
    import sys
    from . import portalocker

    log = open('log.txt', 'a+')
    portalocker.lock(log, portalocker.LOCK_EX)
    timestamp = strftime('%m/%d/%Y %H:%M:%S\n', localtime(time()))
    log.write(timestamp)

    print('Wrote lines. Hit enter to release lock.')
    dummy = sys.stdin.readline()
    log.close()
