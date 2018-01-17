# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import sys
from shutil import rmtree
from multiprocessing import cpu_count


def run_examples(example, pipelines, data_path, plugin=None, rm_base_dir=True):
    from nipype import config
    from nipype.interfaces.base import CommandLine

    if plugin is None:
        plugin = 'MultiProc'

    print('running example: %s with plugin: %s' % (example, plugin))
    config.enable_debug_mode()
    config.enable_provenance()
    CommandLine.set_default_terminal_output("stream")

    plugin_args = {}
    if plugin == 'MultiProc':
        plugin_args['n_procs'] = int(
            os.getenv('NIPYPE_NUMBER_OF_CPUS', cpu_count()))

    __import__(example)
    for pipeline in pipelines:
        wf = getattr(sys.modules[example], pipeline)
        wf.base_dir = os.path.join(os.getcwd(), 'output', example, plugin)

        results_dir = os.path.join(wf.base_dir, wf.name)
        if rm_base_dir and os.path.exists(results_dir):
            rmtree(results_dir)

        # Handle a logging directory
        log_dir = os.path.join(os.getcwd(), 'logs', example)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        wf.config = {
            'execution': {
                'hash_method': 'timestamp',
                'stop_on_first_rerun': 'true',
                'write_provenance': 'true',
                'poll_sleep_duration': 2
            },
            'logging': {
                'log_directory': log_dir,
                'log_to_file': True
            }
        }
        try:
            wf.inputs.inputnode.in_data = os.path.abspath(data_path)
        except AttributeError:
            pass  # the workflow does not have inputnode.in_data

        wf.run(plugin=plugin, plugin_args=plugin_args)
        # run twice to check if nothing is rerunning
        wf.run(plugin=plugin)


if __name__ == '__main__':
    path, file = os.path.split(__file__)
    sys.path.insert(0, os.path.realpath(os.path.join(path, '..', 'examples')))
    examples = {
        'fmri_fsl_reuse': ['level1_workflow'],
        'fmri_spm_nested': ['level1', 'l2pipeline'],
        # 'fmri_spm_dartel':['level1','l2pipeline'],
        # 'fmri_fsl_feeds':['l1pipeline']
    }
    example = sys.argv[1]
    plugin = sys.argv[2]
    data_path = sys.argv[3]
    pipelines = sys.argv[4:]
    run_examples(example, pipelines, data_path, plugin)
