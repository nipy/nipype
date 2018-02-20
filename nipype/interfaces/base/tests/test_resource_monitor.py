#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Module to unit test the resource_monitor in nipype
"""

from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
import os
import pytest

# Import packages
from .... import config
from ....utils.profiler import _use_resources
from ...base import traits, CommandLine, CommandLineInputSpec
from ... import utility as niu

# Try to enable the resource monitor
config.enable_resource_monitor()
run_profile = config.resource_monitor


class UseResourcesInputSpec(CommandLineInputSpec):
    mem_gb = traits.Float(
        desc='Number of GB of RAM to use', argstr='-g %f', mandatory=True)
    n_procs = traits.Int(
        desc='Number of threads to use', argstr='-p %d', mandatory=True)


class UseResources(CommandLine):
    """
    use_resources cmd interface
    """
    from nipype import __path__
    # Init attributes
    input_spec = UseResourcesInputSpec

    # Get path of executable
    exec_dir = os.path.realpath(__path__[0])
    exec_path = os.path.join(exec_dir, 'utils', 'tests', 'use_resources')

    # Init cmd
    _cmd = exec_path
    _always_run = True


@pytest.mark.skip(reason="inconsistent readings")
@pytest.mark.skipif(
    os.getenv('CI_SKIP_TEST', False), reason='disabled in CI tests')
@pytest.mark.parametrize("mem_gb,n_procs", [(0.5, 3), (2.2, 8), (0.8, 4),
                                            (1.5, 1)])
def test_cmdline_profiling(tmpdir, mem_gb, n_procs):
    """
    Test runtime profiler correctly records workflow RAM/CPUs consumption
    of a CommandLine-derived interface
    """
    from nipype import config
    config.set('monitoring', 'sample_frequency', '0.2')  # Force sampling fast

    tmpdir.chdir()
    iface = UseResources(mem_gb=mem_gb, n_procs=n_procs)
    result = iface.run()

    assert abs(mem_gb - result.runtime.mem_peak_gb
               ) < 0.3, 'estimated memory error above .3GB'
    assert int(result.runtime.cpu_percent / 100 + 0.2
               ) == n_procs, 'wrong number of threads estimated'


@pytest.mark.skipif(
    True, reason='test disabled temporarily, until funcion profiling works')
@pytest.mark.parametrize("mem_gb,n_procs", [(0.5, 3), (2.2, 8), (0.8, 4),
                                            (1.5, 1)])
def test_function_profiling(tmpdir, mem_gb, n_procs):
    """
    Test runtime profiler correctly records workflow RAM/CPUs consumption
    of a Function interface
    """
    from nipype import config
    config.set('monitoring', 'sample_frequency', '0.2')  # Force sampling fast

    tmpdir.chdir()
    iface = niu.Function(function=_use_resources)
    iface.inputs.mem_gb = mem_gb
    iface.inputs.n_procs = n_procs
    result = iface.run()

    assert abs(mem_gb - result.runtime.mem_peak_gb
               ) < 0.3, 'estimated memory error above .3GB'
    assert int(result.runtime.cpu_percent / 100 + 0.2) >= n_procs
