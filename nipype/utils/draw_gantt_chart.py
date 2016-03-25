# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Module to draw an html gantt chart from logfile produced by
callback_log.log_nodes_cb()
"""

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
    '''
    Function to extract log node dictionaries into a list of python
    dictionaries and return the list as well as the final node

    Parameters
    ----------
    logfile : string
        path to the json-formatted log file generated from a nipype
        workflow execution

    Returns
    -------
    nodes_list : list
        a list of python dictionaries containing the runtime info
        for each nipype node
    '''

    # Init variables
    #keep track of important vars
    nodes_list = [] #all the parsed nodes
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
            except Exception:
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
                    if aux['id'] == node['id'] and aux['name'] == node['name'] \
                       and aux['start'] < node['finish']:
                        node['start'] = aux['start']
                        node['duration'] = (node['finish'] - node['start']).total_seconds()

                        unifinished_nodes.remove(aux)
                        nodes_list.append(node)
                        break

        #finished parsing
        #assume nodes without finish didn't finish running.
        #set their finish to last node run
        last_node = nodes_list[-1]
        for n in unifinished_nodes:
            n['finish'] = last_node['finish']
            n['duration'] = (n['finish'] - n['start']).total_seconds()
            nodes_list.append(n)

        return nodes_list


def calculate_resources(events, resource):
    res = OrderedDict()
    for event in events:
        all_res = 0.0
        if event['type'] == "start":
            if resource in event and event[resource] != 'Unkown':
                all_res += float(event[resource])
            current_time = event['start'];
        elif event['type'] == "finish":
            if resource in event and event[resource] != 'Unkown':
                all_res += float(event[resource])
            current_time = event['finish'];
        res[current_time] = all_res

    timestamps = [dateutil.parser.parse(ts) for ts in res.keys()]
    time_series = pd.Series(data=res.values(), index=timestamps)
    #TODO: pandas is removing all data values somewhere here
    #interp_seq = pd.date_range(time_series.index[0], time_series.index[-1], freq='U')
    #interp_time_series = time_series.reindex(interp_seq)
    #interp_time_series = interp_time_series.fillna(method='ffill')
    return time_series


def draw_lines(start, total_duration, minute_scale, scale):
    '''
    Function to draw the minute line markers and timestamps

    Parameters
    ----------
    start : datetime.datetime obj
        start time for first minute line marker
    total_duration : float
        total duration of the workflow execution (in seconds)
    minute_scale : integer
        the scale, in minutes, at which to plot line markers for the
        gantt chart; for example, minute_scale=10 means there are lines
        drawn at every 10 minute interval from start to finish
    scale : integer
        scale factor in pixel spacing between minute line markers

    Returns
    -------
    result : string
        the html-formatted string for producing the minutes-based
        time line markers
    '''

    # Init variables
    result = ''
    next_line = 220
    next_time = start
    num_lines = int((total_duration/60) / minute_scale) + 2

    # Iterate through the lines and create html line markers string
    for line in range(num_lines):
        # Line object
        new_line = "<hr class='line' width='100%%' style='top:%dpx;'>" % next_line
        result += new_line
        # Time digits
        time = "<p class='time' style='top:%dpx;'> %02d:%02d </p>" % \
               (next_line-20, next_time.hour, next_time.minute)
        result += time
        # Increment line spacing and digits
        next_line += minute_scale * scale
        next_time += datetime.timedelta(minutes=minute_scale)

    # Return html string for time line markers
    return result


def draw_nodes(start, nodes_list, cores, minute_scale, space_between_minutes, colors):
    '''
    Function to return the html-string of the node drawings for the
    gantt chart

    Parameters
    ----------
    start : datetime.datetime obj
        start time for first node
    nodes_list : list
        a list of the node dictionaries
    cores : integer
        the number of cores given to the workflow via the 'n_procs'
        plugin arg
    total_duration : float
        total duration of the workflow execution (in seconds)
    minute_scale : integer
        the scale, in minutes, at which to plot line markers for the
        gantt chart; for example, minute_scale=10 means there are lines
        drawn at every 10 minute interval from start to finish
    space_between_minutes : integer
        scale factor in pixel spacing between minute line markers
    colors : list
        a list of colors to choose from when coloring the nodes in the
        gantt chart

    Returns
    -------
    result : string
        the html-formatted string for producing the minutes-based
        time line markers
    '''

    # Init variables
    result = ''
    scale = float(space_between_minutes/float(minute_scale))
    space_between_minutes = float(space_between_minutes/scale)
    end_times = [datetime.datetime(start.year, start.month, start.day,
                                   start.hour, start.minute, start.second) \
                 for core in range(cores)]

    # For each node in the pipeline
    for node in nodes_list:
        # Get start and finish times
        node_start = node['start']
        node_finish = node['finish']
        # Calculate an offset and scale duration
        offset = ((node_start - start).total_seconds() / 60) * scale * \
                 space_between_minutes + 220
        # Scale duration
        scale_duration = (node['duration'] / 60) * scale * space_between_minutes
        if scale_duration < 5:
            scale_duration = 5
        scale_duration -= 2
        # Left
        left = 60
        for core in range(len(end_times)):
            if end_times[core] < node_start:
                left += core * 30
                end_times[core] = datetime.datetime(node_finish.year,
                                                    node_finish.month,
                                                    node_finish.day,
                                                    node_finish.hour,
                                                    node_finish.minute,
                                                    node_finish.second)
                break

        # Get color for node object
        color = random.choice(colors) 
        if 'error' in node:
            color = 'red'

        # Setup dictionary for node html string insertion
        node_dict = {'left' : left,
                     'offset' : offset,
                     'scale_duration' : scale_duration,
                     'color' : color,
                     'node_name' : node['name'],
                     'node_dur' : node['duration']/60.0,
                     'node_start' : node_start.strftime("%Y-%m-%d %H:%M:%S"),
                     'node_finish' : node_finish.strftime("%Y-%m-%d %H:%M:%S")}
        # Create new node string
        new_node = "<div class='node' style='left:%(left)spx;top:%(offset)spx;"\
                   "height:%(scale_duration)spx;background-color:%(color)s;"\
                   "'title='%(node_name)s\nduration:%(node_dur)s\n"\
                   "start:%(node_start)s\nend:%(node_finish)s'></div>" % \
                   node_dict

        # Append to output result
        result += new_node

    # Return html string for nodes
    return result


def draw_thread_bar(threads,space_between_minutes, minute_scale, color):
    result = "<p class='time' style='top:198px;left:900px;'>Threads</p>"

    scale = float(space_between_minutes/float(minute_scale))
    space_between_minutes = float(space_between_minutes/60.0)

    for i in range(len(threads)):
        #print threads[i]
        width = threads[i] * 10
        t = (float(i*scale*minute_scale)/60.0) + 220
        bar = "<div class='bar' style='height:"+ str(space_between_minutes) + "px;width:"+ str(width) +"px;left:900px;top:"+str(t)+"px'></div>"
        result += bar

    return result


def draw_memory_bar(nodes_list, space_between_minutes, minute_scale, color,
                    mem_key='runtime_memory_gb'):
    '''
    '''

    # Init variables
    # Memory header
    result = "<p class='time' style='top:198px;left:1200px;'>Memory</p>"
    # 
    scale = float(space_between_minutes/float(minute_scale))
    space_between_minutes = float(space_between_minutes/scale)

    for idx, node in enumerate(nodes_list):
        try:
            memory = float(node[mem_key])
        except:
            memory = 0

        height = (node['duration'] / 60) * scale * space_between_minutes
        width = memory * 20
        t = (float(idx*scale*minute_scale)/60.0) + 220
        bar = "<div class='bar' style='background-color:"+color+";height:"+ \
        str(height) + "px;width:"+ str(width) +\
        "px;left:1200px;top:"+str(t)+"px'></div>"
        result += bar

    return result


def generate_gantt_chart(logfile, cores, minute_scale=10,
                         space_between_minutes=50,
                         colors=["#7070FF", "#4E4EB2", "#2D2D66", "#9B9BFF"]):
    '''
    Generates a gantt chart in html showing the workflow execution based on a callback log file.
    This script was intended to be used with the MultiprocPlugin.
    The following code shows how to set up the workflow in order to generate the log file:

    Parameters
    ----------
    logfile : string
        filepath to the callback log file to plot the gantt chart of
    cores : integer
        the number of cores given to the workflow via the 'n_procs'
        plugin arg
    minute_scale : integer (optional); default=10
        the scale, in minutes, at which to plot line markers for the
        gantt chart; for example, minute_scale=10 means there are lines
        drawn at every 10 minute interval from start to finish
    space_between_minutes : integer (optional); default=50
        scale factor in pixel spacing between minute line markers
    colors : list (optional)
        a list of colors to choose from when coloring the nodes in the
        gantt chart


    Returns
    -------
    None
        the function does not return any value but writes out an html
        file in the same directory as the callback log path passed in

    Usage
    -----
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

    nodes_list = log_to_dict(logfile)
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
                height: 1px;
                opacity: 0.7;
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
    start_node = nodes_list[0]
    last_node = nodes_list[-1]
    duration = (last_node['finish'] - start_node['start']).total_seconds()

    #summary strings of workflow at top
    html_string += '<p>Start: ' + start_node['start'].strftime("%Y-%m-%d %H:%M:%S") + '</p>'
    html_string += '<p>Finish: ' + last_node['finish'].strftime("%Y-%m-%d %H:%M:%S") + '</p>'
    html_string += '<p>Duration: ' + "{0:.2f}".format(duration/60) + ' minutes</p>'
    html_string += '<p>Nodes: ' + str(len(nodes_list))+'</p>'
    html_string += '<p>Cores: ' + str(cores) + '</p>'

    html_string += draw_lines(start_node['start'], duration, minute_scale,
                              space_between_minutes)
    html_string += draw_nodes(start_node['start'], nodes_list, cores, minute_scale,
                              space_between_minutes, colors)

    result = log_to_events(logfile)

    #threads_estimated = calculate_resources(result, 'num_threads')
    #html_string += draw_thread_bar(threads_estimated, space_between_minutes, minute_scale, '#90BBD7')
    
    #threads_real = calculate_resources(result, 'runtime_threads')
    #html_string += draw_thread_bar(threads_real, space_between_minutes, minute_scale, '#03969D')


    #memory_estimated = calculate_resources(result, 'estimated_memory_gb')
    #html_string += draw_memory_bar(memory_estimated, space_between_minutes, minute_scale, '#90BBD7')

    memory_real = calculate_resources(result, 'runtime_memory_gb')
    html_string += draw_memory_bar(nodes_list, space_between_minutes, minute_scale, '#03969D')


    #finish html
    html_string+= '''
        </div>
    </body>'''

    #save file
    html_file = open(logfile +'.html', 'wb')
    html_file.write(html_string)
    html_file.close()
