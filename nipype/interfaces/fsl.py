"""The fsl module provides basic functions for interfacing with fsl tools.

Currently these tools are supported:

  * BET: brain extraction
  * FAST: segmentation and bias correction
  * FLIRT: linear registration
  * FNIRT: non-linear warp

Examples
--------
See the docstrings for the individual classes (Bet, Fast, etc...) for
'working' examples.

"""

import os
import subprocess
from copy import deepcopy
from glob import glob
from nipype.utils.filemanip import fname_presuffix
from nipype.interfaces.base import (Bunch, CommandLine, 
                                    load_template, InterfaceResult)
from nipype.utils import setattr_on_read
from nipype.utils.docparse import get_doc
from nipype.utils.misc import container_to_string, is_container
from nipype.utils.filemanip import fname_presuffix
import warnings
warn = warnings.warn

warnings.filterwarnings('always', category=UserWarning)
# If we don't like the way python is desplaying things, we can override this,
# e.g.:
# def warnings.showwarning(message, category, filename, lineno, file=None,
# line=None):
#     print message

def fslversion():
    """Check for fsl version on system

    Parameters
    ----------
    None

    Returns
    -------
    version : string
       Version number as string or None if FSL not found

    """
    # find which fsl being used....and get version from
    # /path/to/fsl/etc/fslversion
    clout = CommandLine('which fsl').run()

    if clout.runtime.returncode is not 0:
        # fsl not found
        return None
    out = clout.runtime.stdout
    basedir = os.path.split(os.path.split(out)[0])[0]
    clout = CommandLine('cat %s/etc/fslversion'%(basedir)).run()
    out = clout.runtime.stdout
    return out.strip('\n')


def fsloutputtype(ftype=None):
    """Check and or set the global FSL output file type FSLOUTPUTTYPE
    
    Parameters
    ----------
    ftype :  string
        Represents the file type to set based on string of valid FSL
        file types ftype == None to get current setting/ options

    Returns
    -------
    fsl_ftype : string
        Represents the current environment setting of FSLOUTPUTTYPE
    ext : string
        The extension associated with the FSLOUTPUTTYPE

    """
    ftypes = {'NIFTI':'nii',
              'ANALYZE':'hdr',
              'NIFTI_PAIR':'hdr',
              'ANALYZE_GZ':'hdr.gz',
              'NIFTI_GZ':'nii.gz',
              'NIFTI_PAIR_GZ':'hdr.gz',
              None: 'env variable FSLOUTPUTTYPE not set'}

    if ftype is None:
        # get environment setting
        fsl_ftype = os.getenv('FSLOUTPUTTYPE')
        #for key in ftypes.keys():
        #    print '%s = \"%s\"'%(key, ftypes[key])

    else:
        # set environment setting
        fsl_ftype = ftype
        os.putenv('FSLOUTPUTTYPE',fsl_ftype)
        os.environ['FSLOUTPUTTYPE'] = fsl_ftype # seems redundant but necessary
    print 'FSLOUTPUTTYPE = %s (\"%s\")'%(fsl_ftype, ftypes[fsl_ftype])
    return fsl_ftype, ftypes[fsl_ftype]
        

class FSLCommand(CommandLine):
    '''General support for FSL commands'''

    @property
    def cmdline(self):
        """validates fsl options and generates command line argument"""
        allargs = self._parse_inputs()
        allargs.insert(0, self.cmd)
        return ' '.join(allargs)

    def run(self):
        """Execute the command.
        
        Returns
        -------
        results : Bunch
            A `Bunch` object with a copy of self in `interface`

        """
        results = self._runner()
        if results.runtime.returncode == 0:
            pass
            # Uncomment if implemented
            # results.outputs = self.aggregate_outputs()

        return results        

    def _parse_inputs(self, skip=()):
        """Parse all inputs and format options using the opt_map format string.

        Any inputs that are assigned (that are not None) are formatted
        to be added to the command line.

        Parameters
        ----------
        skip : tuple or list
            Inputs to skip in the parsing.  This is for inputs that
            require special handling, for example input files that
            often must be at the end of the command line.  Inputs that
            require special handling like this should be handled in a
            _parse_inputs method in the subclass.
        
        Returns
        -------
        allargs : list
            A list of all inputs formatted for the command line.

        """
        allargs = []
        inputs = [(k, v) for k, v in self.inputs.iteritems() if v is not None ]
        for opt, value in inputs:
            if opt in skip:
                continue
            if opt == 'args':
                # XXX Where is this used?  Is self.inputs.args still
                # used?  Or is it leftover from the original design of
                # base.CommandLine?
                allargs.extend(value)
                continue
            try:
                argstr = self.opt_map[opt]
                if argstr.find('%') == -1:
                    # Boolean options have no format string.  Just
                    # append options if True.
                    if value is True:
                        allargs.append(argstr)
                    elif value is not False:
                        raise TypeError('Boolean option %s set to %s' % 
                                         (opt, str(value)) )
                elif type(value) == list:
                    allargs.append(argstr % tuple(value))
                else:
                    # Append options using format string.
                    allargs.append(argstr % value)
            except TypeError, err:
                msg = 'Error when parsing option %s in class %s.\n%s' % \
                    (opt, self.__class__.__name__, err.message)
                warn(msg)
            except KeyError:                   
                warn('Option %s not supported!' % (opt))
        
        return allargs


