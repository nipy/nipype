import datetime
import logging

def log_nodes_cb(node, status, result=None):
    print 'status', status
    logger = logging.getLogger('callback')
    if status == 'start':
        message  = '{"name":' + '"' + node.name + '"' + ',"id":' + '"' +\
        node._id + '"' + ',"start":' + '"' +str(datetime.datetime.now()) +\
        '"' + ',"estimate memory":' + str(node._interface.estimated_memory) + ',"num_threads":' \
        + str(node._interface.num_threads) + '}'

        logger.debug(message)

    elif status == 'end':
        message  = '{"name":' + '"' + node.name + '"' + ',"id":' + '"' + \
        node._id + '"' + ',"finish":' + '"' + str(datetime.datetime.now()) +\
        '"' + ',"memory":' + str(node._interface.estimated_memory) + ',"num_threads":' \
        + str(node._interface.num_threads) + ',"real memory":' + str(result['real_memory']) + '}'

        logger.debug(message)

    else:
        message  = '{"name":' + '"' + node.name + '"' + ',"id":' + '"' + \
        node._id + '"' + ',"finish":' + '"' + str(datetime.datetime.now()) +\
        '"' + ',"memory":' + str(node._interface.estimated_memory) + ',"num_threads":' \
        + str(node._interface.num_threads) + ',"error":"True"}'

        logger.debug(message)
