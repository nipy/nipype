# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provides interfaces to various commands provided by Camino
"""

#
import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import os                                    # system functions

import re
from glob import glob
from nibabel import load
from nipype.utils.filemanip import fname_presuffix, split_filename, copyfile
from nipype.utils.misc import isdefined
__docformat__ = 'restructuredtext'

from nipype.interfaces.base import (TraitedSpec, File, traits, CommandLine,
    CommandLineInputSpec)

class ConmapInputSpec(CommandLineInputSpec):
	in_file = File(exists=True, argstr='-inputfile %s',
					mandatory=True, position=1,
					desc='tract filename')
		
	roi_file = File(exists=True, argstr='-roifile %s',
					mandatory=True, position=2,
					desc='roi filename')
	
	index_file = File(exists=True, argstr='-indexfile %s',
					mandatory=False, position=3,
					desc='index filename (.txt)')
	
	label_file = File(exists=True, argstr='-labelfile %s',
					mandatory=False, position=4,
					desc='label filename (.txt)')

	out_file = File(argstr="> %s", position=-1, genfile=True)
	
	threshold = traits.Int(argstr='-threshold %d', units='NA',
				desc="threshold indicates the minimum number of fiber connections that has to be drawn in the graph.")

class ConmapOutputSpec(TraitedSpec):
	conmap_txt = File(exists=True, desc='connectivity matrix in text file') 

class Conmap(CommandLine):
    _cmd = 'conmap'
    input_spec=ConmapInputSpec
    output_spec=ConmapOutputSpec
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["conmap_txt"] = os.path.abspath(self._gen_outfilename())
        return outputs
        
    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + "_conmap"