class Bet(FSLCommand):
    """Use FSL BET command for skull stripping.

    For complete details, see the `BET Documentation. 
    <http://www.fmrib.ox.ac.uk/fsl/bet/index.html>`_

    To print out the command line help, use:
        Bet().inputs_help()

    Examples
    --------
    >>> fsl.Bet().inputs_help()
    >>> better = fsl.Bet(frac=0.5)
    >>> betted = better.run('infile', 'outfile')
    >>> better2 = better.update(frac=0.3)

    >>> btr = fsl.Bet(infile='infile', outfile='outfile', frac=0.5)
    >>> btd = btr.run()
    """

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'bet'

    def inputs_help(self):
        """Print command line documentation for BET."""
        print get_doc(self.cmd, self.opt_map)

    def _populate_inputs(self):
        self.inputs = Bunch(infile=None,
                          outfile=None,
                          outline=None,
                          mask=None,
                          skull=None,
                          nooutput=None,
                          frac=None,
                          vertical_gradient=None,
                          radius=None,
                          center=None,
                          threshold=None,
                          mesh=None,
                          verbose=None, 
                          flags=None)

    opt_map = {
        'outline':            '-o',
        'mask':               '-m',
        'skull':              '-s',
        'nooutput':           '-n',
        'frac':               '-f %.2f',
        'vertical_gradient':  '-g %.2f',
        'radius':             '-r %d', # in mm
        'center':             '-c %d %d %d', # in voxels
        'threshold':          '-t',
        'mesh':               '-e',
        'verbose':            '-v',
        'flags':              '%s'}
    # Currently we don't support -R, -S, -B, -Z, -F, -A or -A2

    def _parse_inputs(self):
        """validate fsl bet options"""
        allargs = super(Bet, self)._parse_inputs(skip=('infile', 'outfile'))

        # Add infile and outfile to the args if they are specified
        if self.inputs.infile:
            allargs.insert(0, self.inputs.infile)
            if not self.inputs.outfile:
                # If the outfile is not specified but the infile is,
                # generate an outfile
                pth, fname = os.path.split(self.inputs['infile'])
                newpath=self.inputs.get('cwd', pth)
                self.inputs.outfile = fname_presuffix(fname, suffix='_bet',
                                                      newpath=newpath)
        if self.inputs.outfile:
            allargs.insert(1, self.inputs.outfile)
        return allargs
        
    def run(self, infile=None, outfile=None, **inputs):
        """Execute the command.

        Parameters
        ----------
        infile : string
            Filename to be skull stripped, can be passed as input
        outfile : string, optional
            Filename to save output to. If not specified, the `infile`
            filename will be used with a "_bet" suffix.
        inputs : dict
            Dictionary of any additional flags to send to bet.

        Returns
        -------
        results : Bunch
            A `Bunch` object with a copy of self in `interface`
            runtime : Bunch containing stdout, stderr, returncode, commandline
            
        """

        if infile:
            self.inputs.infile = infile
        if not self.inputs.infile:
            raise AttributeError('Bet requires an input file')
        if outfile:
            self.inputs.outfile = outfile
        self.inputs.update(**inputs)
        
        results = self._runner()
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs()

        return results        


    def outputs_help(self):
        """
        Optional Parameters
        -------------------
        (all default to None and are unset)
        
        outfile : /path/to/outfile
            path/name of skullstripped file
        maskfile : Bool
            binary brain mask if generated
        """
        print self.outputs_help.__doc__

    def aggregate_outputs(self):
        """Generate Bunch of all possible files generated by running interface
        some files are always generated, others depending on what "inputs" options are set
        
        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by interface object.
            If None, file was not generated
            Else, contains path, filename of generated outputfile
        """
        outputs = Bunch(outfile = None,
                        maskfile = None)
        if self.inputs.outfile:
            outfile = self.inputs.outfile
        else:
            pth,fname = os.path.split(self.inputs['infile'])
            outfile = os.path.join(self.inputs.get('cwd',pth),
                                   fname_presuffix(fname,suffix='_bet'))
        assert len(glob(outfile))==1, "Incorrect number or no output files %s generated"%outfile
        outputs.outfile = outfile
        maskfile = fname_presuffix(outfile,suffix='_mask')
        outputs.maskfile = glob(maskfile)
        if len(outputs.maskfile) > 0:
            outputs.maskfile = outputs.maskfile[0]
        else:
            outputs.maskfile = None
        return outputs


