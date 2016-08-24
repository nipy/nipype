# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Callback logger for recording workflow and node run stats
"""
from __future__ import print_function, division, unicode_literals, absolute_import


# Log node stats function
def log_nodes_cb(node, status):
    """Function to record node run statistics to a log file as json
    dictionaries

    Parameters
    ----------
    node : nipype.pipeline.engine.Node
        the node being logged
    status : string
        acceptable values are 'start', 'end'; otherwise it is
        considered and error

    Returns
    -------
    None
        this function does not return any values, it logs the node
        status info to the callback logger
    """

    # Import packages
    import datetime
    import logging
    import json

    # Check runtime profile stats
    if node.result is not None:
        try:
            runtime = node.result.runtime
            runtime_memory_gb = runtime.runtime_memory_gb
            runtime_threads = runtime.runtime_threads
        except AttributeError:
            runtime_memory_gb = runtime_threads = 'Unknown'
    else:
        runtime_memory_gb = runtime_threads = 'N/A'

    # Init variables
    logger = logging.getLogger('callback')
    status_dict = {'name' : node.name,
                   'id' : node._id,
                   'estimated_memory_gb' : node._interface.estimated_memory_gb,
                   'num_threads' : node._interface.num_threads}

    # Check status and write to log
    # Start
    if status == 'start':
        status_dict['start'] = str(datetime.datetime.now())
    # End
    elif status == 'end':
        status_dict['finish'] = str(datetime.datetime.now())
        status_dict['runtime_threads'] = runtime_threads
        status_dict['runtime_memory_gb'] = runtime_memory_gb
    # Other
    else:
        status_dict['finish'] = str(datetime.datetime.now())
        status_dict['error'] = True

    # Dump string to log
    logger.debug(json.dumps(status_dict))
