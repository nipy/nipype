import sys
import getopt
import os
from workflow_reconall import create_reconall
from utils import getdefaultconfig, mkdir_p

def help():
    print("""
This program runs FreeSurfer's recon-all as a nipype script. This allows 
for better parallel processing for easier experimenting with new and/or
improved processing steps.

Usage:
python recon-all.py --T1 <infile1> --subject <name> --subjects_dir <dir> [--T1 <infile2>... --T2 <inT2> --FLAIR <inFLAIR>]

Required inputs;
-i or --T1 <infile1>      Input T1 image. Multiple T1 images may be used as inputs each requiring its own
                          input flag

-s or --subject <name>    Name of the subject being processed.

--subjects_dir <dir>      Input subjects directory defines where to run workflow and output results

Optional inputs:
--T2 <inT2>               Input T2 image. T2 images are not used for processing, but the image will be converted
                          to .mgz format.

--FLAIR <inFLAIR>         Input FLAIR image. FLAIR images are not used for processing, but the image will be 
                              converted to .mgz format.

--plugin <plugin>         Plugin to use when running workflow

-q or --queue <queue>     Queue to submit as a qsub argument (requires 'SGE' or 'SGEGraph' plugin)

--qcache                  Make qcache

--cw256                   Include this flag after -autorecon1 if images have a FOV > 256.  The
                          flag causes mri_convert to conform the image to dimensions of 256^3.

--longbase <name>         Set the longitudinal base template. If a longitudinal 
                          base is set, no input files will be used/required. (in development)

--openmp <numthreads>     OpenMP parallelization (CentOS 6 distribution only!) 
                          To enable this feature, add the flag -openmp <numthreads> 
                          to recon-all, where <numthreads> is the number of threads 
                          you would like to run.

--recoding <file>         Recodes the aseg atlas according to the original and target labels
                          specified by the csv file given. Original labels should be listed
                          first followed by the target labels. There must be a csv header.
                          The csv may either have 2 columns (just integer label values) or
                          4 columns (including label strings).

Author:
David Ellis
University of Iowa
    """)

# TODOs:
# * Fix workflow outputs so that the output is not written to the subjects directory
#   but to the node directory instead
# * Finish longitudinal workflow.
# * Write template workflow.
# * Write option for running a list of sessions instead of a single session.
# * Create more thorough checking of inputs.
    