class Fast(FSLCommand):
    """Use FSL FAST for segmenting and bias correction.

    For complete details, see the `FAST Documentation. 
    <http://www.fmrib.ox.ac.uk/fsl/fast/index.html>`_

    To print out the command line help, use:
        Fast().inputs_help()

    Examples
    --------
    >>> fsl.Fast().inputs_help()
    >>> faster = fsl.Fast(out_basename = 'myfasted')
    >>> fasted = faster.run(['file1','file2'])

    >>> faster = fsl.Fast(infiles=['filea','fileb'], 
                          out_basename = 'myfasted')
    >>> fasted = faster.run()
    """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'fast'
  
    opt_map = {'number_classes':       '-n %d',
               'bias_iters':           '-I %d',
               'bias_lowpass':         '-l %d', # in mm
               'img_type':             '-t %d',
               'init_seg_smooth':      '-f %.3f',
               'segments':             '-g',
               'init_transform':       '-a %s',
               # This option is not really documented on the Fast web page:
               # http://www.fmrib.ox.ac.uk/fsl/fast4/index.html#fastcomm
               # I'm not sure if there are supposed to be exactly 3 args or what
               'other_priors':         '-A %s %s %s',
               'nopve':                '--nopve',
               'output_biasfield':     '-b',
               'output_biascorrected': '-B',
               'nobias':               '-N',
               'n_inputimages':        '-S %d',
               'out_basename':         '-o %s',
               'use_priors':           '-P', # must also set -a!
               'segment_iters':        '-W %d',
               'mixel_smooth':         '-R %.2f',
               'iters_afterbias':      '-O %d',
               'hyper':                '-H %.2f',
               'verbose':              '-v',
               'manualseg':            '-s %s',
               'probability_maps':     '-p'}

    def inputs_help(self):
        """Print command line documentation for FAST."""
        print get_doc(self.cmd, self.opt_map)

    def _populate_inputs(self):
        self.inputs = Bunch(infiles=None,
                            number_classes=None,
                            bias_iters=None,
                            bias_lowpass=None,
                            img_type=None,
                            init_seg_smooth=None,
                            segments=None,
                            init_transform=None,
                            other_priors=None,
                            nopve=None,
                            output_biasfield=None,
                            output_biascorrected=None,
                            nobias=None,
                            n_inputimages=None,
                            out_basename=None,
                            use_priors=None,
                            segment_iters=None,
                            mixel_smooth=None,
                            iters_afterbias=None,
                            hyper=None,
                            verbose=None,
                            manualseg=None,
                            probability_maps=None,
                            flags=None)


    def run(self, infiles=None, **inputs):
        """Execute the FSL fast command.

        Parameters
        ----------
        infiles : string or list of strings
            File(s) to be segmented or bias corrected
        inputs : dict
            Dictionary of any additional flags to send to fast
        
        Returns
        -------
        results : Bunch
            A `Bunch` object with a copy of self in `interface`
            runtime : Bunch containing stdout, stderr, returncode, commandline
            
        """

        if infiles:
            self.inputs.infiles = infiles
        if not self.inputs.infiles:
            raise AttributeError('Fast requires input file(s)')
        self.inputs.update(**inputs)
        
        results = self._runner()
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs()
            # NOT checking if files exist
            # Once implemented: results.outputs = self.aggregate_outputs()
            
        return results        

    def _parse_inputs(self):
        '''Call our super-method, then add our input files'''
        # Could do other checking above and beyond regular _parse_inputs here
        allargs = super(Fast, self)._parse_inputs(skip=('infiles'))
        if self.inputs.infiles:
            allargs.append(container_to_string(self.inputs.infiles))
        return allargs

    def aggregate_outputs(self):
        """Generate Bunch of all possible files generated by running interface
        some files are always generated, others depending on what "inputs" options are set
        
        Returns
        -------
        outputs : Bunch object
            (if multiple infiles, multiple outfiles of each)
            mixeltype : list filename(s)
            partial_volume_map : list  filenames [one for each input] 
            partial_volume_files : list filenames [one for each class, for each input]
            tissue_class_map : list filename(s) (each tissue has unique int value)
            tissue_class_files : list filenames  [one for each class, for each input]
            restored_image : list filename(s) (bias corrected image(s))
            bias_field : list filename(s) 
            probability_maps : list filenames [one for each class, for each input]

        Notes
        -----
        For each item in Bunch:
        If [] empty list, optional file was not generated
        Else, list contains path,filename of generated outputfile(s)
             Raises Exception if file is not found        
        """
        envext = fsloutputtype()[1]
        outputs = Bunch(mixeltype = [],
                        seg = [],
                        partial_volume_map=[],
                        partial_volume_files=[],
                        tissue_class_map=[],
                        tissue_class_files=[],
                        bias_corrected=[],
                        bias_field=[],
                        prob_maps=[])
        
        if not is_container(self.inputs.infiles):
            infiles = [self.inputs.infiles]
        else:
            infiles = self.inputs.infiles
        for item in infiles:
            # get basename (correct fsloutpputytpe extension)
            if self.inputs.out_basename:
                pth,nme = os.path.split(item)
                jnk,ext = os.path.splitext(nme)
                item = self.inputs.out_basename+'.%s'%(envext)
            else:
                nme,ext = os.path.splitext(item)
                item = nme+'.%s'%(envext)
            # get number of tissue classes
            if not self.inputs.number_classes:
                nclasses = 3
            else:
                nclasses = self.inputs.number_classes
                        
            # always seg, (plus mutiple?)
            outputs.seg.append(fname_presuffix(item,suffix='_seg'))
            if self.inputs.segments:
                for i in range(nclasses):
                    outputs.seg.append(fname_presuffix(item,suffix='_seg_%d'%(i)))
            # always pve,mixeltype unless nopve = True
            if not self.inputs.nopve:
                outputs.partial_volume_map.append(fname_presuffix(item,suffix='_pveseg'))
                outputs.mixeltype.append(fname_presuffix(item,suffix='_mixeltype'))
                for i in range(nclasses):
                    outputs.partial_volume_files.append(fname_presuffix(item, suffix='_pve_%d'%(i)))
            # biasfield ? 
            if self.inputs.output_biasfield:
                outputs.bias_field.append(fname_presuffix(item, suffix='_bias'))
            # restored image (bias corrected)?
            if self.inputs.output_biascorrected:
                outputs.biascorrected.append(fname_presuffix(item, suffix='_restore'))
            # probability maps ?
            if self.inputs.probability_maps:
                for i in range(nclasses):
                    outputs.prob_maps.append(fname_presuffix(item, suffix='_prob_%d'%(i)))

        # check files all were created
        for outtype, outlist in outputs.iteritems():
            if len(outlist) > 0:
                for outfile in outlist:
                    if not len(glob(outfile))==1:
                        raise IOError('outputfile %s of type %s not generated'%(outfile,outtype))
                
        return outputs
                    


