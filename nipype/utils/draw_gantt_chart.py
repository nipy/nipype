# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Module to draw an html gantt chart from logfile produced by
callback_log.log_nodes_cb()
"""

# Import packages
# Import packages
import json
from dateutil import parser
import datetime
import random
import pandas as pd
import dateutil
from collections import OrderedDict


def log_to_events(logfile):
    events = []
    with open(logfile, 'r') as content:
        #read file separating each line
        content = content.read()
        lines = content.split('\n')

        for l in lines:
            event = None
            try:
                event = json.loads(l)
            except Exception, e:
                pass

            if not event: continue

            if 'start' in event:
                event['type'] = 'start'
                event['time'] = event['start']
            else:
                event['type'] = 'finish'
                event['time'] = event['finish']

            events.append(event)
    return events

def log_to_dict(logfile):

    #keep track of important vars
    nodes = [] #all the parsed nodes
    unifinished_nodes = [] #all start nodes that dont have a finish yet

    with open(logfile, 'r') as content:

        #read file separating each line
        content = content.read()
        lines = content.split('\n')

        for l in lines:
            #try to parse each line and transform in a json dict.
            #if the line has a bad format, just skip
            node = None
            try:
                node = json.loads(l)
            except Exception, e:
                pass

            if not node: 
                continue

            #if it is a start node, add to unifinished nodes
            if 'start' in node:
                node['start'] = parser.parse(node['start'])
                unifinished_nodes.append(node)

            #if it is end node, look in uninished nodes for matching start
            #remove from unifinished list and add to node list
            elif 'finish' in node:
                node['finish'] = parser.parse(node['finish'])
                #because most nodes are small, we look backwards in the unfinished list
                for s in range(len(unifinished_nodes)):
                    aux = unifinished_nodes[s]
                    #found the end for node start, copy over info
                    if aux['id'] == node['id'] and aux['name'] == node['name'] and aux['start'] < node['finish']:
                        node['start'] = aux['start']
                        node['duration'] = (node['finish'] - node['start']).total_seconds()

                        unifinished_nodes.remove(aux)
                        nodes.append(node)
                        break

        #finished parsing
        #assume nodes without finish didn't finish running.
        #set their finish to last node run
        last_node = nodes[-1]
        for n in unifinished_nodes:
            n['finish'] = last_node['finish']
            n['duration'] = (n['finish'] - n['start']).total_seconds()
            nodes.append(n)

        return nodes, last_node

def calculate_resources(events, resource):
    res = OrderedDict()
    for event in events:
        all_res = 0
        if event['type'] == "start":
            all_res += int(float(event[resource]))
            current_time = event['start'];
        elif event['type'] == "finish":
            all_res+= int(float(event[resource]))
            current_time = event['finish'];

        res[current_time] = all_res

    timestamps = [dateutil.parser.parse(ts) for ts in res.keys()]
    time_series = pd.Series(res.values(), timestamps)
    interp_seq = pd.date_range(time_series.index[0], time_series.index[-1], freq='S')
    interp_time_series = time_series.reindex(interp_seq)
    interp_time_series = interp_time_series.fillna(method='ffill')
    return interp_time_series

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


def draw_nodes(start, nodes, cores, minute_scale, space_between_minutes, colors):
    result = ''
    end_times = [datetime.datetime(start.year, start.month, start.day, start.hour, start.minute, start.second) for x in range(cores)]

    scale = float(space_between_minutes/float(minute_scale))
    space_between_minutes = float(space_between_minutes/scale)

    for node in nodes:
        node_start = node['start']
        node_finish = node['finish']
        offset = ((node_start - start).total_seconds() / 60) * scale * space_between_minutes + 220
        scale_duration = (node['duration'] / 60) * scale * space_between_minutes
        if scale_duration < 5:
            scale_duration = 5

        scale_duration -= 2
        left = 60
        for j in range(len(end_times)):
            if end_times[j] < node_start:
                left += j * 30
                end_times[j] = datetime.datetime(node_finish.year,
                                                 node_finish.month,
                                                 node_finish.day,
                                                 node_finish.hour,
                                                 node_finish.minute,
                                                 node_finish.second)

                break
        color = random.choice(colors)  
        n_start = node['start'].strftime("%Y-%m-%d %H:%M:%S")
        n_finish = node['finish'].strftime("%Y-%m-%d %H:%M:%S")
        n_dur = node['duration']/60
        new_node = "<div class='node' style='left:%spx;top:%spx;height:%spx;background-color:%s;'title='%s\nduration:%s\nstart:%s\nend:%s'></div>"%(left, offset, scale_duration, color, node['name'], n_dur, n_start, n_finish)
        result += new_node

    return result

def draw_thread_bar(threads,space_between_minutes, minute_scale):
    result = "<p class='time' style='top:198px;left:900px;'>Threads</p>"

    scale = float(space_between_minutes/float(minute_scale))
    space_between_minutes = float(space_between_minutes/60.0)
    for i in range(len(threads)):
        width = threads[i] * 10
        t = (float(i*scale*minute_scale)/60.0) + 220
        bar = "<div class='bar' style='height:"+ str(space_between_minutes) + "px;width:"+ str(width) +"px;left:900px;top:"+str(t)+"px'></div>"
        result += bar

    return result

def draw_memory_bar(memory, space_between_minutes, minute_scale):
    result = "<p class='time' style='top:198px;left:1200px;'>Memory</p>"

    scale = float(space_between_minutes/float(minute_scale))
    space_between_minutes = float(space_between_minutes/60.0)

    for i in range(len(memory)):
        width = memory[i] * 10
        t = (float(i*scale*minute_scale)/60.0) + 220
        bar = "<div class='bar' style='height:"+ str(space_between_minutes) + "px;width:"+ str(width) +"px;left:1200px;top:"+str(t)+"px'></div>"
        result += bar

    return result


def generate_gantt_chart(logfile, cores, minute_scale=10,
                         space_between_minutes=50,
                         colors=["#7070FF", "#4E4EB2", "#2D2D66", "#9B9BFF"]):
    '''
    Generates a gantt chart in html showing the workflow execution based on a callback log file.
    This script was intended to be used with the MultiprocPlugin.
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
    
    # workflow.run(plugin='MultiProc',  
    #     plugin_args={'n_procs':8, 'memory':12, 'status_callback': log_nodes_cb})
    
    # generate_gantt_chart('callback.log', 8)
    '''

    result, last_node = log_to_dict(logfile)
    scale = space_between_minutes 

    #add the html header
    html_string = '''<!DOCTYPE html>
    <head>
        <style>
            #content{
                width:100%;
                height:100%;
                position:absolute;
            }

            .node{
                background-color:#7070FF;
                border-radius: 5px;
                position:absolute;
                width:20px;
                white-space:pre-wrap;
            }

            .line{
                position: absolute;
                color: #C2C2C2;
                opacity: 0.5;
                margin: 0px;
            }

            .time{
                position: absolute;
                font-size: 16px;
                color: #666666;
                margin: 0px;
            }

            .bar{
                position: absolute;
                background-color: #80E680;
                height: 1px;
            }

            .dot{
                position: absolute;
                width: 1px;
                height: 1px;
                background-color: red;
            }
        </style>
    </head>

    <body>
        <div id="content">'''


    #create the header of the report with useful information
    start = result[0]['start']
    duration = (last_node['finish'] - start).total_seconds()

    html_string += '<p>Start: '+ result[0]['start'].strftime("%Y-%m-%d %H:%M:%S") +'</p>'
    html_string += '<p>Finish: '+ last_node['finish'].strftime("%Y-%m-%d %H:%M:%S") +'</p>'
    html_string += '<p>Duration: '+ "{0:.2f}".format(duration/60) +' minutes</p>'
    html_string += '<p>Nodes: '+str(len(result))+'</p>'
    html_string += '<p>Cores: '+str(cores)+'</p>'

    html_string += draw_lines(start, duration, minute_scale, space_between_minutes)
    html_string += draw_nodes(start, result, cores, minute_scale,space_between_minutes, colors)

    result = log_to_events(logfile)
    threads = calculate_resources(result, 'num_threads')
    html_string += draw_thread_bar(threads, space_between_minutes, minute_scale)

    memory = calculate_resources(result, 'estimated_memory_gb')
    html_string += draw_memory_bar(memory, space_between_minutes, minute_scale)


    #finish html
    html_string+= '''
        </div>
    </body>'''

    #save file
    html_file = open(logfile +'.html', 'wb')
    html_file.write(html_string)
    html_file.close()