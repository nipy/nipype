from __future__ import print_function, division, unicode_literals, absolute_import
from builtins import object
from collections import defaultdict

from future import standard_library
standard_library.install_aliases()

import os, pdb, time, glob
import itertools, collections
import queue

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
        for (i, ind) in enumerate(itertools.product(*node.state.all_elements)):
            self._submit_work_el(node, i, ind)

    def _submit_work_el(self, node, i, ind):
        logger.debug("SUBMIT WORKER, node: {}, ind: {}".format(node, ind))
        self.worker.run_el(node.run_interface_el, (i, ind))


    def close(self):
        self.worker.close()



class SubmitterNode(Submitter):
    def __init__(self, plugin, node):
        super(SubmitterNode, self).__init__(plugin)
        self.node = node

    def run_node(self):
        self.submit_work(self.node)

        while not self.node.global_done:
            logger.debug("Submitter, in while, to_finish: {}".format(self.node))
            time.sleep(3)


class SubmitterWorkflow(Submitter):
    def __init__(self, graph, plugin):
        super(SubmitterWorkflow, self).__init_(plugin)
        self.graph = graph
        logger.debug('Initialize Submitter, graph: {}'.format(graph))
        self._to_finish = list(self.graph)


    def run_workflow(self):
        for (i_n, node) in enumerate(self.graph):
            # submitting all the nodes who are self sufficient (self.graph is already sorted)
            if node.sufficient:
                self.submit_work(node)
            # if its not, its been added to a line
            else:
                break

            # in case there is no element in the graph that goes to the break
            # i want to be sure that not calculating the last node again in the next for loop
            if i_n == len(self.graph) - 1:
                i_n += 1

            # adding task for reducer
            if node._join_interface:
                # decided to add it as one task, since I have to wait for everyone before  can start it anyway
                self.node_line.append((node, "join", None))


        # all nodes that are not self sufficient will go to the line
        # iterating over all elements
        # (i think ordered list work well here, since it's more efficient to check within a specific order)
        for nn in self.graph[i_n:]:
            for (i, ind) in enumerate(itertools.product(*nn.state.all_elements)):
                self.node_line.append((nn, i, ind))
            if nn._join_interface:
                # decided to add it as one task, since I have to wait for everyone before can start it anyway
                self.node_line.append((nn, "join", None))


        # this parts submits nodes that are waiting to be run
        # it should stop when nothing is waiting
        while self._nodes_check():
            logger.debug("Submitter, in while, node_line: {}".format(self.node_line))
            time.sleep(3)

        # TODO(?): combining two while together
        # this part simply waiting for all "last nodes" to finish
        while self._output_check():
            logger.debug("Submitter, in while, to_finish: {}".format(self._to_finish))
            time.sleep(3)


    # for now without callback, so checking all nodes(with ind) in some order
    def _nodes_check(self):
        _to_remove = []
        for (to_node, i, ind) in self.node_line:
            if i == "join":
                if to_node.global_done: #have to check if interface has finished
                    self.submit_join_work(to_node)
                    _to_remove.append((to_node, i, ind))
                else:
                    pass
            else:
                if to_node.checking_input_el(ind):
                    self._submit_work_el(to_node, i, ind)
                    _to_remove.append((to_node, i, ind))
                else:
                    pass
        # can't remove during iterating
        for rn in _to_remove:
            self.node_line.remove(rn)
        return self.node_line


    # this I believe can be done for entire node
    def _output_check(self):
        _to_remove = []
        for node in self._to_finish:
            print("_output check node", node,node.global_done, node._join_interface, node._global_done_join )
            if node.global_done:
                if node._join_interface:
                    if node.global_done_join:
                        _to_remove.append(node)
                else:
                    _to_remove.append(node)
        for rn in _to_remove:
            self._to_finish.remove(rn)
        return self._to_finish


    def submit_join_work(self, node):
        logger.debug("SUBMIT JOIN WORKER, node: {}".format(node))
        for (state_redu, res_redu) in node.result[node._join_interface_input]: # TODO, should be more general than out
            res_redu_l = [i[1] for i in res_redu]
            self.worker.run_el(node.run_interface_join_el, (state_redu, res_redu_l))
