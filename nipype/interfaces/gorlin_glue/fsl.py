#!/usr/bin/python
#coding:utf-8
"""Routines to automate with FSL"""

import os
import operator
import subprocess
from mvpa.misc.fsl import *
import glob
import numpy as N
FSL_SHELL='tcsh'
def junk_reg_standard(feat):
    """Adds junk data to a feat directory to enable direct use in FFX
    
    Useful ie when using surface-sampled data which should not be resampled in
    3d standard space

    :feat: feat directory
    """
    
    rs = os.path.join(feat, 'reg_standard')
    if not os.path.exists(rs):
        call('ln -s %s %s'%(feat, rs))
    reg=os.path.join(feat, 'reg')
    if not os.path.exists(reg):         
        os.mkdir(reg)
    if not os.path.isfile(os.path.join(feat, 'design.lev')):
        f=open(os.path.join(feat, 'design.lev'), mode='w')
        f.write('junk')
        f.close()#Presence of this file makes featregapply exit (thinks its higher level)
    if not os.path.isfile(os.path.join(reg, 'example_func2standard.mat')):
        f=open(os.path.join(reg, 'example_func2standard.mat'), mode='w')
        f.write('junk')
        f.close()
        f=open(os.path.join(reg, 'standard2example_func.mat'), mode='w')
        f.write('junk')
        f.close()
def cleanFeat(feat, filtered=True, res=True, corrections=True, old=True):
    """Remove large files from a feat directory
    
    Currently removes (toggled with kw flags):
    {feat}/filtered_func_data
    {feat}/stats/res4d
    {feat}/stats/corrections
    """
    def clean(*fpath):
        f = imglob(os.path.join(feat, *fpath))
        if os.path.exists(f):
            print 'Cleaning ' + f
            os.remove(f)
    if filtered:
        clean('filtered_func_data')
    if res:
        clean('stats', 'res4d')
    if corrections:
        clean('stats', 'corrections')
    if old:
        f = os.path.join(feat, 'old')
        if os.path.isdir(f):
            print 'Cleaning ' + f
            shutil.rmtree(f)
        
def imstrip(f):
    """Strips valid image extensions from an image path
    
    :f:
    path to file, like ./im.nii, ./im.nii.gz, etc
    
    :returns:
    Path to file without extension
    """
    (path, im) = os.path.split(f)
    (imroot, imext) = os.path.splitext(im)
    if imext in ['.gz']:
        (imroot, imext) = os.path.splitext(imroot)
    return os.path.join(path, imroot)

def imglob(f, strip=True, first=True):
    """Finds a file with the given path/imroot name

    :strip:
    automatically strips the extension off the input path.  This is only a 
    problem if the name contains multiple '.' like lh.myim.nii and is *not*
    passed in with the extension
    
    ie, if strip is True, lh.myim will be stripped to lh (as myim would be
    considered the extension)
    
    :first:
    If more than one file is found, the first is returned (may be able to set
    extension preference, like return nii if present, if enough wit is applied:)
    
    If false, returns a list (only if more than one file is found)
    
    :returns:
    empty string if no files are found
    """
    if strip:
        f = imstrip(f)
    files = glob.glob(f+'.*')
    if len(files)==0:
        return ''
    if first or len(files)==1:
        return files[0]
    return files
    
def call(cmd, wait=True):
    """Executes a command on the shell
    
    This is usefull, say, if FSL is sourced in a shell's startup
    script
    
    Executes in the shell defined by FSL_SHELL in this module
    """
    print cmd
    p = subprocess.Popen(cmd, shell=True, executable=FSL_SHELL)
    if wait:
        p.wait()
        
