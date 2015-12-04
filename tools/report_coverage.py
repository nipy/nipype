#!/usr/bin/env python

from __future__ import print_function
import subprocess


def run_tests(cmd):
    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True)
    stdout, stderr = proc.communicate()
    if proc.returncode:
        msg = 'Running cmd: %s\n Error: %s' % (cmd, error)
        raise Exception(msg)
    # Nose returns the output in stderr
    return stderr


def grab_coverage(output):
    """Grab coverage lines from nose output."""
    output = output.split('\n')
    covout = []
    header = None
    tcount = None
    for line in output:
        if line.startswith('nipype.interfaces.') or \
                line.startswith('nipype.pipeline.') or \
                line.startswith('nipype.utils.'):
            # Remove the Missing lines, too noisy
            percent_index = line.find('%')
            percent_index += 1
            covout.append(line[:percent_index])
        if line.startswith('Name '):
            header = line
        if line.startswith('Ran '):
            tcount = line
    covout.insert(0, header)
    covout.insert(1, '-' * 70)
    covout.append('-' * 70)
    covout.append(tcount)
    return '\n'.join(covout)


def main():
    cmd = 'nosetests --with-coverage --cover-package=nipype'
    print('From current directory, running cmd:')
    print(cmd, '\n')
    output = run_tests(cmd)
    report = grab_coverage(output)
    print(report)

main()