class Flirt(FSLCommand):
    """Use FSL FLIRT for coregistration.
    
    For complete details, see the `FLIRT Documentation. 
    <http://www.fmrib.ox.ac.uk/fsl/flirt/index.html>`_

    To print out the command line help, use:
        Flirt().inputs_help()

    Examples
    --------
    
    >>> flirtter = fsl.Flirt(bins=640, searchcost='mutualinfo')
    >>> flirtted = flirtter.run(infile='involume.nii', 
    reference='reference.nii',
    outfile='moved.nii', 
    outmatrix='in_to_ref.mat')
    >>> flirtted_est = flirtter.run(infile='involume.nii', 
    reference='reference.nii',
    outfile=None
    outmatrix='in_to_ref.mat')
    >>> xfm_apply = flirtter.applyxfm(infile='involume.nii', 
    reference='reference.nii',
    inmatrix='in_to_ref.mat',
    outfile='moved.nii')
    
    >>> fls.Flirt().inputs_help()
    
    >>> flirter = fsl.Flirt(infile='subject.nii',
    reference='template.nii',
    outfile='moved_subject.nii',
    outmatrix='subject_to_template.mat')
    >>> flitrd = flirter.run()
    
    """
        
    @property
    def cmd(self):
        """sets base command, not editable"""
        return "flirt"

    opt_map = {'datatype':           '-datatype %d ',
               'cost':               '-cost %s',
               'searchcost':         '-searchcost %s',
               'usesqform':          '-usesqform',
               'displayinit':        '-displayinit',
               'anglerep':           '-anglerep %s',
               'interp':             '-interp',
               'sincwidth':          '-sincwidth %d',
               'sincwindow':         '-sincwindow %s',
               'bins':               '-bins %d',
               'dof':                '-dof %d',
               'noresample':         '-noresample',
               'forcescaling':       '-forcescaling',
               'minsampling':        '-minsamplig %f',
               'paddingsize':        '-paddingsize %d',
               'searchrx':           '-searchrx %d %d',
               'searchry':           '-searchry %d %d',
               'searchrz':           '-searchrz %d %d',
               'nosearch':           '-nosearch',
               'coarsesearch':       '-coarsesearch %d',
               'finesearch':         '-finesearch %d',
               'refweight':          '-refweight %s',
               'inweight':           '-inweight %s',
               'noclamp':            '-noclamp',
               'noresampblur':       '-noresampblur',
               'rigid2D':            '-2D',
               'verbose':            '-v %d',
               'flags':              '%s'}

    def inputs_help(self):
        """Print command line documentation for FLIRT."""
        print get_doc(self.cmd, self.opt_map)

    def _populate_inputs(self):
        self.inputs = Bunch(infile=None,
                            outfile=None,
                            reference=None,
                            outmatrix=None,
                            inmatrix=None,
                            datatype=None,
                            cost=None,
                            searchcost=None,
                            usesqform=None,
                            displayinit=None,
                            anglerep=None,
                            interp=None,
                            sincwidth=None,
                            sincwindow=None,
                            bins=None,
                            dof=None,
                            noresample=None,
                            forcescaling=None,
                            minsampling=None,
                            applyisoxfm=None,
                            paddingsize=None,
                            searchrx=None,
                            searchry=None,
                            searchrz=None,
                            nosearch=None,
                            coarsesearch=None,
                            finesearch=None,
                            refweight=None,
                            inweight=None,
                            noclamp=None,
                            noresampblur=None,
                            rigid2D=None,
                            verbose=None,
                            flags=None)
    def _parse_inputs(self):
        '''Call our super-method, then add our input files'''
        # Could do other checking above and beyond regular _parse_inputs here
        allargs = super(Flirt, self)._parse_inputs(skip=('infile', 
                                                         'outfile',
                                                         'reference', 
                                                         'outmatrix',
                                                         'inmatrix'))
        possibleinputs = [(self.inputs.outfile,'-out'),
                          (self.inputs.inmatrix, '-init'),
                          (self.inputs.outmatrix, '-omat'),
                          (self.inputs.reference, '-ref'),
                          (self.inputs.infile, '-in')]
        
        for val, flag in possibleinputs:
            if val:
                allargs.insert(0, '%s %s' % (flag, val))
        return allargs

    def run(self, infile=None, reference=None, outfile=None, outmatrix=None,
            **inputs):
        """Run the flirt command

        Parameters
        ----------
        infile : string
            Filename of volume to be moved.
        reference : string
            Filename of volume used as target for registration.
        outfile : string, optional
            Filename of the output, registered volume.  If not specified, only
            the transformation matrix will be calculated.
        outmatrix : string, optional
            Filename to output transformation matrix in asci format.
            If not specified, the output matrix will not be saved to a file.
        inputs : dict
            Dictionary of any additional flags to send to flirt.

        Returns
        -------
        results : Bunch
            A `Bunch` object with a copy of self in `interface`
            runtime : Bunch containing stdout, stderr, returncode, commandline
        
        Examples
        --------
        flirted = Flirt().run(infile, reference, outfile)
        flirted_estimate = Flirt().run(infile, reference, outfile=None, outmatrix=outmatrix)
        flirt_apply = Flirt().applyxfm(infile, reference, inmatrix, outfile)
            
        """

        if infile:
            self.inputs.infile = infile
        if not self.inputs.infile:
            raise AttributeError('Flirt requires an infile.')
        if reference:
            self.inputs.reference = reference
        if not self.inputs.reference:
            raise AttributeError('Flirt requires a reference file.')

        if outfile:
            self.inputs.outfile = outfile
        if outmatrix:
            self.inputs.outmatrix = outmatrix
        self.inputs.update(**inputs)
        
        results = self._runner()
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs()

        return results 
        

    def applyxfm(self, infile=None, reference=None, inmatrix=None, 
                 outfile=None, **inputs):
        """Run flirt and apply the transformation to the image.

          eg.
         flirt [options] -in <inputvol> -ref <refvol> -applyxfm -init
         <matrix> -out <outputvol>

        Parameters
        ----------
        infile : string
            Filename of volume to be moved.
        reference : string
            Filename of volume used as target for registration.
        inmatrix : string
            Filename for input transformation matrix, in asci format.
        outfile : string, optional
            Filename of the output, registered volume.  If not
            specified, only the transformation matrix will be
            calculated.
        inputs : dict
            Dictionary of any additional flags to send to flirt

        Returns
        -------
        results : Bunch
            A `Bunch` object with a copy of self in `interface`
            runtime : Bunch containing stdout, stderr, returncode, commandline

        Examples
        --------
        flirted = flirtter.applyxfm(infile=None, 
                                    reference=None, 
                                    inmatrix=None, 
                                    outfile=None)
        """

        if infile:
            self.inputs.infile = infile
        if not self.inputs.infile:
            raise AttributeError('Flirt requires an infile.')
        if reference:
            self.inputs.reference = reference
        if not self.inputs.reference:
            raise AttributeError('Flirt requires a reference file.')
        if inmatrix:
            self.inputs.inmatrix = inmatrix
        if not self.inputs.inmatrix:
            raise AttributeError('Flirt applyxfm requires an inmatrix')
        if outfile:
            self.inputs.outfile = outfile
        # If the inputs dict already has a set of flags, we want to
        # update it, not overwrite it.
        flags = inputs.get('flags', None)
        if flags is None:
            inputs['flags'] = '-applyxfm'
        else:
            inputs['flags'] = ' '.join([flags, '-applyxfm'])
        self.inputs.update(**inputs)
            
        results = self._runner()
        if results.runtime.returncode == 0:
            pass
            # run once implemented
            # results.outputs = self.aggregate_outputs()
            
        return results 


