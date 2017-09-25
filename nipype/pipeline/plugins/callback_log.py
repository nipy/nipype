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

    if status != 'end':
        return

    # Import packages
    import logging
    import json

    # Init variables
    logger = logging.getLogger('callback')
    status_dict = {
        'name': node.name,
        'id': node._id,
        'start': getattr(node.result.runtime, 'startTime'),
        'finish': getattr(node.result.runtime, 'endTime'),
        'duration': getattr(node.result.runtime, 'duration'),
        'runtime_threads': getattr(
            node.result.runtime, 'nthreads_max', 'N/A'),
        'runtime_memory_gb': getattr(
            node.result.runtime, 'mem_peak_gb', 'N/A'),
        'estimated_memory_gb': node._interface.estimated_memory_gb,
        'num_threads': node._interface.num_threads,
    }

    if status_dict['start'] is None or status_dict['finish'] is None:
        status_dict['error'] = True

    # Dump string to log
    logger.debug(json.dumps(status_dict))
