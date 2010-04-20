'''
Created on 20 Apr 2010

@author: Chris Filo Gorgolewski
'''
import ConfigParser, os
from io import StringIO

default_cfg = StringIO("""
[logging]
workflow_level = INFO
node_level = INFO
filemanip_level = INFO

[execution]
stop_on_first_crash = false
""")

config = ConfigParser.ConfigParser()
config.readfp(default_cfg)
config.read(['nipype.cfg', os.path.expanduser('~/.nipype.cfg')])

