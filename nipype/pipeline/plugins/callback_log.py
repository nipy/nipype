# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Callback logger for recording workflow and node run stats
"""

# Import packages
import datetime
import logging

# Log node stats function
def log_nodes_cb(node, status):
    """Function to record node run statistics to a log file as json
    dictionaries
    """

    # Init variables
    logger = logging.getLogger('callback')

    # Check runtime profile stats
    if node.result is not None:
        try:
            runtime = node.result.runtime
            runtime_memory_gb = runtime.runtime_memory_gb
            runtime_threads = runtime.runtime_threads
        except:
            runtime_memory_gb = runtime_threads = 'Unkown'
    else:
        runtime_memory_gb = runtime_threads = 'N/A'

    # Check status and write to log
    # Start
    if status == 'start':
        message  = '{"name":' + '"' + node.name + '"' + ',"id":' + '"' +\
        node._id + '"' + ',"start":' + '"' +str(datetime.datetime.now()) +\
        '"' + ',"estimated_memory_gb":' + str(node._interface.estimated_memory_gb) + \
        ',"num_threads":' + str(node._interface.num_threads) + '}'

        logger.debug(message)
    # End
    elif status == 'end':
        message  = '{"name":' + '"' + node.name + '"' + ',"id":' + '"' + \
        node._id + '"' + ',"finish":' + '"' + str(datetime.datetime.now()) +  \
        '"' + ',"estimated_memory_gb":' + '"'+ str(node._interface.estimated_memory_gb) + \
        '"'+ ',"num_threads":' + '"'+ str(node._interface.num_threads) + '"'+ \
        ',"runtime_threads":' + '"'+ str(runtime_threads) + '"'+ \
        ',"runtime_memory_gb":' + '"'+ str(runtime_memory_gb) + '"' + '}'

        logger.debug(message)
    # Other
    else:
        message  = '{"name":' + '"' + node.name + '"' + ',"id":' + '"' + \
        node._id + '"' + ',"finish":' + '"' + str(datetime.datetime.now()) +\
        '"' + ',"estimated_memory_gb":' + str(node._interface.estimated_memory_gb) + \
        ',"num_threads":' + str(node._interface.num_threads) + ',"error":"True"}'

        logger.debug(message)
