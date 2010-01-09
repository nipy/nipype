#!/usr/bin/python
#coding:utf-8

"""Allows calling Matlab functions from python"""
import subprocess

_matlab=None
tester=1
def call(command, exit=True, wait=True, async=False):
    """Init matlab, batch a command, then exit (synchronous with python)
    
    Subsequent calls will open new Matlab processes.  For issueing new commands
    to the same Matlab session, use acall()
    
    :command:
    a single line of code to run in Matlab.  Multiple commands can be issued
    with ';' separating them, but anything fancier should be invoked in an m-
    file
    
    :exit:
    exits matlab as soon as code completes
    
    :wait:
    block python execution until matlab terminates
    
    If exit is False and wait is True, this program may block indefinitely.
    Your matlab command must call 'exit' at some point or there must be another
    method for ending the process
    
    :async:
    If True, calls acall instead.  Overrides other kwargs
    """
    if async:
        acall(command)
        return
    
    if exit:
        command += '; exit'
    p = subprocess.Popen('matlab -nosplash -nodesktop -r "%s"'%command, shell=True)
    
    if wait:
        p.wait()
        
def acall(command, **initkwargs):
    """Async execute a single line of matlab code using pipe to Popen

    The process will not terminate until the python process ends, but python
    will also not wait for the command to finish!  Call await() at end of script
    to ensure everything is flushed.
    
    Subsequent calls will be executed in the same Matlab process, but they will
    not run until Matlab has finished the last set of commands.  This does NOT
    block Python while Matlab is processing.  It DOES allow you to reuse
    variables in the Matlab workspace.
    
    One real benefit to this process is that matlab is only initialized once,
    meaning it is faster, but also avoids pesky license limitations (like if
    the internet drops your vpn connection to a site license)
    
    :command:
    Perfectly okay to run several commands separated by ';' just so long as it
    is only one string of code.  So, eg:
    
    call('a=randn(50, 1); plot(a)')
    
    A single instance of matlab is maintained (if possible) in the global
    matlab object.
    
    :initkwargs:
    not implemented
    
    """
    print command
    global _matlab
    if _matlab is None:
        _matlab=subprocess.Popen('matlab', stdout=None,#subprocess.PIPE,
                                 stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        _matlab.stdin.flush()
    _matlab.stdin.write(command+'\n')
def await():
    """Waits for all asynchronous commands to finish
    
    Works by writing 'exit' to the Matlab input buffer and waiting for it to
    quit
    
    AFAIK there is no way to do this without closing the matlab process, since
    it relies on Popen.wait().  It would, of course, be better to find an
    alternate way to sync... Maybe a filewrite? Or write something in the
    buffer?
    
    Another call to acall() will simply open a new matlab session, but this 
    requires a new license check and startup time. Also can't reuse variables...
    """
    global _matlab
    if not _matlab is None:
        acall('exit')
        _matlab.wait()
        _matlab=None
if __name__ == '__main__':
    call('ver')
    acall('logo')
    acall('peaks')
    acall('pause(3)')
    await()
    print 'Successfully ran Matlab!!'
    pass
