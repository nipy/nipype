import os
import sys
from shutil import rmtree


def run_examples(example, pipelines, plugin):
    print 'running example: %s with plugin: %s'%(example, plugin)
    __import__(example)
    for pipeline in pipelines:
        wf = getattr(sys.modules[example], pipeline)
        wf.base_dir = os.path.join(os.getcwd(),example, plugin)
        if os.path.exists(wf.base_dir):
            rmtree(wf.base_dir)
        wf.config = {'execution' :{'hash_method': 'timestamp', 'stop_on_first_rerun': 'true'}}
        wf.run(plugin=plugin)
        #run twice to check if nothing is rerunning
        wf.run(plugin=plugin)

if __name__ == '__main__':
    path, file = os.path.split(__file__)
    sys.path.insert(0, os.path.realpath(os.path.join(path, '..', 'examples')))
    examples = {'fsl_tutorial2':['l1pipeline'],
                'spm_tutorial2':['level1','l2pipeline'],
                'spm_dartel_tutorial':['level1','l2pipeline'],
                'fsl_feeds_tutorial':['l1pipeline']}
    plugins = ['Linear', 'MultiProc', 'IPython']
    for plugin in plugins:
        for example, pipelines in examples.items():
            run_examples(example, pipelines, plugin)
    
