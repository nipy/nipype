# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Common graph operations for execution"""
import os
import getpass
from socket import gethostname
import sys
import uuid
from time import strftime
from traceback import format_exception

from ... import logging
from ...utils.filemanip import savepkl, crash2txt

logger = logging.getLogger("nipype.workflow")


def report_crash(node, traceback=None, hostname=None):
    """Writes crash related information to a file"""
    name = node._id
    host = None
    traceback = traceback or format_exception(*sys.exc_info())

    try:
        result = node.result
    except FileNotFoundError:
        traceback += """

When creating this crashfile, the results file corresponding
to the node could not be found.""".splitlines(
            keepends=True
        )
    except Exception as exc:
        traceback += """

During the creation of this crashfile triggered by the above exception,
another exception occurred:\n\n{}.""".format(
            exc
        ).splitlines(
            keepends=True
        )
    else:
        if getattr(result, "runtime", None):
            if isinstance(result.runtime, list):
                host = result.runtime[0].hostname
            else:
                host = result.runtime.hostname

    # Try everything to fill in the host
    host = host or hostname or gethostname()
    logger.error("Node %s failed to run on host %s.", name, host)
    timeofcrash = strftime("%Y%m%d-%H%M%S")
    try:
        login_name = getpass.getuser()
    except KeyError:
        login_name = f"UID{os.getuid():d}"
    crashfile = f"crash-{timeofcrash}-{login_name}-{name}-{uuid.uuid4()}"
    crashdir = node.config["execution"].get("crashdump_dir", os.getcwd())

    os.makedirs(crashdir, exist_ok=True)
    crashfile = os.path.join(crashdir, crashfile)

    if node.config["execution"]["crashfile_format"].lower() in ("text", "txt", ".txt"):
        crashfile += ".txt"
    else:
        crashfile += ".pklz"

    logger.error("Saving crash info to %s\n%s", crashfile, "".join(traceback))
    if crashfile.endswith(".txt"):
        crash2txt(crashfile, dict(node=node, traceback=traceback))
    else:
        savepkl(crashfile, dict(node=node, traceback=traceback), versioning=True)
    return crashfile


def report_nodes_not_run(notrun):
    """List nodes that crashed with crashfile info

    Optionally displays dependent nodes that weren't executed as a result of
    the crash.
    """
    if notrun:
        logger.info("***********************************")
        for info in notrun:
            node = info["node"]
            logger.error(f"could not run node: {node._hierarchy}.{node._id}")
            logger.info("crashfile: %s" % info["crashfile"])
            logger.debug("The following dependent nodes were not run")
            for subnode in info["dependents"]:
                logger.debug(subnode._id)
        logger.info("***********************************")


def create_pyscript(node, updatehash=False, store_exception=True):
    # pickle node
    timestamp = strftime("%Y%m%d_%H%M%S")
    if node._hierarchy:
        suffix = f"{timestamp}_{node._hierarchy}_{node._id}"
        batch_dir = os.path.join(node.base_dir, node._hierarchy.split(".")[0], "batch")
    else:
        suffix = f"{timestamp}_{node._id}"
        batch_dir = os.path.join(node.base_dir, "batch")
    if not os.path.exists(batch_dir):
        os.makedirs(batch_dir)
    pkl_file = os.path.join(batch_dir, "node_%s.pklz" % suffix)
    savepkl(pkl_file, dict(node=node, updatehash=updatehash))
    mpl_backend = node.config["execution"]["matplotlib_backend"]
    # create python script to load and trap exception
    cmdstr = """import os
import sys

can_import_matplotlib = True #Silently allow matplotlib to be ignored
try:
    import matplotlib
    matplotlib.use('%s')
except ImportError:
    can_import_matplotlib = False
    pass

import os
value = os.environ.get('NIPYPE_NO_ET', None)
if value is None:
    # disable ET for any submitted job
    os.environ['NIPYPE_NO_ET'] = "1"
from nipype import config, logging

from nipype.utils.filemanip import loadpkl, savepkl
from socket import gethostname
from traceback import format_exception
info = None
pklfile = '%s'
batchdir = '%s'
from nipype.utils.filemanip import loadpkl, savepkl
try:
    from collections import OrderedDict
    config_dict=%s
    config.update_config(config_dict)
    ## Only configure matplotlib if it was successfully imported,
    ## matplotlib is an optional component to nipype
    if can_import_matplotlib:
        config.update_matplotlib()
    logging.update_logging(config)
    traceback=None
    cwd = os.getcwd()
    info = loadpkl(pklfile)
    result = info['node'].run(updatehash=info['updatehash'])
except Exception as e:
    etype, eval, etr = sys.exc_info()
    traceback = format_exception(etype,eval,etr)
    if info is None or not os.path.exists(info['node'].output_dir()):
        result = None
        resultsfile = os.path.join(batchdir, 'crashdump_%s.pklz')
    else:
        result = info['node'].result
        resultsfile = os.path.join(info['node'].output_dir(),
                               'result_%%s.pklz'%%info['node'].name)
"""
    if store_exception:
        cmdstr += """
    savepkl(resultsfile, dict(result=result, hostname=gethostname(),
                              traceback=traceback))
"""
    else:
        cmdstr += """
    if info is None:
        savepkl(resultsfile, dict(result=result, hostname=gethostname(),
                              traceback=traceback))
    else:
        from nipype.pipeline.plugins.base import report_crash
        report_crash(info['node'], traceback, gethostname())
    raise Exception(e)
"""
    cmdstr = cmdstr % (mpl_backend, pkl_file, batch_dir, node.config, suffix)
    pyscript = os.path.join(batch_dir, "pyscript_%s.py" % suffix)
    with open(pyscript, "w") as fp:
        fp.writelines(cmdstr)
    return pyscript
