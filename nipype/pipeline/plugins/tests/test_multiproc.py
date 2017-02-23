# -*- coding: utf-8 -*-
import logging
import os, sys
from multiprocessing import cpu_count

import nipype.interfaces.base as nib
from nipype.utils import draw_gantt_chart
import pytest
import nipype.pipeline.engine as pe
from nipype.pipeline.plugins.callback_log import log_nodes_cb
from nipype.pipeline.plugins.multiproc import get_system_total_memory_gb

class InputSpec(nib.TraitedSpec):
    input1 = nib.traits.Int(desc='a random int')
    input2 = nib.traits.Int(desc='a random int')


class OutputSpec(nib.TraitedSpec):
    output1 = nib.traits.List(nib.traits.Int, desc='outputs')


class MultiprocTestInterface(nib.BaseInterface):
    input_spec = InputSpec
    output_spec = OutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output1'] = [1, self.inputs.input1]
        return outputs

def test_run_multiproc(tmpdir):
    os.chdir(str(tmpdir))

    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=MultiprocTestInterface(), name='mod1')
    mod2 = pe.MapNode(interface=MultiprocTestInterface(),
                      iterfield=['input1'],
                      name='mod2')
    pipe.connect([(mod1, mod2, [('output1', 'input1')])])
    pipe.base_dir = os.getcwd()
    mod1.inputs.input1 = 1
    pipe.config['execution']['poll_sleep_duration'] = 2
    execgraph = pipe.run(plugin="MultiProc")
    names = ['.'.join((node._hierarchy, node.name)) for node in execgraph.nodes()]
    node = execgraph.nodes()[names.index('pipe.mod1')]
    result = node.get_output('output1')
    assert result == [1, 1]


class InputSpecSingleNode(nib.TraitedSpec):
    input1 = nib.traits.Int(desc='a random int')
    input2 = nib.traits.Int(desc='a random int')


class OutputSpecSingleNode(nib.TraitedSpec):
    output1 = nib.traits.Int(desc='a random int')


class SingleNodeTestInterface(nib.BaseInterface):
    input_spec = InputSpecSingleNode
    output_spec = OutputSpecSingleNode

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output1'] = self.inputs.input1
        return outputs


def find_metrics(nodes, last_node):
    """
    """

    # Import packages
    from dateutil.parser import parse
    import datetime

    start = nodes[0]['start']
    total_duration = int((last_node['finish'] - start).total_seconds())

    total_memory = []
    total_threads = []
    for i in range(total_duration):
        total_memory.append(0)
        total_threads.append(0)

    now = start
    for i in range(total_duration):
        start_index = 0
        node_start = None
        node_finish = None

        x = now

        for j in range(start_index, len(nodes)):
            node_start = nodes[j]['start']
            node_finish = nodes[j]['finish']

            if node_start < x and node_finish > x:
                total_memory[i] += float(nodes[j]['estimated_memory_gb'])
                total_threads[i] += int(nodes[j]['num_threads'])
                start_index = j

            if node_start > x:
                break

        now += datetime.timedelta(seconds=1)

    return total_memory, total_threads

def test_no_more_memory_than_specified():
    LOG_FILENAME = 'callback.log'
    my_logger = logging.getLogger('callback')
    my_logger.setLevel(logging.DEBUG)

    # Add the log message handler to the logger
    handler = logging.FileHandler(LOG_FILENAME)
    my_logger.addHandler(handler)

    max_memory = 1
    pipe = pe.Workflow(name='pipe')
    n1 = pe.Node(interface=SingleNodeTestInterface(), name='n1')
    n2 = pe.Node(interface=SingleNodeTestInterface(), name='n2')
    n3 = pe.Node(interface=SingleNodeTestInterface(), name='n3')
    n4 = pe.Node(interface=SingleNodeTestInterface(), name='n4')

    n1.interface.estimated_memory_gb = 1
    n2.interface.estimated_memory_gb = 1
    n3.interface.estimated_memory_gb = 1
    n4.interface.estimated_memory_gb = 1

    pipe.connect(n1, 'output1', n2, 'input1')
    pipe.connect(n1, 'output1', n3, 'input1')
    pipe.connect(n2, 'output1', n4, 'input1')
    pipe.connect(n3, 'output1', n4, 'input2')
    n1.inputs.input1 = 1

    pipe.run(plugin='MultiProc',
             plugin_args={'memory_gb': max_memory,
                          'status_callback': log_nodes_cb})


    nodes = draw_gantt_chart.log_to_dict(LOG_FILENAME)
    last_node = nodes[-1]
    #usage in every second
    memory, threads = find_metrics(nodes, last_node)

    result = True
    for m in memory:
        if m > max_memory:
            result = False
            break

    assert result

    max_threads = cpu_count()

    result = True
    for t in threads:
        if t > max_threads:
            result = False
            break

    assert result,\
        "using more threads than system has (threads is not specified by user)"

    os.remove(LOG_FILENAME)

def test_no_more_threads_than_specified():
    LOG_FILENAME = 'callback.log'
    my_logger = logging.getLogger('callback')
    my_logger.setLevel(logging.DEBUG)

    # Add the log message handler to the logger
    handler = logging.FileHandler(LOG_FILENAME)
    my_logger.addHandler(handler)

    max_threads = 4
    pipe = pe.Workflow(name='pipe')
    n1 = pe.Node(interface=SingleNodeTestInterface(), name='n1')
    n2 = pe.Node(interface=SingleNodeTestInterface(), name='n2')
    n3 = pe.Node(interface=SingleNodeTestInterface(), name='n3')
    n4 = pe.Node(interface=SingleNodeTestInterface(), name='n4')

    n1.interface.num_threads = 1
    n2.interface.num_threads = 1
    n3.interface.num_threads = 4
    n4.interface.num_threads = 1

    pipe.connect(n1, 'output1', n2, 'input1')
    pipe.connect(n1, 'output1', n3, 'input1')
    pipe.connect(n2, 'output1', n4, 'input1')
    pipe.connect(n3, 'output1', n4, 'input2')
    n1.inputs.input1 = 4
    pipe.config['execution']['poll_sleep_duration'] = 1
    pipe.run(plugin='MultiProc', plugin_args={'n_procs': max_threads,
                                              'status_callback': log_nodes_cb})

    nodes = draw_gantt_chart.log_to_dict(LOG_FILENAME)
    last_node = nodes[-1]
    #usage in every second
    memory, threads = find_metrics(nodes, last_node)

    result = True
    for t in threads:
        if t > max_threads:
            result = False
            break

    assert result, "using more threads than specified"

    max_memory = get_system_total_memory_gb()
    result = True
    for m in memory:
        if m > max_memory:
            result = False
            break
    assert result,\
        "using more memory than system has (memory is not specified by user)"

    os.remove(LOG_FILENAME)
