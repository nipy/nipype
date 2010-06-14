# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import tempfile
import shutil

from nipype.testing import (assert_equal, assert_not_equal, assert_true,
                            assert_raises)
import nipype.interfaces.fsl as fsl

# XXX Write tests for fsl_model

