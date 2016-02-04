import datetime
import logging

def log_nodes_cb(node, status, result=None):
    '''
    '''

    # Init variables
    logger = logging.getLogger('callback')

    # Check runtime profile stats
    if result is None:
        node_mem = cmd_mem = run_seconds = cmd_threads = 'N/A'
    else:
        try:
            node_mem = result['node_memory']
        except KeyError:
            node_mem = 'Unknown'
        try:
            cmd_mem = result['cmd_memory']
        except KeyError:
            cmd_mem = 'Unknown'
        try:
            run_seconds = result['run_seconds']
        except KeyError:
            run_seconds = 'Unknown'
        try:
            cmd_threads = result['cmd_threads']
        except:
            cmd_threads = 'Unknown'

    # Check status and write to log
    # Start
    if status == 'start':
        message  = '{"name":' + '"' + node.name + '"' + ',"id":' + '"' +\
        node._id + '"' + ',"start":' + '"' +str(datetime.datetime.now()) +\
        '"' + ',"estimated_memory":' + str(node._interface.estimated_memory) + ',"num_threads":' \
        + str(node._interface.num_threads) + '}'

        logger.debug(message)
    # End
    elif status == 'end':
        message  = '{"name":' + '"' + node.name + '"' + ',"id":' + '"' + \
        node._id + '"' + ',"finish":' + '"' + str(datetime.datetime.now()) +  \
        '"' + ',"estimated_memory":' + '"'+ str(node._interface.estimated_memory) + '"'+ \
        ',"num_threads":' + '"'+ str(node._interface.num_threads) + '"'+ \
        ',"cmd-level_threads":' + '"'+ str(cmd_threads) + '"'+ \
        ',"node-level_memory":' + '"'+ str(node_mem) + '"'+ \
        ',"cmd-level_memory":' + '"'+ str(cmd_mem) + '"' + \
        ',"run_seconds":' + '"'+ str(run_seconds) + '"'+ '}'

        logger.debug(message)
    # Other
    else:
        message  = '{"name":' + '"' + node.name + '"' + ',"id":' + '"' + \
        node._id + '"' + ',"finish":' + '"' + str(datetime.datetime.now()) +\
        '"' + ',"estimated_memory":' + str(node._interface.estimated_memory) + ',"num_threads":' \
        + str(node._interface.num_threads) + ',"error":"True"}'

        logger.debug(message)
