from __future__ import print_function, division, unicode_literals, absolute_import
from builtins import object

from future import standard_library
standard_library.install_aliases()

import os, pdb, time
from copy import deepcopy

from .workers import MpWorker, SerialWorker, DaskWorker, ConcurrentFuturesWorker

from ... import config, logging
logger = logging.getLogger('nipype.workflow')


class Submitter(object):
    # TODO: runnable in init or run
    def __init__(self, plugin, runnable):
        self.plugin = plugin
        self.node_line = []
        self._to_finish = [] # used only for wf
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

        if hasattr(runnable, 'interface'): # a node
            self.node = runnable
        elif hasattr(runnable, "graph"): # a workflow
            self.workflow = runnable
        else:
            raise Exception("runnable has to be a Node or Workflow")


    def run(self):
        """main running method, checks if submitter id for Node or Workflow"""
        if hasattr(self, "node"):
            self.run_node()
        elif hasattr(self, "workflow"):
            self.run_workflow()


    def run_node(self):
        """the main method to run a Node"""
        self.node.prepare_state_input()
        self._submit_node(self.node)
        while not self.node.is_complete:
            logger.debug("Submitter, in while, to_finish: {}".format(self.node))
            time.sleep(3)
        self.node.get_output()


    def _submit_node(self, node):
        """submitting nodes's interface for all states"""
        for (i, ind) in enumerate(node.state.index_generator):
            self._submit_node_el(node, i, ind)

    def _submit_node_el(self, node, i, ind):
        """submitting node's interface for one element of states"""
        logger.debug("SUBMIT WORKER, node: {}, ind: {}".format(node, ind))
        self.worker.run_el(node.run_interface_el, (i, ind))


    def run_workflow(self, workflow=None, ready=True):
        """the main function to run Workflow"""
        if not workflow:
            workflow = self.workflow
        workflow.prepare_state_input()

        # TODO: should I have inner_nodes for all workflow (to avoid if wf.mapper)??
        if workflow.mapper:
            for key in workflow._node_names.keys():
                workflow.inner_nodes[key] = []
            for (i, ind) in enumerate(workflow.state.index_generator):
                new_workflow = deepcopy(workflow)
                new_workflow.parent_wf = workflow
                if ready:
                    self._run_workflow_el(new_workflow, i, ind)
                else:
                    self.node_line.append((new_workflow, i, ind))
        else:
            if ready:
                if workflow.print_val:
                        workflow.preparing(wf_inputs=workflow.inputs)
                else:
                    inputs_ind = dict((key, None) for (key, _) in workflow.inputs)
                    workflow.preparing(wf_inputs=workflow.inputs, wf_inputs_ind=inputs_ind)
                self._run_workflow_nd(workflow=workflow)
            else:
                self.node_line.append((workflow, 0, ()))

        # this parts submits nodes that are waiting to be run
        # it should stop when nothing is waiting
        while self._nodes_check():
            logger.debug("Submitter, in while, node_line: {}".format(self.node_line))
            time.sleep(3)

        # this part simply waiting for all "last nodes" to finish
        while self._output_check():
            logger.debug("Submitter, in while, to_finish: {}".format(self._to_finish))
            time.sleep(3)

        # calling only for the main wf (other wf will be called inside the function)
        if workflow is self.workflow:
            workflow.get_output()


    def _run_workflow_el(self, workflow, i, ind, collect_inp=False):
        """running one internal workflow (if workflow has a mapper)"""
        # TODO: can I simplify and remove collect inp? where should it be?
        if collect_inp:
            st_inputs, wf_inputs = workflow._collecting_input_el(ind)
        else:
            wf_inputs = workflow.state.state_values(ind)
        if workflow.print_val:
            workflow.preparing(wf_inputs=wf_inputs)
        else:
            wf_inputs_ind = workflow.state.state_ind(ind)
            workflow.preparing(wf_inputs=wf_inputs, wf_inputs_ind=wf_inputs_ind)
        self._run_workflow_nd(workflow=workflow)


    def _run_workflow_nd(self, workflow):
        """iterating over all nodes from a workflow and submitting them or adding to the node_line"""
        for (i_n, node) in enumerate(workflow.graph_sorted):
            if workflow.parent_wf and workflow.parent_wf.mapper: # for now if parent_wf, parent_wf has to have mapper
                workflow.parent_wf.inner_nodes[node.name].append(node)
            node.prepare_state_input()
            self._to_finish.append(node)
            # submitting all the nodes who are self sufficient (self.workflow.graph is already sorted)
            if node.ready2run:
                if hasattr(node, 'interface'):
                    self._submit_node(node)
                else:  # it's workflow
                    self.run_workflow(workflow=node)
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
            if hasattr(nn, 'interface'):
                for (i, ind) in enumerate(nn.state.index_generator):
                    self._to_finish.append(nn)
                    self.node_line.append((nn, i, ind))
            else: #wf
                self.run_workflow(workflow=nn, ready=False)


    def _nodes_check(self):
        """checking which nodes-states are ready to run and running the ones that are ready"""
        _to_remove = []
        for (to_node, i, ind) in self.node_line:
            if hasattr(to_node, 'interface'):
                if to_node.checking_input_el(ind):
                    self._submit_node_el(to_node, i, ind)
                    _to_remove.append((to_node, i, ind))
                else:
                    pass
            else: #wf
                if to_node.checking_input_el(ind):
                    self._run_workflow_el(workflow=to_node, i=i, ind=ind, collect_inp=True)
                    _to_remove.append((to_node, i, ind))
                else:
                    pass

        # can't remove during iterating
        for rn in _to_remove:
            self.node_line.remove(rn)
        return self.node_line


    # this I believe can be done for entire node
    def _output_check(self):
        """"checking if all nodes are done"""
        _to_remove = []
        for node in self._to_finish:
            print("_output check node", node, node.is_complete)
            if node.is_complete:
                _to_remove.append(node)
        for rn in _to_remove:
            self._to_finish.remove(rn)
        return self._to_finish


    def close(self):
        self.worker.close()