class Feat(object):
    """Runs FSL.FEAT to automate *.fsf file creation

    This has the benefit over manually writing a fsf file of using 
    FEAT itself to generate contrasts, design matrix, convolutions, etc
    
    Really, this is a 'meta-script' in that it generates a script to generate a 
    script :)
    
    This works by writing a tcl script to call the FEAT GUI functions
    automatically
    
    typical process should mimick the order of a FEAT setup, as it is processed
    sequentially:
    f = Feat(fn, initialdict, kwargs for setFMRI)
    f.addFMRI(any other kwargs)
    f.writeEnding(interactive=,runImmediately=) if you want to view the feat, 
    or directly run it f.generate() runs Feat and generates the design
    """                   
    def __init__(self, filename=None, feat=None, **kwargs):
        """Initialize creation
        
        :filename:
        filename should be a name (including directory) to store, *.fsf not needed
        
        This is only where the temporary generation files are stored, and where
        the FSF is saved.  This does not override the outputdir option.
        
        can pass in a list of keywords to populate the FEAT properties in the
        fmri structure.  To know what they are, you'll have to look them up in a fsf 
        file or read the sources in feat.tcl or featlib.tcl
        
        A list of useful set_fmri parameters (may be FSL version dependent),
        see also self.setFMRI
        
        defaults are loaded independently via the FEAT gui, so everything 
        should be identical to doing this all by hand (just faster ;)
        
        see feat.tcl and featlib.tcl (in $FSLDIR/tcl) for reference
        
        
        """

        self._generated=False
        if filename is None:
            filename = os.tmpnam()
        self._fn = filename
        (filepath, filename) = os.path.split(filename)
        (root, ext) = os.path.splitext(filename)
        self._fsffile=os.path.join(filepath, root+'.fsf')
        # Default parameters
        self._fmri = {}
        
        # Creates launcher *.tcl script
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        self._scriptfile = os.path.join(filepath, root+'.tcl')
        tcl = open(self._scriptfile, mode='w')
        self._tcl = tcl
        tcl.write('#!/bin/sh\n\n')
        tcl.write('# Shell script to generate an FSL.FEAT *.fsf file\n')
        tcl.write('# program written by Scott Gorlin 11/27/2008\n')
        tcl.write('# Autogenerated by a python function\n')
        tcl.write('# Set TCLTKSHELL \\\n')
        tcl.write('TCLTKSHELL=wish ; export TCLTKSHELL\n\n')
        tcl.write('# Launch using WISH \\\n')
        tcl.write('if [ _$FSLWISH = _ ] ; then echo "You need to source an FSL setup file - either fsl.sh or fsl.csh in \$FSLDIR/etc/fslconf !" ; exit 1 ; else exec $FSLWISH "$0" -- "$@"; fi\n\n')
        
        # Creates *.tcl script
        tcl.write('# TCL script to generate an FSL.FEAT *.fsf file\n')
        tcl.write('# Autogenerated by a python function\n')
        tcl.write('# program written by Scott Gorlin 11/27/2008\n\n')
      
        tcl.write('# This is a hack to allow FEAT to run with console interaction\nglobal INGUI\nset INGUI 1\n')
        tcl.write('set FSLDIR $env(FSLDIR)\n')
        tcl.write('source ${FSLDIR}/tcl/feat.tcl\n\n')
    
        tcl.write('# Manually launch FEAT, but now with script control\n')
        tcl.write('wm withdraw .\nfeat5 .r\n')
        self.__wait('.r\n')
        tcl.write('# Overwrites the MxPause function, because this breaks automation\n')
        tcl.write('global MxPause\n')
        tcl.write('proc MxPause {msg} {}\n\n')
        tcl.write('# Useful function for getting dialog windows\n')
        tcl.write('global lastDialog\n')
        tcl.write('proc getDialog {prefix} { \n')
        tcl.write('    global lastDialog\n')
        tcl.write('    set dialog dialog\n')
        tcl.write('    set count 1\n')
        tcl.write('    while { [ winfo exists ".$prefix$dialog$count"] } {\n')
        tcl.write('        set lastDialog ".$prefix$dialog$count"\n')
        tcl.write('        incr count\n')
        tcl.write('    }\n')
        tcl.write('}\n\n')
        tcl.write('# Begin custom arguments\n')
        
        self.setFMRI(**kwargs)
    def execute(self):
        """Executes the file (assuming runImmediately wasn't called)"""
        self.generate()
        call('feat %s'%self._fsffile)
    def setLevel(self, level):
        """Sets low-level (level=1) or higher-level(level=2) analysis
        Should be the first thing set (if second level)"""
        self.setFMRI(level=level)
        self._tcl.write('feat5:updatelevel .r\n')
    def setAnalysis(self, analysis):
        """Sets the steps of analysis to perform
        Should be the second (after setLevel) thing to call
        
        analysis                       # see an fsf file. controls which to run:
        * 0 : No first-level analysis (registration and/or group stats only)
        * 7 : Full first-level analysis
        * 1 : Pre-Stats
        * 3 : Pre-Stats + Stats
        * 2 :             Stats
        * 6 :             Stats + Post-stats
        * 4 :                     Post-stats
        """
        self.setFMRI(analysis=analysis)
        self._tcl.write('feat5:updateanalysis .r\n')
    # Modelling
    def modelWizard(self, wizard_type=1, r_count=16, a_count=16, b_count=16):
        """Simple model setup
        
        :wizard_type: 
        First level: 1 rArAr... 2 rArBrA... 3 perfusion
        Higher level: 1 single group avg 2 two groups unpaired 2 paired
        
        :r_count, a_count, b_count:
        seconds in rest, a, and b conditions
        
        :a_count:
        if higherlevel, and wizard_type=2, is #subjects in first group
        
        Don't use wizard with the full setup
        """
        self._tcl.write('# Model Wizard\n')
        if not self._fmri.has_key('level'):
            self.setFMRI(level=1) # 1st or higher level analysis
        
        self._tcl.write('feat5:wizard .r\n')
        self.__getLastDialog()
        self.__wait('$lastDialog')
        self.setFMRI(wizard_type = wizard_type)
        self._tcl.write('feat5:update_wizard $lastDialog\n')
        if self._fmri['level'] == 1:
            # 1st level wizard
            self.setFMRI(r_count=r_count, a_count=a_count, b_count=b_count)
        elif wizard_type==2:
            # If 2 groups nonpaired, need to know number in first group
            self.setFMRI(a_count=a_count)
        self._tcl.write('feat5:updatestats .r 1 ; destroy $lastDialog\n')
    def updateModel(self):
        """Call if just running poststats, after loading the Feat dir, otherwise
        there may be errors running Feat
        
        Should expand this to allow new options, currently just loads what's set
        in stats
        """
        self._tcl.write('feat5:setup_model .r\n')
        self.__getLastDialog('w')
        self.__wait("$lastDialog")
    def modelFull(self, evs, cons, groups=None, con_mode='orig'):
        """Runs the full model setup
        
        :evs:
        evs should be a dict or list of dicts containing any of the following 
        (or alternately a ModelEV object handling the dict interface):
        
        evtitle shape skip off on phase stop period nharmonics convolve 
        convolve_phase gausssigma gaussdelay bfcustom basisfnum basisfwidth 
        tempfilt_yn default_deriv_yn deriv_yn
        
        For higher level analysis, it should contain the field 'evg' which is a
        list of values for that ev 
        
        :groups: for higher level analysis, is a list containing the group
        numbers.
        
        # shape: 
        * 0 : Square 
        * 1 : Sinusoid 
        * 2 : Custom (1 entry per volume)
        * 3 : Custom (3 column format) 
        * 4 : Interaction 
        * 10 : Empty (all zeros)
        include the field 'custom' with the path to the file if choosing 2 or 3
        
        # convolve 
        * 0 : None 
        * 1 : Gaussian 
        * 2 : Gamma 
        * 3 : Double-Gamma HRF
        * 4 : Gamma basis functions 
        * 5 : Sine basis functions 
        * 6 : FIR
        * 7 : FLOBS optimal basis functions
        
        :cons:
        cons should be a dict or list of dicts with fields:
        conname, conpic, c
        conpic: whether to include in webpage report
        c is a vector either of the weights directly indexed against the EVs
        (though remember that FSL is 1-based, and Python is 0 based)
        or a list of EV's with weight 1, times the sign
        
        i.e. c=[1 -2] would mean contrast 1 gets +1 and contrast 2 gets -1
        
        This latter style only works if the length of c is less than the
        number of EV's.  If the lengths are equal, it is assumed that every
        EV is given the weight at that index
        
        Alternatively, c can be a dict with keys to the (1-based) EV's to 
        sparsely set the weights
        
        cons can also have the field conpic which decides whether they
        are included in Feat's webpage output
        
        may also include a field 'f' in each contrast specifying (in list form)
        which f-tests it should belong to
        """
        self._tcl.write('# Full model setup\n')
        if not self._fmri.has_key('level'):
            self.setFMRI(level=1) # 1st or higher level analysis
            
        self._tcl.write('feat5:setup_model .r\n')
        self.__getLastDialog(prefix='w')
        self.__wait("$lastDialog")
        if isinstance(evs, dict):
            evs=[evs]
        
        if self._fmri['level'] == 1:
            # Explanatory Values
            nevs = len(evs)
            self.setFMRI(evs_orig=nevs)
            self._tcl.write('feat5:setup_model_update_evs .r $fmri(evsf) 1\n')
            for (i, ev) in enumerate(evs):
                for k,v in ev.items():
                    self.setFMRI(**{(k+'%d'%(i+1)):v})
                    if k=='convolve':
                        self._tcl.write('feat5:setup_model_update_ev_i .r $fmri(evsf) %d 2 1\n'%(i+1))
            self._tcl.write('feat5:setup_model_update_evs .r $fmri(evsf) 1\n')
            
        else:
            # Groups (2nd level only)
            con_mode = 'real'
            if groups:
                for i,g in enumerate(groups):
                    self.setFMRI(**{('groupmem.%i'%(i+1)):g})
            
            # EV's
            nevs = len(evs)
            self.setFMRI(evs_orig=nevs)
            self._tcl.write('feat5:setup_model_update_evs .r $fmri(evsf) 1\n')
            for i, ev in enumerate(evs):
                title = ev.get('evtitle', '')
                self.setFMRI(**{('evtitle%i'%(i+1)):title})
                for (ii, evval) in enumerate(ev['evg']):
                    self.setFMRI(**{('evg%i.%i'%(ii+1, i+1)):evval})
        
        # Contrasts
        if not operator.isSequenceType(cons):
            cons=[cons]
        self.setFMRI(**{'con_mode':con_mode, ('ncon_'+con_mode):len(cons)})
        
        self._tcl.write('feat5:setup_model_update_contrasts .r\n')
        maxf = 0
        
        args={}
        for (i, c) in enumerate(cons):
            # Optionals
            if c.has_key('conname'):
                args['conname_%s.%d'%(con_mode,i+1)]=c['conname']
            if c.has_key('conpic'):
                args['conpic_%s.%d'%(con_mode,i+1)]=c['conpic']
            if c.has_key('f'):
                if not operator.isSequenceType(c['f']):
                    c['f'] = [c['f']]
                for ff in c['f']:
                    if ff > maxf:
                        maxf=ff
                    args['ftest_%s%d.%d'%(con_mode,i+1,ff)] = 1
                    
            # The actual contrast
            if isinstance(c['c'], dict):
                cdict=c['c']
            else:
                if operator.isNumberType(c['c']):
                    c['c']=[c['c']]
                cdict={}
                if len(c['c'])==nevs:
                    for (j, cval) in enumerate(c['c']):
                        cdict[j+1]=cval
                else:
                    for cval in c['c']:
                        cdict[abs(cval)]=2*(cval>0)-1# This is lame, should use numpy.sign
            for (j,v) in cdict.items():
                args['con_%s%d.%d'%(con_mode, i+1, j)]=v
        self.setFMRI(**{('nftests_'+con_mode):maxf})
        self.setFMRI(**args)
        
        self._tcl.write('feat5:setup_model_update_contrasts .r\n')
        self._tcl.write('feat5:setup_model_destroy .r $lastDialog\n')
    # Misc
    def addFiles(self, files, whichFiles='feat_files'):        
        """Add input files/copes/directories etc
        Files may be a string or list/tuple of strings

        whichFiles is either an integer or a name which is mapped to the other:

        feat_files=0,
        unwarp_files=1, 
        unwarp_files_mag=2,
        initial_highres_files=3,
        highres_files=4,
        confoundev_files=20
        """
        
        if isinstance(files, str):
            files=[files]
        # Sets variables
        varname = dict(feat_files=0, unwarp_files=1, 
                       unwarp_files_mag=2,initial_highres_files=3,
                       highres_files=4,confoundev_files=20)
        varn = {}
        for (k,v) in varname.items():
            varn[v]=k # Reverse maps
        try:
            if operator.isNumberType(whichFiles):
                wf = varn[whichFiles]
                wn = whichFiles
            else:
                wn = varname[whichFiles]
                wf = whichFiles
        except KeyError:
            Exception('FSL data requires the whichFiles to be set appropriately: %s'%wf)
        
        if wf == 'feat_files':
            self.setFMRI(multiple=len(files))
            
        # Inits multi-select
        self._tcl.write('feat5:multiple_select .r %d {Auto-setting files}\n'%wn)
        self.__getLastDialog()
        self.__wait('$lastDialog')
        
        # Writes filenames
        for (i, f) in enumerate(files):
            self._tcl.write('set %s(%d) %s\n'%(wf, i+1, f))
        
        # Hits 'OK'
        self._tcl.write('feat5:multiple_check .r %d 1 1 d; destroy $lastDialog\n'%wn)
        
        if (wn == 3) or (wn == 4):
            self._tcl.write('feat5:updatereg_hr_init .r\n')
            
    def __wait(self, window):
        """Waits for a window to get setup"""
        self._tcl.write('tkwait visibility %s\n'%window)
    def __getLastDialog(self, prefix='""'):
        """Locally gets the window for the last dialog.  Users should not call"""
        self._tcl.write('getDialog %s\n'%prefix)
    def setFMRI(self, **kwargs):
        """For each keyword, adds that value in a set fmri(key) value call
        This is the major way to set a preference/option in the FEAT file
        
        Script will autodetect whether val is a string or number
        
        Also stores all added keys in self._fmri for later reference
        
        The keys to use are all pretty similar to their GUI counterparts,
        but unfortunately, you'll have to look at an fsf file or the tcl
        scripts to know the exact names you want
        
        The following list should help, but it is not meant to be complete:
        
        # Misc   
        (use self.setLevel and self.setAnalysis for these two)
        level                          # 1->first 2-> higher-level analysis
        analysis                       # see an fsf file. controls which to run:
        * 0 : No first-level analysis (registration and/or group stats only)
        * 7 : Full first-level analysis
        * 1 : Pre-Stats
        * 3 : Pre-Stats + Stats
        * 2 :             Stats
        * 6 :             Stats + Post-stats
        * 4 :                     Post-stats
        overwrite_yn  (not in gui!!)   # 0->amends names with -or+ if fn exists
        relative_yn                    # relative filenames
        sscleanup_yn                   # cleanup first level standard space
        featwatcher_yn                 # Whether to run featwatcher
        
        # Data
        inputtype                      # 1: featdirs 2: copes
        tr
        outputdir
        npts                           # number of timepoints in each scan
        ndelete
        dwell
        te
        
        # Prestats
        filtering_yn
        mc
        smooth                         # FWHM in mm
        prewhiten_yn
        motionevs
        confoundevs                    # bool.  must set file with addFiles()
        regunwarp_yn
        unwarp_dir
        st                             # slice timing correction
        bet_yn
        norm_yn
        temphp_yn                      # Highpass temporal filter
        templp_yn
        melodic_yn
        robust_yn                      # FLAME (higher-level) outlier detection
        paradigm_hp                    # Highpass filter cutoff (seconds?)
        
        # Stats
        mixed_yn                       # Higher-level modelling
        * 3 : Fixed effects
        * 0 : Mixed Effects: Simple OLS
        * 2 : Mixed Effects: FLAME 1
        * 1 : Mixed Effects: FLAME 1+2
        
        # Poststats
        newdir_yn                      # copy original feat directory if redoing
        z_thresh
        thresh
        * 0 "None" 
        * 1 "Uncorrected"
        * 2 "Voxel"
        * 3 "Cluster"
        threshmask
        bgimage
        * 1 "Mean highres"
        * 2 "First highres"
        * 3 "Mean functional"
        * 4 "First functional"
        * 5 "Standard space template"
        
        # Reg - most can be switched between initial, highres, standard
        reginitial_highres_yn      
        reginitial_highres_search
        reginitial_highres_dof
        
        reghighres_yn
        reghighres_search              
        reghires_dof                   
        
        regstandard                     # Filename of standard image
        regstandard_search              # 0, 90, 180
        regstandard_dof                 # Should be 3,6,7, or 12
        regstandard_nonlinear_yn
        regstandard_nonlinear_warpres   # mm
        """
        
        for (key, value) in kwargs.items():
            self._fmri[key]=value
            if operator.isNumberType(value):
                v = '%g'
            else:
                v = '%s'
            self._tcl.write(('set fmri(%s) '+v+'\n')%(key, value))
                            
                            
    def writeEnding(self, interactive=False, runImmediately=False, save=True):
        """This should be the last call in the design file creation.  It writes the exit line and closes.
        (although, if you want the default options, you do not have to call this -
        it is called in self.generate)
        
        If interactive is True, then it leaves the FEAT window open for editing
        
        if runImmediately=True, then it immediately executes the Feat paradigm after creation
        (this is run in a separate process)
        This overrides interactive, since it can just be clicked :)
        
        This func will automatically detect if the file is closed, so calling it
        more than once has no effect"""
        
        if not self._tcl.closed:
            self._tcl.write('# Generation complete! Now saves, maybe runs, maybe waits for user input\n')
            # Saves
            if save:
                #self._tcl.write('feat_file:setup_dialog .r a a a [namespace current] *.fsf {Save Feat setup} {feat5:write .r 1 1 0} {}\n')
                self._tcl.write('feat5:write .r 1 1 0 %s\n'%self._fsffile)
            # Runs and/or exits or remains
            if runImmediately:
                self._tcl.write('feat5:apply .r\n')
            elif interactive:
                self._tcl.write('tkwait window .r\n')
            self._tcl.write('exit\n')
            self._tcl.close()
    def generate(self, shell='tcsh'):
        """Calls the generated file, produces the FEAT design
        
        Will only run once per file (safe to call multiple times if necessary)
    
        the shell should be your normal shell with the sourced fsl files on linux
        (haven't tried other OSes yet)
        """
        if not self._generated:
            # Closes file if not already done:
            self.writeEnding()
            
            def popen(cmd):
                subprocess.Popen(cmd, shell=True, executable=shell).wait()
            
            # Ensures the file has execute permissions (OS dependent - needs revision)
            popen('chmod 777 '+ self._scriptfile)
            
            # Runs the file, opening FEAT and generating the design
            popen(self._scriptfile)
            
            # Won't run again unless forced by marking this false
            self._generated=True
            
        
