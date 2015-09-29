import logging
import datetime

def log_nodes_cb(node, status):
    if status == 'start':
        print 'START', "name:",node.name, "id:", node._id, "start:", datetime.datetime.now(), "memory:", node._interface.memory,"num_threads:", node._interface.num_threads
        logging.debug(
            "name:",node.name, 
            "id:", node._id, 
            "start:", datetime.datetime.now(), 
            "memory:", node._interface.memory, 
            "num_threads:", node._interface.num_threads)
    else:
        print 'FINISH', "name:",node.name, "id:", node._id, "finish:", datetime.datetime.now(), "memory:", node._interface.memory,"num_threads:", node._interface.num_threads
        logging.debug(
            "name:",node.name, 
            "id:", node._id, 
            "finish:", datetime.datetime.now(), 
            "memory:", node._interface.memory, 
            "num_threads:", node._interface.num_threads)