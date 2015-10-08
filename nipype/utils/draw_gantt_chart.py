import json
from dateutil import parser
import datetime
import random


def log_to_json(logfile):
    result = []
    with open(logfile, 'r') as content:

            #read file separating each line
            content = content.read()
            lines = content.split('\n')

            lines = [ json.loads(x) for x in lines[:-1]]

            last_node = [ x for x in lines if x.has_key('finish')][-1]

            for i, line in enumerate(lines):
                #get first start it finds
                if not line.has_key('start'):
                    continue

                #fint the end node for that start
                for j in range(i+1, len(lines)):
                    if lines[j].has_key('finish'):
                        if lines[j]['id'] == line['id'] and lines[j]['name'] == line['name']:
                            line['finish'] = lines[j]['finish']
                            line['duration'] = (parser.parse(line['finish']) - parser.parse(line['start'])).total_seconds()
                            result.append(line)
                            break

    return result, last_node


#total duration in seconds
def draw_lines(start, total_duration, minute_scale, scale):
    result = ''
    next_line = 220
    next_time = start;
    num_lines = int((total_duration/60) / minute_scale) +2;

    for i in range(num_lines):
        new_line = "<hr class='line' width='100%' style='top:"+ str(next_line) + "px;'>"
        result += new_line

        time = "<p class='time' style='top:" + str(next_line - 20) + "px;'> " + str(next_time.hour) + ':' + str(next_time.minute) + " </p>";
        result += time

        next_line += minute_scale * scale
        next_time += datetime.timedelta(minutes=minute_scale)
    return result

def draw_nodes(start, nodes, cores, scale, colors):
    result = ''
    end_times = [datetime.datetime(start.year, start.month, start.day, start.hour, start.minute, start.second) for x in range(cores)]

    for node in nodes:
        node_start = parser.parse(node['start'])
        node_finish = parser.parse(node['finish'])
        offset = ((node_start - start).total_seconds() / 60) * scale + 220
        scale_duration = (node['duration'] / 60) * scale
        if scale_duration < 5:
            scale_duration = 5

        scale_duration -= 2
        left = 60
        for j in range(len(end_times)):
            if end_times[j] < node_start:
                left += j * 30
                end_times[j] = datetime.datetime(node_finish.year, node_finish.month, node_finish.day, node_finish.hour, node_finish.minute, node_finish.second)
                #end_times[j]+=  datetime.timedelta(microseconds=node_finish.microsecond)
                break

        color = random.choice(colors)
        new_node = "<div class='node' style=' left:" + str(left) + "px;top: " + str(offset) + "px;height:" + str(scale_duration) + "px; background-color: " + color  + " 'title='" + node['name'] +'\nduration: ' + str(node['duration']/60) + '\nstart: ' + node['start'] + '\nend: ' + node['finish'] + "'></div>";
        result += new_node
    return result


'''
Generates a gantt chart in html showing the workflow execution based on a callback log file.
This script was intended to be used with the ResourceMultiprocPlugin.
The following code shows how to set up the workflow in order to generate the log file:

# import logging
# import logging.handlers
# from nipype.pipeline.plugins.callback_log import log_nodes_cb

# log_filename = 'callback.log'
# logger = logging.getLogger('callback')
# logger.setLevel(logging.DEBUG)
# handler = logging.FileHandler(log_filename)
# logger.addHandler(handler)

# #create workflow
# workflow = ...

# workflow.run(plugin='ResourceMultiProc',  
#     plugin_args={'num_threads':8, 'memory':12, 'status_callback': log_nodes_cb})

# generate_gantt_chart('callback.log', 8)
'''
def generate_gantt_chart(logfile, cores, minute_scale=10, space_between_minutes=50, colors=["#7070FF", "#4E4EB2", "#2D2D66", "#9B9BFF"]):

    result, last_node = log_to_json(logfile)
    scale = space_between_minutes 

    #add the html header
    html_string = '''<!DOCTYPE html>
    <head>
        <link rel="stylesheet" type="text/css" href="style.css">
    </head>

    <body>
        <div id="content">'''


    #create the header of the report with useful information
    start = parser.parse(result[0]['start'])
    duration = int((parser.parse(last_node['finish']) - start).total_seconds())

    html_string += '<p>Start: '+ result[0]['start'] +'</p>'
    html_string += '<p>Finish: '+ last_node['finish'] +'</p>'
    html_string += '<p>Duration: '+ str(duration/60) +' minutes</p>'
    html_string += '<p>Nodes: '+str(len(result))+'</p>'
    html_string += '<p>Cores: '+str(cores)+'</p>'


    #draw lines
    html_string += draw_lines(start, duration, minute_scale, scale)

    #draw nodes
    html_string += draw_nodes(start, result, cores, scale, colors)


    #finish html
    html_string+= '''
        </div>
    </body>'''

    #save file
    html_file = open(logfile +'.html', 'wb')
    html_file.write(html_string)
    html_file.close()