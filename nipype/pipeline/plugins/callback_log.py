import datetime
import logging

def log_nodes_cb(node, status):
    logger = logging.getLogger('callback')
    if status == 'start':
        message  = '{"name":' + '"' + node.name + '"' + ',"id":' + '"' +\
        node._id + '"' + ',"start":' + '"' +str(datetime.datetime.now()) +\
        '"' + ',"memory":' + str(node._interface.memory) + ',"num_threads":' \
        + str(node._interface.num_threads) +  '}'

        logger.debug(message)
    else:
        message  = '{"name":' + '"' + node.name + '"' + ',"id":' + '"' + \
        node._id + '"' + ',"finish":' + '"' + str(datetime.datetime.now()) +\
        '"' + ',"memory":' + str(node._interface.memory) + ',"num_threads":' \
        + str(node._interface.num_threads) +  '}'

        logger.debug(message)