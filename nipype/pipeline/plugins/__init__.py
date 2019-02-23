# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

from .debug import DebugPlugin
from .linear import LinearPlugin
from .pbs import PBSPlugin
from .oar import OARPlugin
from .sge import SGEPlugin
from .condor import CondorPlugin
from .dagman import CondorDAGManPlugin
from .multiproc import MultiProcPlugin
from .legacymultiproc import LegacyMultiProcPlugin
from .ipython import IPythonPlugin
from .somaflow import SomaFlowPlugin
from .pbsgraph import PBSGraphPlugin
from .sgegraph import SGEGraphPlugin
from .lsf import LSFPlugin
from .slurm import SLURMPlugin
from .slurmgraph import SLURMGraphPlugin

from . import semaphore_singleton
