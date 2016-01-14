import datetime
import logging

def log_nodes_cb(node, status, result=None):
    logger = logging.getLogger('callback')
    try:
        node_mem = result['node_memory']
        cmd_mem = result['cmd_memory']
        run_seconds = result['run_seconds']
        cmd_threads = result['cmd_threads']
    except Exception as exc:
        node_mem = cmd_mem = run_seconds = cmd_threads = 'N/A'
    if status == 'start':
        message  = '{"name":' + '"' + node.name + '"' + ',"id":' + '"' +\
        node._id + '"' + ',"start":' + '"' +str(datetime.datetime.now()) +\
        '"' + ',"estimate memory":' + str(node._interface.estimated_memory) + ',"num_threads":' \
        + str(node._interface.num_threads) + '}'

        logger.debug(message)

    elif status == 'end':
        message  = '{"name":' + '"' + node.name + '"' + ',"id":' + '"' + \
        node._id + '"' + ',"finish":' + '"' + str(datetime.datetime.now()) + \
        '"' + ',"estimate memory":' + str(node._interface.estimated_memory) + \
        ',"num_threads":' + str(node._interface.num_threads) + \
        ',"cmd-level threads":' + str(cmd_threads) + \
        ',"node-level memory":' + str(node_mem) + \
        ',"cmd-level memory":' + str(cmd_mem) + \
        ',"run_seconds":' + str(run_seconds) + '}'

        logger.debug(message)

    else:
        message  = '{"name":' + '"' + node.name + '"' + ',"id":' + '"' + \
        node._id + '"' + ',"finish":' + '"' + str(datetime.datetime.now()) +\
        '"' + ',"estimate memory":' + str(node._interface.estimated_memory) + ',"num_threads":' \
        + str(node._interface.num_threads) + ',"error":"True"}'

        logger.debug(message)
