# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""FIX THIS XXX FIX THIS

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)

"""
__docformat__ = 'restructuredtext'

import os
from glob import glob
import itertools
import numpy as np

from nipype.externals.pynifti import load
from nipype.utils.filemanip import fname_presuffix
from nipype.interfaces.io import FreeSurferSource

from nipype.interfaces.freesurfer.base import FSCommand, FSTraitedSpec
from nipype.interfaces.base import (TraitedSpec, File, traits,
                                    Directory, InputMultiPath)
from nipype.utils.misc import isdefined


class SurfaceScreenshotsInputSpec(FSTraitedSpec):

    subject = traits.String(position=1,argstr="%s",mandatory=True,
                            desc="subject to visualize")
    hemi = traits.Enum("lh","rh",position=2,argstr="%s",mandatory=True,
                       desc="hemisphere to visualize")
    surface = traits.String(position=3,argstr="%s",mandatory=True,
                            desc="surface to visualize")
    show_curv = traits.Bool(argstr="-curv",desc="show curvature",xor=["show_gray_curv"])
    show_gray_curv = traits.Bool(argstr="-gray",desc="show curvature in gray",xor=["show_curv"])
    screenshot_stem = traits.String(desc="stem to use for screenshot file names")
    tcl_script = traits.File(exists=True, argstr="-tcl %s",genfile=True, 
                             desc="override default screenshot script")

class SurfaceScreenshotsOutputSpec(TraitedSpec):
    
    pass

class SurfaceScreenshots(FSCommand):

    _cmd = "tksurfer"
    input_spec = SurfaceScreenshotsInputSpec
    output_spec = SurfaceScreenshotsOutputSpec

    def format_args(self, name, spec, value):
        if name == "tcl_script":
            if not isdefined(value):
                if not isdefined(self.inputs.screenshot_stem):
                    stem = "%s_%s_%s"%(
                            self.inputs.subject, self.inputs.hemi, self.inputs.surface)
                else:
                    stem = self.inputs.screenshot_stem
                self.write_tcl_script(stem)
                return "-tcl screenshots.tcl"
        return super(SurfaceScreenshots, self)._format_arg(name, spec, value)
        
    def write_tcl_script(self, stem):
        fid = open("screenshots.tcl","w")
        fid.write("\n".join(["save_tiff %s-lat.tif"%stem,
                             "make_lateral_view",
                             "rotate_brain_y 180",
                             "redraw",
                             "save_tiff %s-med.tif"%stem,
                             "make_lateral_view",
                             "rotate_brain_x 90",
                             "redraw",
                             "save_tiff %s-ven.tif"%stem,
                             "make_lateral_view",
                             "rotate_brain_x -90",
                             "redraw",
                             "save_tiff %s-dor.tif"%stem,
                             "exit"]))
        fid.close()

    def _gen_filename(self, name):
        if name == "tcl_script":
            return "screenshots.tcl"
        return None
