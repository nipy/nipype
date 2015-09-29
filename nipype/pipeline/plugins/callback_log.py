import datetime
import logging

def log_nodes_cb(node, status):
    logger = logging.getLogger('callback')
    if status == 'start':
        message  = "name:",node.name, "id:", node._id, "start:", datetime.datetime.now(), "memory:", node._interface.memory, "num_threads:", node._interface.num_threads
        logger.debug(message)
    else:
        message  = "name:",node.name, "id:", node._id, "finish:", datetime.datetime.now(), "memory:", node._interface.memory, "num_threads:", node._interface.num_threads
        logger.debug(message)