class McFlirt(FSLCommand):
    """Use FSL MCFLIRT to do within-modality motion correction.

    For complete details, see the `MCFLIRT Documentation. 
    <http://www.fmrib.ox.ac.uk/fsl/mcflirt/index.html>`_

    To print out the command line help, use:
        McFlirt().inputs_help()
    
    Examples
    --------
    
    >>> mcflirtter = fsl.McFlirt(infile='timeseries.nii',cost='mututalinfo')
    >>> mcflirtted = mcflirtter.run()

    """
    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'mcflirt'
    
    def inputs_help(self):
        """Print command line documentation for MCFLIRT."""
        print get_doc(self.cmd, self.opt_map)

    opt_map = {
        'outfile':     '-out %s',
        'cost':        '-cost %s',
        'bins':        '-bins %d',
        'dof':         '-dof %d',
        'refvol':      '-refvol %d',
        'scaling':     '-scaling %.2f',
        'smooth':      '-smooth %.2f',
        'rotation':    '-rotation %d',
        'verbose':     '-verbose',
        'stages':      '-stages %d',
        'init':        '-init %s',
        'usegradient': '-gdt',
        'usecontour':  '-edge',
        'meanvol':     '-meanvol',
        'statsimgs':   '-stats',
        'savemats':    '-mats',
        'saveplots':   '-plots',
        'report':      '-report'}

    def _populate_inputs(self):
        self.inputs = Bunch(infile=None,
                            outfile=None,
                            cost=None,
                            bins=None,
                            dof=None,
                            refvol=None,
                            scaling=None,
                            smooth=None,
                            rotation=None,
                            verbose=None,
                            stages=None,
                            init=None,
                            usegradient=None,
                            usecontour=None,
                            meanvol=None,
                            statsimgs=None,
                            savemats=None,
                            saveplots=None,
                            report=None)
        
    def _parse_inputs(self):
        """Call our super-method, then add our input files"""
        allargs = super(McFlirt, self)._parse_inputs(skip=('infile'))
        if self.inputs.infile:
            allargs.insert(0,'-in %s'%(self.inputs.infile))
        return allargs

    def run(self, infile=None, **inputs):
        """Runs mcflirt
        
        Parameters
        ----------
        infile : string
            Filename of volume to be aligned
        inputs : dict
            Dictionary of any additional flags to send to mcflirt

        Returns
        -------
        results : Bunch
            A `Bunch` object with a copy of self in `interface`
            runtime : Bunch containing stdout, stderr, returncode, commandline

        Examples
        --------
        >>> mcflrt = fsl.McFlirt(cost='mutualinfo')
        >>> mcflrtd = mcflrt.run(infile='timeseries.nii')

        """
        if infile:
            self.inputs.infile = infile
        if not self.inputs.infile:
            raise AttributeError('McFlirt requires an infile.')

        self.inputs.update(**inputs)
        results = self._runner()
        if results.runtime.returncode == 0:
            pass
            # Uncomment once implemented
            # results.outputs = self.aggregate_outputs()
        return results 


