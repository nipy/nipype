#!/usr/bin/env python
from nipype.pipeline import engine as pe
import nipype.interfaces.utility as niu
from functools import partial
import time

def timeit(func):
    tic = time.time()
    func()
    toc = time.time()
    return toc - tic

def sleeper(arg):
    import time
    time.sleep(5)

if __name__ == '__main__':
    wf1 = pe.Workflow(base_dir='/tmp/nipype', name='wf1')
    node1 = pe.Node(niu.Function(function=sleeper), name='node1')
    node2 = pe.Node(niu.Function(function=sleeper), name='node2')
    node1.inputs.arg = 1
    node2.inputs.arg = 2
    node1.interface.num_threads = 5
    node2.interface.num_threads = 5
    wf1.add_nodes([node1, node2])
    
    wf2 = pe.Workflow(base_dir='/tmp/nipype', name='wf2')
    mapnode = pe.MapNode(niu.Function(function=sleeper), iterfield='arg', name='mapnode')
    mapnode.inputs.arg = [3, 4]
    mapnode.interface.num_threads = 5
    wf2.add_nodes([mapnode])
    
    tic = time.time()
    wf1.run(plugin='Dask')
    toc = time.time()
    time1 = toc - tic
    tic = time.time()
    wf2.run(plugin='Dask')
    toc = time.time()
    time2 = toc - tic
    
    print("Two Nodes: {:.1f}s".format(time1))
    print("MapNode: {:.1f}s".format(time2))
