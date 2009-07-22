#!/usr/bin/python

# satra@mit.edu 
import sys, os, string
import scipy.io as sio
import libxml2
import yaml

#### functions ####

def parse2xmldict(jobs,doc=libxml2.newDoc("1.0"),counter=0):
    try:
        for j in jobs:
            try:
                print "  "*counter + "<"+j._fieldnames[0]+">"
                child = doc.newChild(None,j._fieldnames[0],None)
                parse2xmldict(getattr(j,j._fieldnames[0]),child,counter+1)
                print "  "*counter + "</"+j._fieldnames[0]+">"
            except:
                pass
    except:
        for f in jobs._fieldnames:
            try:
                print "  "*(counter) + "<"+f+">"
                child = doc.newChild(None,f,None)
                parse2xmldict(getattr(jobs,f),child,counter+1)
                print "  "*(counter) + "</"+f+">"
            except:
                print "  "*(counter) + "</"+f+">"
                pass
        pass
    return doc

def parse2yamldict(jobs,doc={},counter=0):
    try:
        for j in jobs:
            try:
                print "  "*counter + "- "+j._fieldnames[0]+":"
                parse2yamldict(getattr(j,j._fieldnames[0]),{},counter+1)
            except:
                pass
    except:
        for f in jobs._fieldnames:
            try:
                print "  "*(counter) + "- "+f+":"
                parse2yamldict(getattr(jobs,f),{},counter+1)
            except:
                pass
        pass
    return doc

def parser_core(spmjobname,options,progname):
    """
    Parses the SPM job struct to determine the input requirements for the job.
    The job struct contains defaults for temporal, spatial and stats jobs. 
    """ 
    jobsdict = sio.loadmat(os.path.join(options.matlab_dir,"jobstruct.mat"))
    jobs= jobsdict['jobs']
    joblist = dict()
    for j0 in jobs[1:]:
        j0att = getattr(j0,j0._fieldnames[0])
        for sj0 in j0att:
             joblist.__setitem__(sj0._fieldnames[0],getattr(sj0,sj0._fieldnames[0]))
    print joblist


def parse_spm_struct():
    """
    Wrapper script for the parser that parses the SPM job struct to determine
    the input requirements for the job. The job struct was created with the SPM gui.
    """
    from optparse import OptionParser
    parser = OptionParser(usage='usage: %prog [options] spmjobname',version='0.1')
    parser.add_option("-j", "--job-help", default=False,action="store_true",dest="jobhelp",
                  help="show job specific parameters")
    parser.add_option("-m", "--matlab_dir", default=".",dest="matlab_dir",
                  help="directory with required matlab job template")
    parser.add_option("-v", "--verbose",default=False,
                  action="store_true", dest="verbose")

    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.print_help()
        sys.exit(1)
    else:
        spmjobname = args[0]

    if options.verbose:
        print(options)
        print("Validating arguments")

    parser_core(spmjobname,options,sys.argv[0])

if __name__ == "__main__":
    parse_spm_struct()