def procargs(argv, config):
    try:
        opts, args = getopt.getopt(argv, "hi:q:s:", ["help",
                                                     "T1=",
                                                     "subject=",
                                                     "T2=",
                                                     "FLAIR=",
                                                     "plugin=",
                                                     "queue=",
                                                     "subjects_dir=",
                                                     "cache_dir=",
                                                     "qcache",
                                                     "cw256",
                                                     "longbase=",
                                                     "tp=",
                                                     "openmp=",
                                                     "recoding="])
    except getopt.GetoptError:
        print("Error occured when parsing arguments")
        help()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            help()
            sys.exit()
        elif opt in ("-i", "--T1"):
            config['in_T1s'].append(os.path.abspath(arg))
            if not os.path.isfile(arg):
                print("ERROR: input T1 image must be an existing image file")
                print("{0} does not exist".format(arg))
                sys.exit(2)
        elif opt in ("-s", "--subject"):
            config['subject_id'] = arg
        elif opt in ("--T2"):
            config['in_T2'] = os.path.abspath(arg)
            if not os.path.isfile(config['in_T2']):
                print("ERROR: input T2 image must be an existing image file")
                print("{0} does not exist".format(config['in_T2']))
                sys.exit(2)
        elif opt in ("--FLAIR"):
            config['in_FLAIR'] = os.path.abspath(arg)
            if not os.path.isfile(config['in_FLAIR']):
                print("ERROR: input FLAIR image must be an existing image file")
                print("{0} does not exist".format(config['in_FLAIR']))
                sys.exit(2)
        elif opt in ("--plugin"):
            config['plugin'] = arg
        elif opt in ("-q", "--queue"):
            config['queue'] = arg
        elif opt in ("--subjects_dir"):
            config['subjects_dir'] = os.path.abspath(arg)
        elif opt in ("--qcache"):
            config['qcache'] = True
        elif opt in ("--cw256"):
            config['cw256'] = True
        elif opt in ("--longbase"):
            config['longitudinal'] = True
            config['long_base'] = arg
            #TODO: Check that the longitudinal base pre-exists
        elif opt in ("--tp"):
            config['timepoints'].append(arg)
        elif opt in ("--openmp"):
            try:
                config['openmp'] = int(arg)
            except ValueError:
                print("ERROR: --openmp flag accepts only integers")
                sys.exit(2)
        elif opt in ('--recoding'):
            recoding_file = os.path.abspath(arg)
            if os.path.isfile(recoding_file) and '.csv' in recoding_file:
                config['recoding_file'] = recoding_file
            else:
                print("ERROR: the file must be an existing csv file")
                sys.exit(2)
        elif opt in ('--cache_dir'):
            config['cache_dir'] = os.path.abspath(arg)
                

    if config['subject_id'] == None:
        print("ERROR: Must set subject_id using -s flag")
        help()
        sys.exit(2)
        
    if not config['longitudinal'] and len(config['in_T1s']) == 0:
        print("ERROR: Must have at least one input T1 image")
        help()
        sys.exit(2)
        
    if config['subjects_dir'] == None:
        print("ERROR: Must set the subjects_dir before running")
        help()
        sys.exit(2)

    # print the input cofigurations
    print('Subject ID: {0}'.format(config['subject_id']))
    print('Input T1s: {0}'.format(config['in_T1s']))
    
    if config['in_T2'] != None:
        print('Input T2: {0}'.format(config['in_T2']))

    if config['in_FLAIR'] != None:
        print('Input FLAIR: {0}'.format(config['in_FLAIR']))
        
    print('Plugin: {0}'.format(config['plugin']))
    print('Make qcache: {0}'.format(config['qcache']))
    print('Conform to 256: {0}'.format(config['cw256']))
    
    if config['queue'] != None:
        print('Queue: {0}'.format(config['queue']))
        if config['plugin'] == 'Linear':
            print("ERROR: cannot submit to a queue unless SGE or SGEGraph plugins are set")
            sys.exit(2)
        if config['openmp'] != None:
            minmemoryGB = 8 # this could be modified in later updates
            config['plugin_args'] = { 'qsub_args' :  modify_qsub_args(config['queue'],
                                                                      minmemoryGB,
                                                                      config['openmp'],
                                                                      config['openmp']), 
                                      'overwrite' : True }
            print('plugin_args: {0}'.format(config['plugin_args']))
                
    if config['openmp'] != None:
        print('OpenMP: {0}'.format(config['openmp']))
        
    if config['longitudinal']:
        # set input requirements for running longitudinally
        # TODO: print(errors when inputs are not set correctly
        print('Running longitudinally')
        print('Longitudinal Base: {0}'.format(config['long_base']))
    return config


def main(argv):
    defaultconfig = getdefaultconfig()
    config = procargs(argv, defaultconfig)
    if config['longitudinal']:
        config['long_id'] = "{0}.long.{1}".format(config['subject_id'], config['long_base'])
        config['current_id'] = config['long_id']
    else:
        config['current_id'] = config['subject_id']
    
    # Experiment Info
    # TODO: Have user input cache directory
    ExperimentInfo = {"Atlas": {"TEMP_CACHE": os.path.join(config['cache_dir'], config['subject_id']),
                                "LOG_DIR": os.path.join(config['cache_dir'], config['subject_id'], 'log')}}
    
    # Create necessary output directories
    for item in ExperimentInfo["Atlas"].iteritems():
        mkdir_p(item[1])

    # Now that we've defined the args and created the folders, create workflow
    reconall = create_reconall(config)

    # Set workflow configurations
    reconall.config['execution'] = {
        'stop_on_first_crash': 'true',
        'stop_on_first_rerun': 'false',
        # This stops at first attempt to rerun, before running, and before
        # deleting previous results.
        'hash_method': 'timestamp',
        'remove_unnecessary_outputs': 'false',
        'use_relative_paths': 'false',
        'remove_node_directories': 'false',
    }
    reconall.config['logging'] = {
        'workflow_level' : 'DEBUG',
        'filemanip_level' : 'DEBUG',
        'interface_level' : 'DEBUG',
        'log_directory' : ExperimentInfo["Atlas"]["LOG_DIR"],
        'log_to_file' : True
    }

    # Run Workflow
    reconall.base_dir = ExperimentInfo["Atlas"]["TEMP_CACHE"]
    if config['plugin'] in ('SGE', 'SGEGraph') and config['queue'] != None:
        reconall.run(plugin=config['plugin'], plugin_args=dict(qsub_args='-q ' + config['queue']))
    elif config['plugin'] != 'Linear':
        reconall.run(plugin=config['plugin'])
    else:
        reconall.run()


if __name__ == "__main__":
    main(sys.argv[1:])