class ModelShape(dict):
    """Namespace for shape constants"""
    Square = 0
    Sinusoid = 1
    Custom1 = 2
    Custom3 = 3
    Interaction = 4
    Empty = 10
    _locals = locals()
    
class ModelCustomShape(ModelShape):
    def __init__(self, fn, shape=ModelShape.Custom3):
        """Class which models a custom (file-based shape)
        
        :Parameters:
          shape: 1 or 3 (for 1 column or 3 column format)
          fn: path to file containing data
        """
        if not(shape==ModelShape.Custom1 or shape==ModelShape.Custom3) or not fn:
            raise RuntimeError("Bad arguments in ModelCustomShape creation")
        ModelShape.__init__(self, shape=shape, custom=fn)
    
class ModelConvolution(dict):
    """Namespace for convolution constants"""
    NoConv = 0
    Gaussian = 1
    Gamma = 2
    DoubleGammaHRF = 3
    GammaBasis = 4
    SineBasis = 5
    FIR = 6
    FLOBS = 7
    _locals = locals()
class ModelFIR(ModelConvolution):
    def __init__(self, pre=2, TR=2, n=6):
        """Models the convolution as FIR
        
        :Parameters:
          pre: Number of timepoints prior to onset to model
          n: number of timepoints after onset to model (contrast with vanilla FSL,
          where n is total number)
          TR: time of TR, so that window and offset etc are appropriately set
        """
        ModelConvolution.__init__(self, convolve=ModelConvolution.FIR,
                                  basisfnum=pre+n, basisfwidth=TR*(pre+n),
                                  convolve_phase=TR*pre)
        
