# -*- coding: utf-8 -*-
""" Test the nipype interface caching mechanism
"""

from .. import Memory
from ...pipeline.engine.tests.test_engine import EngineTestInterface

from ... import config

config.set_default_config()

nb_runs = 0


class SideEffectInterface(EngineTestInterface):
    def _run_interface(self, runtime):
        global nb_runs
        nb_runs += 1
        return super(SideEffectInterface, self)._run_interface(runtime)


def test_caching(tmpdir):
    old_rerun = config.get("execution", "stop_on_first_rerun")
    try:
        # Prevent rerun to check that evaluation is computed only once
        config.set("execution", "stop_on_first_rerun", "true")
        mem = Memory(tmpdir.strpath)
        first_nb_run = nb_runs
        results = mem.cache(SideEffectInterface)(input1=2, input2=1)
        assert nb_runs == first_nb_run + 1
        assert results.outputs.output1 == [1, 2]
        results = mem.cache(SideEffectInterface)(input1=2, input2=1)
        # Check that the node hasn't been rerun
        assert nb_runs == first_nb_run + 1
        assert results.outputs.output1 == [1, 2]
        results = mem.cache(SideEffectInterface)(input1=1, input2=1)
        # Check that the node hasn been rerun
        assert nb_runs == first_nb_run + 2
        assert results.outputs.output1 == [1, 1]
    finally:
        config.set("execution", "stop_on_first_rerun", old_rerun)
