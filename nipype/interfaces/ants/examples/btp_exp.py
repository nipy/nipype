#!/usr/bin/python
#################################################################################
## Program:   Build Template Parallel
## Language:  Python
##
## Author:  Hans J. Johnson
##
##      This software is distributed WITHOUT ANY WARRANTY; without even
##      the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
##      PURPOSE.  See the above copyright notices for more information.
##
#################################################################################
import os
import re
import sys

##############################################################################
def get_global_sge_script(pythonPathsList,binPathsList,customEnvironment={}):
    """This is a wrapper script for running commands on an SGE cluster
so that all the python modules and commands are pathed properly"""

    custEnvString=""
    for key,value in customEnvironment.items():
        custEnvString+="export "+key+"="+value+"\n"

    PYTHONPATH=":".join(pythonPathsList)
    BASE_BUILDS=":".join(binPathsList)
    GLOBAL_SGE_SCRIPT="""#!/bin/bash
echo "STARTED at: $(date +'%F-%T')"
echo "Ran on: $(hostname)"
export PATH={BINPATH}
export PYTHONPATH={PYTHONPATH}

echo "========= CUSTOM ENVIRONMENT SETTINGS =========="
echo "export PYTHONPATH={PYTHONPATH}"
echo "export PATH={BINPATH}"
echo "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"

echo "With custom environment:"
echo {CUSTENV}
{CUSTENV}
## NOTE:  nipype inserts the actual commands that need running below this section.
""".format(PYTHONPATH=PYTHONPATH,BINPATH=BASE_BUILDS,CUSTENV=custEnvString)
    return GLOBAL_SGE_SCRIPT