class ModelEV(dict):
    def __init__(self, shape=ModelShape.Square, conv=ModelConvolution.DoubleGammaHRF, **kwargs):
        """Class which describes a single EV in FSL's model
        
        :Parameters:
          shape: Either a constant from ModelShape or a ModelShape object
          conv: Either a constant from ModelConvolution or a ModelConvolution 
          object

          kwargs from: evtitle skip off on phase stop period nharmonics
          convolve_phase gausssigma gaussdelay gammasigma gammadelay bfcustom
          basisfnum basisfwidth tempfilt_yn default_deriv_yn deriv_yn
          
          use kw 'custom' to specify file for custom convolution
        """
        dict.__init__(self)
        if isinstance(shape, ModelShape):
            self.update(shape)
        elif shape in ModelShape._locals.values():
            self['shape']=shape
        else:
            raise RuntimeError('Unrecognized shape %s'%shape)
        
        if isinstance(conv, ModelConvolution):
            self.update(conv)
        elif conv in ModelConvolution._locals.values():
            self['convolve']=conv
        else:
            raise RuntimeError('Unrecognized convolution %s'%conv)
        
        self.update(kwargs)
class Flobs(object):
    def __init__(self, flob='/usr/share/fsl/etc/default_flobs.flobs', nsecs=28.):
        """Interface to Flobs optimal basis sets
        :Parameters:
          flob: directory with stored flob
          
          nsecs: number of seconds in generated flob (not stored in the directory
          unfortunately, which is why it must be input).  If you created the flobs
          yourself then you might know this; check the log file in the flobs 
          directory, which might read something like this:
          /usr/local/fsl/bin/halfcosbasis --hf=/tmp/flobs_rtSk40.txt --nbfs=3 --ns=28 
          in which case nsecs is 28 (which is for the default flobs).
        """
        hrftxt = os.path.join(flob, 'hrfbasisfns.txt')
        try:
            from mvpa.misc.io import ColumnData
            bases = ColumnData(hrftxt, header=['b1', 'b2', 'b3'])
            self.basis = N.asarray([bases['b1'], bases['b2'], bases['b3']])
            self.time = N.arange(0, nsecs, nsecs/float(self.basis.shape[1]))
        except IOError:
            self.basis = None
            self.time = None
    def generateHRF(self, coef1=1., coef2=1., coef3=1., NiftiFormat=False):
        """Linearly combines the basis functions, returns a numpy array
        
        The resulting rfh has dimensions of the coefs +1 (time on axis=-1)
        
        :Parameters:
          coef1: scalar or numpy array which is the coefficient of the first basis
          function
          NiftiFormat: if True, time is created on the first axis (not the last)
          for compatiblility with pynifti
        """
        cs = map(N.asarray, (coef1, coef2, coef3))
        n = max(map(N.ndim, cs))
        if NiftiFormat:
            b = (3,) + (self.time.size,) + (1,)*n
        else:
            b = (3,) + (1,)*n + (self.time.size,)
            cs = [N.resize(c, c.shape + (1,)) for c in cs]
        bases=self.basis
        bases.resize(b)
        bases = [bases[i] for i in range(3)]
        
        return reduce(lambda a, b: a+b[0]*b[1], zip(cs, bases), 0)
    def plot(self):
        """Plots all three bases against time"""
        import pylab
        pylab.plot(self.time, self.basis[0], 'r',
                   self.time, self.basis[1], 'g', 
                   self.time, self.basis[2], 'b')
    def resample(self, TR=2, hrf=None, window=None, NiftiFormat=False):
        """Resamples either the bases, or a created hrf, to a desired time
        interval
        
        I will semi-naively recommend that resampling occur *after* HRF
        generation, especially with time-offset data (like fMRI slices) since
        adding the resampled temporal derivative will likely be much less
        accurate than adding the derivative first, then resampling.
        
        :Parameters:
          hrf: Optional signal to resample, sharing a time axis with this Flobs
          object.  If None, the basis functions of this object are used instead
          window: window parameter passed to scipy.signal.resample.  If ndim >1,
          then time is the last axis.
          NiftiFormat: if True, time is the first axis (only if passing in an
          HRF)
          
        :Returns:
          if hrf was not provided, returns a new resampled Flobs object
          if hrf was provided, returns (resampled_hrf, resampled_time) """
        if hrf is None:
            x = self.basis
            axis=0
        else:
            x = hrf
            if NiftiFormat:
                axis=0
            else:
                axis=-1
        from scipy.signal import resample
        num = N.round(self.time[-1]/TR)
        r = resample(x, num, t = self.time, axis=axis, window=window)
        if hrf is None:
            f = Flobs('')
            f.basis = r[0]
            f.time = r[1]
            return f
        return r
            
