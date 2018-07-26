# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Additional handy utilities for testing
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import range, object, open

import os
import time
import shutil
import signal
import subprocess
from subprocess import CalledProcessError
from tempfile import mkdtemp
from future.utils import raise_from
from ..utils.misc import package_check

__docformat__ = 'restructuredtext'

import numpy as np
import nibabel as nb


class TempFATFS(object):
    def __init__(self, size_in_mbytes=8, delay=0.5):
        """Temporary filesystem for testing non-POSIX filesystems on a POSIX
        system.

        with TempFATFS() as fatdir:
            target = os.path.join(fatdir, 'target')
            copyfile(file1, target, copy=False)
            assert not os.path.islink(target)

        Arguments
        ---------
        size_in_mbytes : int
            Size (in MiB) of filesystem to create
        delay : float
            Time (in seconds) to wait for fusefat to start, stop
        """
        self.delay = delay
        self.tmpdir = mkdtemp()
        self.dev_null = open(os.devnull, 'wb')

        vfatfile = os.path.join(self.tmpdir, 'vfatblock')
        self.vfatmount = os.path.join(self.tmpdir, 'vfatmount')
        self.canary = os.path.join(self.vfatmount, '.canary')

        with open(vfatfile, 'wb') as fobj:
            fobj.write(b'\x00' * (int(size_in_mbytes) << 20))
        os.mkdir(self.vfatmount)

        mkfs_args = ['mkfs.vfat', vfatfile]
        mount_args = ['fusefat', '-o', 'rw+', '-f', vfatfile, self.vfatmount]

        try:
            subprocess.check_call(
                args=mkfs_args, stdout=self.dev_null, stderr=self.dev_null)
        except CalledProcessError as e:
            raise_from(IOError("mkfs.vfat failed"), e)

        try:
            self.fusefat = subprocess.Popen(
                args=mount_args, stdout=self.dev_null, stderr=self.dev_null)
        except OSError as e:
            raise_from(IOError("fusefat is not installed"), e)

        time.sleep(self.delay)

        if self.fusefat.poll() is not None:
            raise IOError("fusefat terminated too soon")

        open(self.canary, 'wb').close()

    def __enter__(self):
        return self.vfatmount

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fusefat is not None:
            self.fusefat.send_signal(signal.SIGINT)

            # Allow 1s to return without sending terminate
            for count in range(10):
                time.sleep(0.1)
                if self.fusefat.poll() is not None:
                    break
            else:
                self.fusefat.terminate()
            time.sleep(self.delay)
            assert not os.path.exists(self.canary)
        self.dev_null.close()
        shutil.rmtree(self.tmpdir)


def save_toy_nii(ndarray, filename):
    toy = nb.Nifti1Image(ndarray, np.eye(4))
    nb.nifti1.save(toy, filename)
    return filename
