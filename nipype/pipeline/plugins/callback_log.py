import datetime
import logging

def log_nodes_cb(node, status, result=None):
    logger = logging.getLogger('callback')
    try:
        real_mem1 = result['real_memory']
        real_mem2 = result['real_memory2']
        run_seconds = result['run_seconds']
    except Exception as exc:
        real_mem1 = real_mem2 = run_seconds = 'N/A'
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
        + str(node._interface.num_threads) + ',"real_memory1":' + str(real_mem1) + ',"real_memory2":' + str(real_mem2) + ',"run_seconds":' + str(run_seconds) + '}'

        logger.debug(message)

    else:
        message  = '{"name":' + '"' + node.name + '"' + ',"id":' + '"' + \
        node._id + '"' + ',"finish":' + '"' + str(datetime.datetime.now()) +\
        '"' + ',"memory":' + str(node._interface.estimated_memory) + ',"num_threads":' \
        + str(node._interface.num_threads) + ',"error":"True"}'

        logger.debug(message)
