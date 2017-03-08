# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import pytest
import os
import numpy as np

from .....testing import utils
from .....interfaces import IdentityInterface
from .....pipeline.engine import Node, Workflow

from ..resting import create_resting_preproc

def test_create_resting():
    wf = create_resting_preproc()
