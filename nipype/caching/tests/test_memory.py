""" Test the nipype interface caching mechanism
"""

from tempfile import mkdtemp
from shutil import rmtree

from nose.tools import assert_equal

from nipype.caching import Memory
from nipype.pipeline.tests.test_engine import TestInterface
from nipype.utils.config import NipypeConfig
config = NipypeConfig()
config.set_default_config()

nb_runs = 0


class SideEffectInterface(TestInterface):

    def _run_interface(self, runtime):
        global nb_runs
        nb_runs += 1
        runtime.returncode = 0
        return runtime


def test_caching():
    temp_dir = mkdtemp(prefix='test_memory_')
    old_rerun = config.get('execution', 'stop_on_first_rerun')
    try:
        # Prevent rerun to check that evaluation is computed only once
        config.set('execution', 'stop_on_first_rerun', 'true')
        mem = Memory(temp_dir)
        first_nb_run = nb_runs
        results = mem.cache(SideEffectInterface)(input1=2, input2=1)
        assert_equal(nb_runs, first_nb_run + 1)
        assert_equal(results.outputs.output1, [1, 2])
        results = mem.cache(SideEffectInterface)(input1=2, input2=1)
        # Check that the node hasn't been rerun
        assert_equal(nb_runs, first_nb_run + 1)
        assert_equal(results.outputs.output1, [1, 2])
        results = mem.cache(SideEffectInterface)(input1=1, input2=1)
        # Check that the node hasn been rerun
        assert_equal(nb_runs, first_nb_run + 2)
        assert_equal(results.outputs.output1, [1, 1])
    finally:
        rmtree(temp_dir)
        config.set('execution', 'stop_on_first_rerun', old_rerun)


if __name__ == '__main__':
    test_caching()