def main(argv=None):
    import argparse
    import ConfigParser
    import csv
    import string

    if argv == None:
        argv = sys.argv

    # Create and parse input arguments
    parser = argparse.ArgumentParser(description='Runs a mini version of BuildTemplateParallel')
    group = parser.add_argument_group('Required')
    group.add_argument('-pe', action="store", dest='processingEnvironment', required=True,
                       help='The name of the processing environment to use from the config file')
    group.add_argument('-wfrun', action="store", dest='wfrun', required=True,
                       help='The name of the workflow running plugin to use')
    group.add_argument('-ExperimentConfig', action="store", dest='ExperimentConfig', required=True,
                       help='The path to the file that describes the entire experiment')
    input_arguments = parser.parse_args()


    expConfig = ConfigParser.ConfigParser()
    expConfig.read(input_arguments.ExperimentConfig)

    # Experiment specific information
    session_db=expConfig.get('EXPERIMENT_DATA','SESSION_DB')
    ExperimentName=expConfig.get('EXPERIMENT_DATA','EXPERIMENTNAME')

    # Platform specific information
    #     Prepend the python search paths
    PYTHON_AUX_PATHS=expConfig.get(input_arguments.processingEnvironment,'PYTHON_AUX_PATHS')
    PYTHON_AUX_PATHS=PYTHON_AUX_PATHS.split(':')
    PYTHON_AUX_PATHS.extend(sys.path)
    sys.path=PYTHON_AUX_PATHS
    #     Prepend the shell environment search paths
    PROGRAM_PATHS=expConfig.get(input_arguments.processingEnvironment,'PROGRAM_PATHS')
    PROGRAM_PATHS=PROGRAM_PATHS.split(':')
    PROGRAM_PATHS.extend(os.environ['PATH'].split(':'))
    os.environ['PATH']=':'.join(PROGRAM_PATHS)
    #    Define platform specific output write paths
    BASEOUTPUTDIR=expConfig.get(input_arguments.processingEnvironment,'BASEOUTPUTDIR')
    ExperimentBaseDirectoryPrefix=os.path.realpath(os.path.join(BASEOUTPUTDIR,ExperimentName))
    ExperimentBaseDirectoryCache=ExperimentBaseDirectoryPrefix+"_CACHE"
    ExperimentBaseDirectoryResults=ExperimentBaseDirectoryPrefix +"_Results"
    if not os.path.exists(ExperimentBaseDirectoryCache):
        os.makedirs(ExperimentBaseDirectoryCache)
    if not os.path.exists(ExperimentBaseDirectoryResults):
        os.makedirs(ExperimentBaseDirectoryResults)

    print os.environ
    #sys.exit(-1)

    CLUSTER_QUEUE=expConfig.get(input_arguments.processingEnvironment,'CLUSTER_QUEUE')

    ## Setup environment for CPU load balancing of ITK based programs.
    import multiprocessing
    total_CPUS=multiprocessing.cpu_count()
    if input_arguments.wfrun == 'helium_all.q':
        pass
    elif input_arguments.wfrun == 'ipl_OSX':
        pass
    elif input_arguments.wfrun == 'local_4':
        os.environ['NSLOTS']="{0}".format(total_CPUS/4)
    elif input_arguments.wfrun == 'local_3':
        os.environ['NSLOTS']="{0}".format(total_CPUS/3)
    elif input_arguments.wfrun == 'local_12':
        os.environ['NSLOTS']="{0}".format(total_CPUS/12)
    elif input_arguments.wfrun == 'local':
        os.environ['NSLOTS']="{0}".format(total_CPUS/1)
    else:
        print "You must specify the run environment type. [helium_all.q,ipl_OSX,local_3,local_4,local_12,local]"
        print input_arguments.wfrun
        sys.exit(-1)

    print "Configuring Pipeline"
    from nipype import config  ## NOTE:  This needs to occur AFTER the PYTHON_AUX_PATHS has been modified
    config.enable_debug_mode() ## NOTE:  This needs to occur AFTER the PYTHON_AUX_PATHS has been modified
    import buildTemplateParallelDriver ## NOTE:  This needs to occur AFTER the PYTHON_AUX_PATHS has been modified
    btp=buildTemplateParallelDriver.BuildTemplateParallelWorkFlow(
      ExperimentBaseDirectoryCache,
      ExperimentBaseDirectoryResults,
      session_db)
    print "Start Processing"

    ## Create the shell wrapper script for ensuring that all jobs running on remote hosts from SGE
    #  have the same environment as the job submission host.
    JOB_SCRIPT=get_global_sge_script(sys.path,PROGRAM_PATHS)
    print JOB_SCRIPT

    SGEFlavor='SGE'
    if input_arguments.wfrun == 'helium_all.q':
        btp.run(plugin=SGEFlavor,
            plugin_args=dict(template=JOB_SCRIPT,qsub_args="-S /bin/bash -pe smp1 1-4 -l mem_free=4000M -o /dev/null -e /dev/null "+CLUSTER_QUEUE))
    if input_arguments.wfrun == 'helium_all.q_graph':
        SGEFlavor='SGEGraph' #Use the SGEGraph processing
        btp.run(plugin=SGEFlavor,
            plugin_args=dict(template=JOB_SCRIPT,qsub_args="-S /bin/bash -pe smp1 1-4 -l mem_free=4000M -o /dev/null -e /dev/null "+CLUSTER_QUEUE))
    elif input_arguments.wfrun == 'ipl_OSX':
        btp.write_graph()
        print "Running On ipl_OSX"
        btp.run(plugin=SGEFlavor,
            plugin_args=dict(template=JOB_SCRIPT,qsub_args="-S /bin/bash -pe smp1 1-4 -l mem_free=4000M -o /dev/null -e /dev/null "+CLUSTER_QUEUE))
    elif input_arguments.wfrun == 'local_4':
        btp.write_graph()
        print "Running with 4 parallel processes on local machine"
        btp.run(plugin='MultiProc', plugin_args={'n_procs' : 4})
    elif input_arguments.wfrun == 'local_3':
        btp.write_graph()
        print "Running with 3 parallel processes on local machine"
        btp.run(plugin='MultiProc', plugin_args={'n_procs' : 3})
    elif input_arguments.wfrun == 'local_12':
        btp.write_graph()
        print "Running with 12 parallel processes on local machine"
        btp.run(plugin='MultiProc', plugin_args={'n_procs' : 12})
    elif input_arguments.wfrun == 'local':
        try:
            btp.write_graph()
        except:
            pass
        print "Running sequentially on local machine"
        btp.run()
    else:
        print "You must specify the run environment type. [helium_all.q,ipl_OSX,local_3,local_4,local_12,local]"
        print input_arguments.wfrun
        sys.exit(-1)

if __name__ == "__main__":
    sys.exit(main())
