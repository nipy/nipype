# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    The gif module provides higher-level interfaces to some of the operations
    that can be performed with the niftyseggif (seg_gif) command-line program.
"""
import os
import numpy as np

from nipype.interfaces.niftyseg.base import NIFTYSEGCommand, NIFTYSEGCommandInputSpec
from nipype.interfaces.base import (TraitedSpec, File, Directory, traits, InputMultiPath,
                                    isdefined)

class GifInput(NIFTYSEGCommandInputSpec):
    
    in_file = File(position=2, argstr="-in %s", exists=True, mandatory=True,
                desc="Input target image filename")
    
    database_file = File(position=3, argstr="-db %s", exists=True, mandatory=True,
                desc="Path to database <XML> file")    

    cpp_dir = Directory(exists=True, mandatory=True, position=4, argstr="-cpp %s", 
                        desc="Folder to read/store cpp files.")

    mask_file = File(exists=True, mandatory=False, position=5, argstr="-mask %s", 
                     desc="Mask over the input image [default: none]")

    out_dir = Directory(exists=True, mandatory=False, position=6, argstr="-out %s", 
                        desc="Output folder [default: ./]")
    
class Gif(NIFTYSEGCommand):


    """

  GIF Propagation :
  Usage -> seg_GIF <mandatory> <options>


  * * * * * * * * * * * Mandatory * * * * * * * * * * * * * * * * * * * * * * *

    -in <filename>	| Input target image filename
    -db <XML>   	| Path to database <XML> file
    -cpp <cpp_path>	| Folder to read/store cpp files.

  * * * * * * * * * * * General Options * * * * * * * * * * * * * * * * * * * *

    -mask <filename>	| Mask over the input image
    -out <path> 	| Output folder [./]

    Examples
    --------
    from nipype.interfaces.niftyseg import Gif
    seggif = Gif()
    seggif.inputs.in_file = "T1.nii.gz"
    seggif.inputs.database_file = "db.xml"
    seggif.inputs.cpp_dir = "cpps"
    seggif.inputs.out_dir = "outputs"
    seggif.cmdline
    seg_GIF -in T1.nii.gz -cpp cpps -out outputs

    """

    _cmd = "seg_GIF"

    input_spec = GifInput    

    def _list_outputs(self):
        self._suffix = "_" + self._cmd
        return super(Gif, self)._list_outputs()
