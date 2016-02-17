import datetime
import logging

def log_nodes_cb(node, status, result=None):
    '''
    '''

    # Init variables
    logger = logging.getLogger('callback')

    # Check runtime profile stats
    if result is None:
        runtime_memory = runtime_seconds = runtime_threads = 'N/A'
    else:
        try:
            runtime_memory = result['runtime_memory']
        except KeyError:
            runtime_memory = 'Unknown'
        try:
            runtime_seconds = result['runtime_seconds']
        except KeyError:
            runtime_seconds = 'Unknown'
        try:
            runtime_threads = result['runtime_threads']
        except:
            runtime_threads = 'Unknown'

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
        ',"runtime_threads":' + '"'+ str(runtime_threads) + '"'+ \
        ',"runtime_memory":' + '"'+ str(runtime_memory) + '"' + \
        ',"runtime_seconds":' + '"'+ str(runtime_seconds) + '"'+ '}'

        logger.debug(message)
    # Other
    else:
        message  = '{"name":' + '"' + node.name + '"' + ',"id":' + '"' + \
        node._id + '"' + ',"finish":' + '"' + str(datetime.datetime.now()) +\
        '"' + ',"estimated_memory":' + str(node._interface.estimated_memory) + ',"num_threads":' \
        + str(node._interface.num_threads) + ',"error":"True"}'

        logger.debug(message)
