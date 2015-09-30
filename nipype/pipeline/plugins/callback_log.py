import datetime
import logging

def log_nodes_cb(node, status):
    logger = logging.getLogger('callback')
    if status == 'start':
        message  = '{"name":' + '"' + node.name + '"' + ',"id":' + '"' + node._id + '"' + ',"start":' + '"' +str(datetime.datetime.now()) + '"' + ',"memory":' + str(node._interface.memory) + ',"num_threads":' + str(node._interface.num_threads) +  '}'
        logger.debug(message)
    else:
        message  = '{"name":' + '"' + node.name + '"' + ',"id":' + '"' + node._id + '"' + ',"finish":' + '"' + str(datetime.datetime.now()) + '"' + ',"memory":' + str(node._interface.memory) + ',"num_threads":' + str(node._interface.num_threads) +  '}'
        logger.debug(message)



import json
from dateutil import parser

def convert_logcb_to_json(filename):
    with open(filename, 'r') as content:
        #read file separating each line
        content = content.read()
        lines = content.split('\n')

        #separate lines of starting nodes and ending nodes
        starts = [ json.loads(x) for x in lines if '"start":' in x ]
        ends = [json.loads(x) for x in lines if '"finish":' in x ]



        #foreach start, search its end. They have same name and id
        #this line is O(n^2). refactor
        for element in starts:
            end = next((f for f in ends if (f['id'] == element['id'] and  f['name'] == element['name'])), None)

            if end is not None:
                element['finish'] = end['finish']
            else:
                element['finish'] = element['start']


        first_node = starts[0]['start']
        last_node = ends[-1]['finish']

        duration = parser.parse(last_node) - parser.parse(first_node)

        #sorted(starts, key=lambda e: parser.parse(e['start']))   # sort by age
        result = {'start': first_node, 'finish': last_node, 'duration':duration.total_seconds(), 'nodes': starts}
        #finally, save the json file
        with open(filename + '.json', 'w') as outfile:
            json.dump(result, outfile)