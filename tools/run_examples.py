import os
import sys
from shutil import rmtree


def run_examples(example, pipelines, plugin):
    print 'running example: %s with plugin: %s'%(example, plugin)
    from nipype.utils.config import NipypeConfig
    config = NipypeConfig()
    config.enable_debug_mode()
    __import__(example)
    for pipeline in pipelines:
        wf = getattr(sys.modules[example], pipeline)
        wf.base_dir = os.path.join(os.getcwd(), 'output', example, plugin)
        if os.path.exists(wf.base_dir):
            rmtree(wf.base_dir)
        wf.config = {'execution' :{'hash_method': 'timestamp', 'stop_on_first_rerun': 'true'}}
        wf.run(plugin=plugin, plugin_args={'n_procs': 4})
        #run twice to check if nothing is rerunning
        wf.run(plugin=plugin)

if __name__ == '__main__':
    path, file = os.path.split(__file__)
    sys.path.insert(0, os.path.realpath(os.path.join(path, '..', 'examples')))
    examples = {'fmri_fsl_reuse':['l1pipeline'],
                'fmri_spm_nested':['level1','l2pipeline'],
                'fmri_spm_dartel':['level1','l2pipeline'],
                'fmri_fsl_feeds':['l1pipeline']}
    plugins = ['Linear', 'MultiProc', 'IPython']
    for plugin in plugins:
        for example, pipelines in examples.items():
            run_examples(example, pipelines, plugin)