class Fnirt(FSLCommand):
    """Use FSL FNIRT for non-linear registration.
    
    For complete details, see the `FNIRT Documentation.
    <http://www.fmrib.ox.ac.uk/fsl/fnirt/index.html>`_

    To print out the command line help, use:
        Fnirt().inputs_help()

    Examples
    --------
    >>> fnirter = fsl.Fnirt(affine='affine.mat')
    >>> fnirted = fnirter.run(reference='ref.nii',infile='anat.nii')
    >>> fsl.Fnirt().inputs_help()
    
    
    """
    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'fnirt'
    
    def inputs_help(self):
        """Print command line documentation for FNIRT."""
        print get_doc(self.cmd, self.opt_map)

    def _populate_inputs(self):
        self.inputs = Bunch(infile=None,
                          reference=None,
                          affine=None,
                          initwarp= None,
                          initintensity=None,
                          configfile=None,
                          referencemask=None,
                          imagemask=None,
                          fieldcoeff_file=None,
                          outimage=None,
                          fieldfile=None,
                          jacobianfile=None,
                          reffile=None,
                          intensityfile=None,
                          logfile=None,
                          verbose=None,
                          sub_sampling=None,
                          max_iter=None,
                          referencefwhm=None,
                          imgfwhm=None,
                          lambdas=None,
                          estintensity=None,
                          applyrefmask=None,
                          applyimgmask=None)

    opt_map = {
        'affine':           '--aff %s',
        'initwarp':         '--inwarp %s',
        'initintensity':    '--intin %s',
        'configfile':       '--config %s',
        'referencemask':    '--refmask %s',
        'imagemask':        '--inmask %s',
        'fieldcoeff_file':  '--cout %s',
        'outimage':         '--iout %s',
        'fieldfile':        '--fout %s',
        'jacobianfile':     '--jout %s',
        'reffile':          '--refout %s',
        'intensityfile':    '--intout %s',
        'logfile':          '--logout %s',
        'verbose':          '--verbose',
        'sub_sampling':     '--subsample %d',
        'max_iter':         '--miter %f',
        'referencefwhm':    '--reffwhm %f',
        'imgfwhm':          '--infwhm %f',
        'lambdas':          '--lambda %f',
        'estintensity':     '--estint %f',
        'applyrefmask':     '--applyrefmask %f',
        'applyimgmask':     '--applyinmask %f',
        'flags':            '%s'}

    @property
    def cmdline(self):
        """validates fsl options and generates command line argument"""
        self.update_optmap()
        allargs = self._parse_inputs()
        allargs.insert(0, self.cmd)
        return ' '.join(allargs)
            
  
    def run(self, infile=None, reference=None, **inputs):
        """Run the fnirt command
  
        Parameters
        ----------
        infile : string
            Filename of the volume to be warped/moved.
        reference : string
            Filename of volume used as target for warp registration.
        inputs : dict
            Dictionary of any additional flags to send to fnirt.

        Returns
        --------
        results : Bunch
            A `Bunch` object with a copy of self in `interface`
            runtime : Bunch containing stdout, stderr, returncode, commandline

        Examples
        --------
        >>> #T1-> MNI153
        >>> fnirt_mprage = fsl.Fnirt(imgfwhm=[8,4,2],sub_sampling=[4,2,1],
                                     warp_resolution=[6,6,6])
        >>> fnirted_mprage = fnirt_mprage.run(infile='jnkT1.nii', reference='refimg.nii')

        """
        if infile:
            self.inputs.infile = infile
        if not self.inputs.infile:
            raise AttributeError('Fnirt requires an infile.')
        if reference:
            self.inputs.reference = reference
        if not self.inputs.reference:
            raise AttributeError('Fnirt requires a reference file.')
        self.inputs.update(**inputs)
                                   
        results = self._runner()
        if results.runtime.returncode == 0:
            pass
            # Uncomment once implemented
            # results.outputs = self.aggregate_outputs()
            
        return results 

    def update_optmap(self):
        """Updates opt_map for inout items with variable values
        """
        itemstoupdate = ['sub_sampling',
                         'max_iter',
                         'referencefwhm',
                         'imgfwhm',
                         'lambdas',
                         'estintensity',
                         'applyrefmask',
                         'applyimgmask']
        for item in itemstoupdate:
            if self.inputs.get(item):
                opt = self.opt_map[item].split()
                values = self.inputs.get(item)
                try:
                    valstr = opt[0] + ' %s'%(opt[1])* len(values)
                except TypeError:
                    # TypeError is raised if values is not a list
                    valstr = opt[0] + ' %s'%(opt[1])
                self.opt_map[item] = valstr
   
    def _parse_inputs(self):
        '''Call our super-method, then add our input files'''
        # Could do other checking above and beyond regular _parse_inputs here
        allargs = super(Fnirt, self)._parse_inputs(skip=('infile', 'reference'))
        
        possibleinputs = [(self.inputs.reference,'--ref='),
                          (self.inputs.infile, '--in=')]
        
        for val, flag in possibleinputs:
            if val:
                allargs.insert(0,'%s%s'%(flag, val))
        
        return allargs

    def write_config(self,configfile):
        """Writes out currently set options to specified config file
        
        Parameters
        ----------
        configfile : /path/to/configfile
        """
        self.update_optmap()
        valid_inputs = self._parse_inputs() 
        try:
            fid = open(configfile, 'w+')
        except IOError:
            print ('unable to create config_file %s'%(configfile))
            
        for item in valid_inputs:
            fid.write('%s\n'%(item))
        fid.close()




