#!/usr/bin/python
#coding:utf-8
""" Tools for operating with Freesurfer and FS-FAST"""

from mvpa.misc.io import ColumnData
import os
import subprocess

FS_SHELL='tcsh'
SUBJECTS_DIR='/home/scott/data/mri/subjects'
SESSIONS_DIR='/home/scott/data/mri/sessions'

def call(cmd, wait=True):
    """Executes a command on the shell
    
    This is usefull, say, if freesurfer is sourced in a shell's startup
    script
    
    Executes in the shell defined by FS_SHELL in this module
    """
    print cmd
    p = subprocess.Popen(cmd, shell=True, executable=FS_SHELL)
    if wait:
        p.wait()
        
def fillRibbon(vol, reg):
    (base, vname) = os.path.split(vol)
    out={}
    cmd = 'mri_surf2vol --fillribbon --mkmask --template %s --reg %s'%(vol, reg)
    for hemi in ['lh', 'rh']:
        out[hemi]=os.path.join(base, hemi+'.ribbon.'+vname)
        call(cmd + ' --hemi ' + hemi + ' --o ' + out[hemi])
    call('mri_concat --i %s --i %s --max --o %s'%(out['lh'], out['rh'],
                                                  os.path.join(base, 'ribbon.' + vname)))
    #call("3dcalc -a %s -b %s -expr 'max(a,b)' -prefix %s"%(out['lh'], out['rh'],
                                                           #os.path.join(base, 'ribbon.' + vname)))
        
def mris_volsmooth(vol, out, reg=None, fwhm=5):
    """Smooths a 3/4D volume along the cortical surface, preserving the 
    dimensions of the image.  Also creates a mask in the same directory called
    ribbon.nii.gz (containing both L and R hemispheres)
    
    works slightly differently from Freesurfer's mris_volsmooth: 
    1) Non-ribbon voxels are not filled
    2) trilinear interpolation
    
    :reg: path to registration file
    If None looks for fs.register.dat in same directory as volume
    """
    
    (folder, volim) = os.path.split(vol)
    if reg is None:
        reg = os.path.join(folder, 'fs.register.dat')
    if not os.path.isfile(reg):
        raise RuntimeError('No register file %s found'%reg)
    
    if os.path.isfile(out):
        os.remove(out)
    
    tempsurf = os.path.join(folder, 'tmpsurf.mgz')
    
    cmd = 'mri_vol2surf --mov %s --reg %s --interp trilinear'%(vol, reg)
    cmd += ' --projfrac-avg 0 1 .1 --surf-fwhm %i'%fwhm
    cmd += ' --o ' + tempsurf
    for hemi in ['lh', 'rh']:
        # Projects to surface
        call(cmd + ' --hemi ' + hemi)
        surf2vol = 'mri_surf2vol --fillribbon --surfval %s'%tempsurf
        surf2vol += ' --hemi %s --o %s --reg %s'%(hemi, out, reg)
        if os.path.isfile(out):
            surf2vol += ' --merge ' + out
        else:
            surf2vol += ' --template ' + vol
        call(surf2vol)
    os.remove(tempsurf)
    
    # Ribbon mask
    mask = os.path.join(folder, 'ribbon.nii.gz')
    cmd = 'mri_surf2vol --mkmask --fillribbon --reg %s'%reg
    call(cmd+' --hemi lh --template %s --o %s'%(vol, mask))
    call(cmd+' --hemi rh --merge %s --o %s'%(mask, mask))
    
def vol2surf(vol, out, hemi, reg=None, subject=None, target=None,
             fwhm=None, addArgs='', wait=True, interp='trilinear',
             proj='projfrac-avg 0 1 .1', icoOrder=7):
    """Paints a volume onto a FS surface
    
    :vol:
    path to the volume to project onto the surface
    
    :out:
    path to output volume
    
    The extension can be anything freesurfer can write (nii, nii.gz, mgh, etc..)
    BUT because one voxel is written per node, a weird reshape is done because 
    NII's can only have 32000 voxels per dim (and the surface is ~150k).  So
    nii's are safe for fsaverage or ico surfaces, but not in general, since the
    number of vertices for a given subject may not have factors.  Use mgh or w
    for individuals
    
    :hemi:
    'lh' or 'rh', which is automatically prepended to the output name
    
    :reg:
    path to the register.dat aligning the volume to the subject's T1
    If none, then the headers are used for registration (require subject)
    
    :subject:
    the source subject to map to (required if different from reg file or if 
    reg file not provided)
    
    :target:
    Final surface target.  None -> source subject
    Common option is 'fsaverage'
    
    :fwhm:
    smooth the input volume along the surface in mm
    
    :addArgs:
    any additional command line args to be sent to mri_vol2surf
    
    :wait:
    Whether to pause execution until subprocess terminates
    
    :proj:
    Projection string sent to vol2surf
    
    :interp:
    'nearest' or 'trilinear'
    
    """
    path, name = os.path.split(out)
    if not name[:3] == '%s.'%hemi:
        name = '%s.%s'%(hemi, name)
    out = os.path.join(path, name)
    cmd = 'mri_vol2surf --%s --interp %s'%(proj,interp)
    cmd += ' --mov %s --out %s --hemi %s'%(vol, out, hemi)
    if not reg is None:
        cmd += ' --reg %s'%reg
    elif subject is None:
        raise NotImplementedError()
    else:
        cmd+= ' --regheader %s'%subject
    if not target is None:
        cmd+= ' --trgsubject %s'%target
    if target is 'ico':
        cmd += ' --icoorder %i'%icoOrder
    if not (addArgs == '' or addArgs is None):
        cmd += ' %s'%addArgs
        
    call(cmd, wait=wait)
class Par(ColumnData):
    """Class for interacting with *.par paradigm files"""
    # Header names for data, consistent with FSL's EV3
    HEADERS=['onsets', 'cond', 'durations', 'name']
    def __init__(self, source, ncols=4, **kwargs):
        """Reads in a paradigm *.par file
        
         The par file should be either 3 columns (onset, cond#, duration)
         and ideally 4 (w/ cond name).
         
         Currently PyMVPA's ColumnData class seems to only work if the headers
         are fed in, meaning that the par file must have exactly ncols number 
         of columns (ie all entries must have all 4 fields, or 3, etc, 
         otherwise an error will be thrown)
         
         ncols must be 2, 3 or 4
         ideally it should be autodetected from data, pending bugfix above
         
         Any kwargs get passed up to ColumnData (Don't use the headers kwarg,
         as it's created automatically)
         """
        
        assert ncols >=2 and ncols <= 4
        ColumnData.__init__(self, source, header=Par.HEADERS[:ncols], **kwargs)

    
    
class McDat(ColumnData):
    """Class for interacting with motion correction fmc.mcdat output files"""
    # This filetype is produced by mc-afni2, which states that the file contains:
    HEADERS=['n', 'roll', 'pitch', 'yaw', 'dcol', 'drow', 'dslice', 'rmsold', 'rmsnew', 'trans']
    def __init__(self, source, **kwargs):
        """Reads a *.mcdat from file"""
        ColumnData.__init__(self, source, header=McDat.HEADERS, **kwargs)
