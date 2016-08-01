from __future__ import print_function
import os
import sys
from shutil import rmtree, copyfile
from multiprocessing import cpu_count


def run_examples(example, pipelines, data_path, plugin=None):
    '''
    Run example workflows
    '''

    # Import packages
    from nipype import config
    from nipype.interfaces.base import CommandLine
    from nipype.utils import draw_gantt_chart
    from nipype.pipeline.plugins import log_nodes_cb

    if plugin is None:
        plugin = 'MultiProc'

    print('running example: %s with plugin: %s' % (example, plugin))
    config.enable_debug_mode()
    config.enable_provenance()
    CommandLine.set_default_terminal_output("stream")

    plugin_args = {}
    if plugin == 'MultiProc':
        plugin_args['n_procs'] = cpu_count()

    __import__(example)

    for pipeline in pipelines:
        # Init and run workflow
        wf = getattr(sys.modules[example], pipeline)
        wf.base_dir = os.path.join(os.getcwd(), 'output', example, plugin)
        if os.path.exists(wf.base_dir):
            rmtree(wf.base_dir)

        # Handle a logging directory
        log_dir = os.path.join(os.getcwd(), 'logs', example)
        if os.path.exists(log_dir):
            rmtree(log_dir)
        os.makedirs(log_dir)
        wf.config = {'execution': {'hash_method': 'timestamp',
                                   'stop_on_first_rerun': 'true',
                                   'write_provenance': 'true'}}

        # Callback log setup
        if example == 'fmri_spm_nested' and plugin == 'MultiProc' and \
           pipeline == 'l2pipeline':
            # Init callback log
            import logging
            cb_log_path = os.path.join(os.path.expanduser('~'), 'callback.log')
            cb_logger = logging.getLogger('callback')
            cb_logger.setLevel(logging.DEBUG)
            handler = logging.FileHandler(cb_log_path)
            cb_logger.addHandler(handler)
            plugin_args = {'n_procs' : 4, 'status_callback' : log_nodes_cb}
        else:
            plugin_args = {'n_procs' : 4}
        try:
            wf.inputs.inputnode.in_data = os.path.abspath(data_path)
        except AttributeError:
            pass # the workflow does not have inputnode.in_data

        wf.run(plugin=plugin, plugin_args=plugin_args)

        # Draw gantt chart only if pandas is installed
        try:
            import pandas
            pandas_flg = True
        except ImportError as exc:
            pandas_flg = False

        if plugin_args.has_key('status_callback') and pandas_flg:
            draw_gantt_chart.generate_gantt_chart(cb_log_path, 4)
            dst_log_html = os.path.join(os.path.expanduser('~'), 'callback.log.html')
            copyfile(cb_log_path+'.html', dst_log_html)

if __name__ == '__main__':
    path, file = os.path.split(__file__)
    sys.path.insert(0, os.path.realpath(os.path.join(path, '..', 'examples')))
    examples = {'fmri_fsl_reuse': ['level1_workflow'],
                'fmri_spm_nested': ['level1', 'l2pipeline'],
                # 'fmri_spm_dartel':['level1','l2pipeline'],
                # 'fmri_fsl_feeds':['l1pipeline']
                }
    example = sys.argv[1]
    plugin = sys.argv[2]
    data_path = sys.argv[3]
    pipelines = sys.argv[4:]
    run_examples(example, pipelines, data_path, plugin)