class FSFmaker:
    '''Use the template variables above to construct fsf files for feat.
    
    This doesn't actually run anything.
    
    Examples
    --------
    FSFmaker(5, ['left', 'right', 'both'])
        
    '''
    # These are still somewhat specific to my experiment, but should be so in an
    # obvious way.  Contrasts in particular need to be addressed more generally.
    # These should perhaps be redone with a setattr_on_read property, though we
    # don't want to reload for each instance separately.
    fsf_header = load_template('feat_header.tcl')
    fsf_ev = load_template('feat_ev.tcl')
    fsf_ev_ortho = load_template('feat_ev_ortho.tcl')
    fsf_contrasts = load_template('feat_contrasts.tcl')

    def __init__(self, num_scans, cond_names):
        subj_dir = dirname(getcwd())
        # This is more package general, and should happen at a higher level
        fsl_root = getenv('FSLDIR')
        for i in range(num_scans):
            fsf_txt = self.fsf_header.substitute(num_evs=len(cond_names), 
                                                 base_dir=subj_dir, scan_num=i,
                                                 fsl_root=fsl_root)
            for j, cond in enumerate(cond_names):
                fsf_txt += self.gen_ev(i, j+1, cond, subj_dir, len(cond_names))
            fsf_txt += self.fsf_contrasts.substitute()

            f = open('scan%d.fsf' % i, 'w')
            f.write(fsf_txt)
            f.close()
                
                
    def gen_ev(self, scan, cond_num, cond_name, subj_dir, total_conds):
        args = (cond_num, cond_name) + (cond_num,) * 6 + \
                (scan, cond_name) + (cond_num, ) * 2

        ev_txt = self.fsf_ev.substitute(ev_num=cond_num, ev_name=cond_name,
                                        scan_num=scan, base_dir=subj_dir)

        for i in range(total_conds + 1):
            ev_txt += self.fsf_ev_ortho.substitute(c0=cond_num, c1=i) 

        return ev_txt


##################################################################################


    
    
#def bet(*args, **kwargs):
#   bet_element = BetElement(*args, **kwargs)
    
    # We should check the return value
#    bet_element.execute()

#    return load_image(bet_element.state['output'])

#def flirt(target, moving, space=None, output_filename=None, **kwargs):
"""Call flirt to register moving to target with optional space to define 
    space new image is resliced into

    Parameters
    ----------

    target : nipy image
        Image to register other image(s) to
    moving : nipy image
        Image being moved/registered to target
    space : nipy image or coordinate_map
        image or coordinate map defining space to reslice image into
    outputfilename  : filename
        optional filename to use when creating registered image

    Returns
    -------

    movedimage : nipy image
        Image coregistered to target

    transform : numpy array
        A 4 X 4 array os the transform from moving to target

    Other Parameters
    ----------------
    xform_only : True
        Only computes the transform and only returns transform
"""
#    target_filename = target.filename

    
def apply_transform(target, moving, transform, space=None, output_filename=None):
    """
    While this also uses flirt, it is a quite different usage, and as such gets
    it's own function.
    """
    pass
