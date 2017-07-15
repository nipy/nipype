# coding: utf-8
from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu
def square(x):
    return x ** 2
def increment(x):
    return x + 1

if __name__ == '__main__':
    sq = pe.Node(niu.Function(function=square), name='sq')
    inc = pe.Node(niu.Function(function=increment), name='inc')
    sq.inputs.x = 5
    wf = pe.Workflow(name='fun_wf', base_dir='/tmp')
    wf.connect([(sq, inc, [('out', 'x')])])
    wf.run(plugin='Dask')
