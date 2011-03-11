# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Common graph operations for execution
"""

import logging
import os
import pwd
from socket import gethostname
import sys
from time import strftime
from traceback import format_exception

import numpy as np

logger = logging.getLogger('workflow')

def report_crash(node, traceback=None):
    """Writes crash related information to a file
    """
    name = node._id
    if node.result and hasattr(node.result, 'runtime') and \
            node.result.runtime:
        if isinstance(node.result.runtime, list):
            host = node.result.runtime[0].hostname
        else:
            host = node.result.runtime.hostname
    else:
        host = gethostname()
    message = ['Node %s failed to run on host %s.' % (name,
                                                      host)]
    logger.error(message)
    if not traceback:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback = format_exception(exc_type,
                                     exc_value,
                                     exc_traceback)
    timeofcrash = strftime('%Y%m%d-%H%M%S')
    login_name = pwd.getpwuid(os.geteuid())[0]
    crashfile = 'crash-%s-%s-%s.npz' % (timeofcrash,
                                        login_name,
                                        name)
    if hasattr(node, 'config') and ('crashdump_dir' in node.config.keys()):
        if not os.path.exists(node.config['crashdump_dir']):
            os.makedirs(node.config['crashdump_dir'])
        crashfile = os.path.join(node.config['crashdump_dir'],
                                 crashfile)
    else:
        crashfile = os.path.join(os.getcwd(), crashfile)
    logger.info('Saving crash info to %s' % crashfile)
    logger.info(''.join(traceback))
    np.savez(crashfile, node=node, traceback=traceback)
    return crashfile

def report_nodes_not_run(notrun):
    """List nodes that crashed with crashfile info

    Optionally displays dependent nodes that weren't executed as a result of
    the crash.
    """
    if notrun:
        logger.info("***********************************")
        for info in notrun:
            logger.error("could not run node: %s" % '.'.join((info['node']._hierarchy,info['node']._id)))
            logger.info("crashfile: %s" % info['crashfile'])
            logger.debug("The following dependent nodes were not run")
            for subnode in info['dependents']:
                logger.debug(subnode._id)
        logger.info("***********************************")
        raise RuntimeError('Workflow did not execute cleanly. Check log for details')

class PluginBase(object):
    """Base class for plugins"""

    def run(self, graph):
        raise NotImplementedError