class EV3(FslEV3):
    """Provides some extra functionality over the PYMVPA version"""
    
    @staticmethod
    def create(onsets, durations, intensities=None):
        """Creates an EV3 object
        
        All entries must be lists of the same length
        
        :onsets:
        time (seconds) since begining of scan
        
        :durations:
        seconds per event.
        
        :intensities:
        if None, a list of ones is used of the same length as the others
        
        :returns:
        an EV3 object with the given input
        """
        if not operator.isSequenceType(onsets):
            onsets=[onsets]
        if not operator.isSequenceType(durations):
            durations=[durations]*len(onsets)
        if intensities is None:
            intensities = [1]*len(onsets)
        if not operator.isSequenceType(intensities):
            intensities=[intensities]
        assert len(onsets) == len(durations)
        assert len(durations)==len(intensities)
        return EV3({'onsets':onsets, 'durations':durations, 'intensities':intensities})
        
if __name__ == '__main__':
    ## Test
    #f = Feat('/media/Modular/data/mri/sessions/mriseComplex3/kc/bold/007/feat/design')
    #f.addFiles('/home/scott/data/mri/sessions/mriseComplex3/kc/bold/007/fmc.nii')
    #f.setFMRI(tr=2, npts=136)
    #evs=[{'evtitle':'Visual', 'convolve':7, 'on':16, 'off':16}]
    #cons=[{'conname':'VisualResponse', 'c':[1]}]
    #f.modelFull(evs, cons)
    #f.writeEnding(interactive=True, runImmediately=True)
    #f.generate()
    cleanFeat('/home/scott/data/mri/sessions/mriseComplex3/sh/bold/021/blocks.feat')
    #par2ev3('/home/scott/data/mri/sessions/mriseComplex3/kc/bold/007/paradigm.par')
    
    