# coding: utf-8
from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu
def square(x):
    return x ** 2
def increment(x):
    return x + 1

if __name__ == '__main__':
    sq = pe.MapNode(niu.Function(function=square), iterfield=['x'], name='sq')
    sq.inputs.x = [5, 4, 3]
    inc = pe.MapNode(niu.Function(function=increment), iterfield=['x'], name='inc')
    wf = pe.Workflow(name='fun_wf', base_dir='/tmp')
    wf.connect([(sq, inc, [('out', 'x')])])
    wf.run(plugin='Dask')
