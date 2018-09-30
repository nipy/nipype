from __future__ import print_function, division, unicode_literals, absolute_import
from builtins import object
from collections import defaultdict

from future import standard_library
standard_library.install_aliases()

import os, pdb, time
from copy import deepcopy

from .workers import MpWorker, SerialWorker, DaskWorker, ConcurrentFuturesWorker

from ... import config, logging
logger = logging.getLogger('nipype.workflow')

class Submitter(object):
    def __init__(self, plugin):
        self.plugin = plugin
        self.node_line = []
        if self.plugin == "mp":
            self.worker = MpWorker()
        elif self.plugin == "serial":
            self.worker = SerialWorker()
        elif self.plugin == "dask":
            self.worker = DaskWorker()
        elif self.plugin == "cf":
            self.worker = ConcurrentFuturesWorker()
        else:
            raise Exception("plugin {} not available".format(self.plugin))


    def submit_work(self, node):
        for (i, ind) in enumerate(node.state.index_generator):
            self._submit_work_el(node, i, ind)

    def _submit_work_el(self, node, i, ind):
        logger.debug("SUBMIT WORKER, node: {}, ind: {}".format(node, ind))
        print("SUBMIT WORK", node.inputs)
        self.worker.run_el(node.run_interface_el, (i, ind))


    def close(self):
        self.worker.close()



class SubmitterNode(Submitter):
    def __init__(self, plugin, node):
        super(SubmitterNode, self).__init__(plugin)
        self.node = node

    def run_node(self):
        self.submit_work(self.node)
        while not self.node.finished_all:
            logger.debug("Submitter, in while, to_finish: {}".format(self.node))
            time.sleep(3)


class SubmitterWorkflow(Submitter):
    def __init__(self, workflow, plugin):
        super(SubmitterWorkflow, self).__init__(plugin)
        self.workflow = workflow
        logger.debug('Initialize Submitter, graph: {}'.format(self.workflow.graph_sorted))
        #self._to_finish = list(self.workflow.graph)
        self._to_finish = []


    def run_workflow(self):
        if self.workflow.mapper:
            self.workflow.inner_nodes = {}
            for key in self.workflow._node_names.keys():
                self.workflow.inner_nodes[key] = []
            for (i, ind) in enumerate(self.workflow.state.index_generator):
                print("LOOP", i, self._to_finish, self.node_line)
                wf_inputs = self.workflow.state.state_values(ind)
                new_workflow = deepcopy(self.workflow)
                #pdb.set_trace()
                new_workflow.preparing(wf_inputs=wf_inputs)
                #pdb.set_trace()
                self.run_workflow_el(workflow=new_workflow)
                print("LOOP END", i, self._to_finish, self.node_line)
        else:
            self.workflow.preparing(wf_inputs=self.workflow.inputs)
            self.run_workflow_el(workflow=self.workflow)

        # this parts submits nodes that are waiting to be run
        # it should stop when nothing is waiting
        while self._nodes_check():
            logger.debug("Submitter, in while, node_line: {}".format(self.node_line))
            time.sleep(3)

        # this part simply waiting for all "last nodes" to finish
        while self._output_check():
            logger.debug("Submitter, in while, to_finish: {}".format(self._to_finish))
            time.sleep(3)


    def run_workflow_el(self, workflow):
        #pdb.set_trace()
        for (i_n, node) in enumerate(workflow.graph_sorted):
            if self.workflow.mapper:
                self.workflow.inner_nodes[node.name].append(node)
            node.prepare_state_input()


            print("RUN WF", node.name, node.inputs)
            self._to_finish.append(node)
            # submitting all the nodes who are self sufficient (self.workflow.graph is already sorted)
            if node.ready2run:

                self.submit_work(node)
            # if its not, its been added to a line
            else:
                break
            # in case there is no element in the graph that goes to the break
            # i want to be sure that not calculating the last node again in the next for loop
            if i_n == len(workflow.graph_sorted) - 1:
                i_n += 1

        # all nodes that are not self sufficient (not ready to run) will go to the line
        # iterating over all elements
        for nn in list(workflow.graph_sorted)[i_n:]:
            for (i, ind) in enumerate(nn.state.index_generator):
                self._to_finish.append(nn)
                self.node_line.append((nn, i, ind))


    # for now without callback, so checking all nodes (with ind) in some order
    def _nodes_check(self):
        print("NODES CHECK BEG", self.node_line)
        _to_remove = []
        for (to_node, i, ind) in self.node_line:
            if to_node.checking_input_el(ind):
                self._submit_work_el(to_node, i, ind)
                _to_remove.append((to_node, i, ind))
            else:
                pass
        # can't remove during iterating
        for rn in _to_remove:
            self.node_line.remove(rn)
        print("NODES CHECK END", self.node_line)
        return self.node_line


    # this I believe can be done for entire node
    def _output_check(self):
        _to_remove = []
        print("OUT CHECK", self._to_finish)
        for node in self._to_finish:
            print("_output check node", node, node.finished_all)
            if node.finished_all:
                _to_remove.append(node)
        for rn in _to_remove:
            self._to_finish.remove(rn)
        print("OUT CHECK END", self._to_finish)
        return self._to_finish