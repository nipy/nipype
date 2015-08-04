# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from tempfile import mkdtemp
from shutil import rmtree

import numpy as np

import nibabel as nif
from nipype.testing import (assert_equal, assert_not_equal,
                            assert_raises, skipif)
from nipype.interfaces.base import TraitError

import nipype.interfaces.freesurfer as fs
from nipype.interfaces.freesurfer.tests import no_freesurfer
