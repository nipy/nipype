"""
The fsl module provides basic functions for interfacing with fsl to access fsl tools

these functions include 
    
    BET: brain extraction

    FAST: segmentation and bias correction

    FLIRT: linear registration

    FNIRT: non-linear warp

Examples
--------
See documentation for bet, fast and flirt functions for 'working' examples.


filename vs nipy image:
I am wondering about a fancy decorator which would preprocess certain arguments
to make sure they are nipy images, but would then allow filenames or file
objects as well.  I would like to guarantee that we get a nipy object, as it
makes it more flexible for us to assume things in the future. -DJC

Im thinking we will do the not-cool thing to start with and deal with files, 
give an example on how to then access as nipy object (maybe add helper function to base.py)
And then consider the fancy decorator
"""

from nipype.interfaces.base import Bunch, CommandLine, setattr_on_read
import os



import subprocess
import string
from string import Template

def fslversion():
    """Check for fsl version on system

    Parameters
    ----------
    None

    Returns
    -------
    version : string
       version number as string 
       or None if FSL not found

    """
    # find which fsl being used....and get version from /path/to/fsl/etc/fslversion
    clout = CommandLine('which fsl').run()

    if clout.output['returncode'] is not 0:
        # fsl not found
        return None
    out = clout.output['out']
    basedir = os.path.split(os.path.split(out)[0])[0]
    clout = CommandLine('less %s/etc/fslversion'%(basedir)).run()
    out = clout.output['out']
    return out.strip('\n')

def fsloutputtype(ftype=None):
    """Check and or set the global FSL output file type FSLOUTPUTTYPE
    
    Parameters
    ----------
    ftype :  string
        Represents the file type to set
        based on string of valid FSL file types
        ftype == None to get current setting/ options

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
        for key in ftypes.keys():
            print '%s = \"%s\"'%(key, ftypes[key])

    else:
        # set environment setting
        fsl_ftype = ftype
        os.environ['FSLOUTPUTTYPE'] = fsl_ftype
    
    print 'FSLOUTPUTTYPE = %s (\"%s\")'%(fsl_ftype, ftypes[fsl_ftype])
    return fsl_ftype,ftypes[fsl_ftype]
        

class Bet(CommandLine):

    _cmd = None
    @property
    def cmd(self):
        """sets base command, not editable"""
        if self._cmd is None:
            self._cmd = 'bet'
        return self._cmd

    def __init__(self, **opts):
        """use fsl bet for skull stripping

        Options
        -------

        To see optianl arguments
        Bet().opts_help()


        Examples
        --------
        >>> fsl.Bet().opts_help()
        >>> better = fsl.Bet(frac=0.5)
        >>> betted = better.run('infile', 'outfile')
        >>> better2 = better.update(frac=0.3)

        >>> btr = fsl.Bet(infile='infile', outfile='outfile', frac=0.5)
        >>> btd = btr.run()
        """
        
        super(Bet,self).__init__()
        self.args = []
        self._populate_opts()
        self.opts.update(**opts)
        self.cmdline = ''
        self.infile = ''
        self.outfile = ''
        
        
    def opts_help(self):
        doc = """
        Optional Parameters
        -------------------
        (all default to None and are unset)
        
        infile : /path/to/file
            file to skull strip 
            --can be set as argument at .run(infile)
        outfile : /path/to/outfile
            path/name of skullstripped file
            --can be set as argument at .run(infile,outfile)
        outline : Bool
	    generate brain surface outline overlaid onto original image
	mask : Bool
	    generate binary brain mask
	skull : Bool	
            generate approximate skull image
	nooutput : Bool	
            don't generate segmented brain image output
	frac : float
	    fractional intensity threshold (0->1); fsldefault=0.5; 
            smaller values give larger brain outline estimates
	vertical_gradient : float		
            vertical gradient in fractional intensity threshold (-1->1); fsldefault=0
            positive values give larger brain outline at bottom, smaller at top
	radius : float	
            head radius (mm not voxels); initial surface sphere is set to half of this
	center : list of ints [x,y,z]
            centre-of-gravity (voxels not mm) of initial mesh surface.
	threshold : Bool	
            apply thresholding to segmented brain image and mask
	mesh : Bool	
            generates brain surface as mesh in vtk format
	verbose : Bool	
            switch on diagnostic messages
	
        flags = unsupported flags, use at your own risk  ['-R']

        """
        print doc

    def _populate_opts(self):
        self.opts = Bunch(infile=None,
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

    def _validate(self):
        """validate fsl bet options
        if set to None ignore
        """
        out_opts = []
        opts = {}
        [opts.update({k:v}) for k, v in self.opts.iteritems() if v is not None ]
        for opt in opts:
            if opt is 'infile':
                continue
            if opt is 'outfile':
                continue
            if opt is 'frac':
                val = float(opts['frac'])
                out_opts.extend(['-f','%.2f'%(val)])
                continue
            if opt is 'center':
                val = [float(x) for x in opts['center']]
                if len(val) is not 3:
                    raise ValueError('three values required for center option')
                out_opts.extend(['-c' , '%s %s %s'%(val[0],val[1],val[2])])
                continue
            if opt is 'vertical_gradient':
                val = float(opts['vertical_gradient'])
                out_opts.extend(['-g','%.2f'%(val)])
                continue
            if opt is 'outline':
                if opts[opt]:
                    out_opts.extend(['--outline'])
                continue
            if opt is 'mask':
                if opts[opt]:
                    out_opts.extend(['--mask'])
                continue
            if opt is 'skull':
                if opts[opt]:
                    out_opts.extend(['--skull'])
                continue
            if opt is 'nooutput':
                if opts[opt]:
                    out_opts.extend(['--nooutput'])
                continue
            if opt is 'radius':
                val = float(opts[opt])
                out_opts.extend(['--radius %f'%(val)])
            if opt is 'threshold':
                if opts[opt]:
                    out_opts.extend(['--threshold'])
                continue
            if opt is 'mesh':
                if opts[opt]:
                    out_opts.extend(['--mesh'])
                continue
            if opt is 'verbose':
                if opts[opt]:
                    out_opts.extend(['--verbose'])
                continue
            if opt is 'flags':
                out_opts.extend(opts[opt])
                continue
            print 'option %s not supported'%(opt)
        
        return out_opts

    def run(self, infile=None, outfile=None):
        """ runs bet command

        Parameters 
        ----------
        (these can also be set as options)

        infile : filename
            file to skull strip 
            (default = None)
        outfile : filename
            filename for skull-stripped image 
            (default = None)

        Options
        -------
        see Bet().opts_help()
        
        Returns
        --------
        bet : object

        """
        if infile is None:
            if self.opts.infile is None:
                raise ValueError('infile not a valid file')
            else:
                infile = self.opts.infile
        if outfile is None:
            if self.opts.outfile is None:
                raise ValueError('outfile not a valid file')
            else:
                outfile =self.opts.outfile
        
        newbet = self.update(infile=infile, outfile=outfile)
        
        newbet.args = [infile, outfile]
        cmd = newbet._compile_command()
        
        newbet.cmdline = cmd
        newbet.infile = infile
        newbet.outfile = outfile
        (retcode, out, err) = newbet._runner(newbet.cmdline)
        newbet.retcode = retcode
        newbet.out = out
        newbet.err = err
        
        return newbet

    def _compile_command(self):
        """validates fsl options and generates command line argument"""
        valid_opts = self._validate()
        allargs =  [self.cmd] + self.args + valid_opts
        return ' '.join(allargs)

    def update(self, **opts):
        newbet = Bet()
        [newbet.opts.__setattr__(k,v) for k, v in self.opts.iteritems() if v is not None ]
        newbet.opts.update(**opts)
        return newbet
        

class Fast(CommandLine):

    _cmd = None
    @property
    def cmd(self):
        """sets base command"""
        if self._cmd is None:
            self._cmd = 'fast'
        return self._cmd

    def __init__(self, **opts):
        """use fsl fast for segmenting, bias correction

        Options
        -------
        see  
        fsl.Fast().opts_help()
        
        Example
        -------
        >>> faster = fsl.Fast(out_basename = 'myfasted')
        >>> fasted = faster.run(['file1','file2'])
        >>> fsl.Fast().opts_help()

        >>> faster = fsl.Fast(infiles=['filea','fileb'], 
                              out_basename = 'myfasted')
        >>> fasted = faster.run()
        """
        
        super(Fast,self).__init__()
        self.args = []
        self._populate_opts()
        self.opts.update(**opts)
        self.cmdline = ''
        self.infiles = []

    def opts_help(self):
        doc = """
        POSSIBLE OPTIONS
        -----------------
        (all default to None and are unset)
        infiles : list
            files to run on ['/path/to/afile', /path/to/anotherfile']
            can be set at runtime  .run(['/path/to/filea', 'fileb'])
        number_classes : int
            number of tissue-type classes, (default=3)
        bias_iters : int
            number of main-loop iterations during bias-field removal (default=4)
        bias_lowpass : int
            bias field smoothing extent (FWHM) in mm (default=20)
        img_type : int
            type of image 1=T1, 2=T2, 3=PD; (default=T1)
        init_seg_smooth : float
            initial segmentation spatial smoothness (during bias field estimation); default=0.02
        segments : Boolean
            outputs a separate binary image for each tissue type
        init_transform : string filename
            initialise using priors; you must supply a FLIRT transform <standard2input.mat>
        other_priors : list of strings (filenames)
            <prior1> <prior2> <prior3>    alternative prior images
        nopve :Boolean
            turn off PVE (partial volume estimation)
        output_biasfield : Boolean
            output estimated bias field
        output_biascorrected : Boolean
            output bias-corrected image
        nobias : Boolean
            do not remove bias field
        n_inputimages : int
            number of input images (channels); (default 1)
        out_basename: string <filename>
            output basename for output images
        use_priors : Boolean
            use priors throughout; you must also set the init_transform option
        segment_iters : int
            number of segmentation-initialisation iterations; (default=15)
        mixel_smooth : float
            spatial smoothness for mixeltype; (default=0.3)
        iters_afterbias : int
            number of main-loop iterations after bias-field removal; (default=4)
        hyper : float
            segmentation spatial smoothness; (default=0.1)
        verbose : Boolean
            switch on diagnostic messages
        manualseg : string <filename>
            Filename containing intensities
        probability_maps : Boolean
            outputs individual probability maps

        flags = unsupported flags, use at your own risk  ['-R']
        """
        print doc

    def _populate_opts(self):
        self.opts = Bunch(infiles=None,
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

    def _validate(self):
        """validate fsl bet options
        if set to None ignore
        """
        out_opts = []
        opts = {}
        [opts.update({k:v}) for k, v in self.opts.iteritems() if v is not None ]
        for opt in opts:
            if opt is 'infiles':
                continue
            if opt is 'number_classes':
                val = int(opts['number_classes'])
                out_opts.extend(['--class %d '%(val)])
                continue
            if opt is 'bias_iters':
                val = int(opts['bias_iters'])
                out_opts.extend(['--iter %d'%(val)])
                continue
            if opt is 'bias_lowpass':
                val = int(opts['bias_lowpass'])
                out_opts.extend(['--lowpass %d'%(val)])
                continue
            if opt is 'img_type':
                val = int(opts['img_type'])
                out_opts.extend(['--type %d'%(val)])
                continue
            if opt is 'init_seg_smooth':
                val = float(opts['init_seg_smooth'])
                out_opts.extend(['--fHard %f'%(val)])
                continue
            if opt is 'segments':
                if opts['segments']:
                    out_opts.extend(['--segments'])
                continue
            if opt is 'init_transform':
                out_opts.extend(['-a %s'%(opts['init_transform'])])
                continue
            if opt is 'other_priors':
                imgs = opts['other_priors']
                out_opts.extend(['-A %s %s %s'%(imgs[0], imgs[1], imgs[2])])
                continue
            if opt is 'nopve':
                if opts['nopve']:
                    out_opts.extend(['--nopve'])
                continue
            if opt is 'output_biasfield':
                if opts['output_biasfield']:
                     out_opts.extend(['-b'])
                continue
            if opt is 'output_biascorrected':
                if opts['output_biascorrected']:
                    out_opts.extend(['-B'])
                continue
            if opt is 'nobias':
                if opts['nobias']:
                    out_opts.extend(['--nobias'])
                continue
            if opt is 'n_inputimages':
                val = int(opts['n_inputimages'])
                out_opts.extend(['--channels %d'%(val)])
                continue
            if opt is 'out_basename':
                out_opts.extend(['--out %s'%(opts['out_basename'])])
                continue
            if opt is 'use_priors':
                if opts['use_priors']:
                     out_opts.extend(['--Prior'])
                continue
            if opt is 'segment_iters':
                val = int(opts['segment_iters'])
                out_opts.extend(['--init %d'%(val)])
                continue
            if opt is 'mixel_smooth':
                 val = float(opts['mixel_smooth'])
                 out_opts.extend(['--mixel %f'%(val)])
                 continue
            if opt is 'iters_afterbias':
                 val = int(opts['iters_afterbias'])
                 out_opts.extend(['--fixed %d'%(val)])
                 continue
            if opt is 'hyper':
                val = float(opts['hyper'])
                out_opts.extend(['--Hyper %f'%(val)])
                continue
            if opt is 'verbose':
                if opts['verbose']:
                    out_opts.extend(['--verbose'])
                continue
            if opt is 'manualseg':
                out_opts.extend(['--manualseg %s'%(opts['manualseg'])])
                continue
            if opt is 'probability_maps':
                if opts['probability_maps']:
                    out_opts.extend(['-p'])
                continue
            if opt is 'flags':
                out_opts.extend(opts['flags'])
                continue
                               
            print 'option %s not supported'%(opt)
        
        return out_opts

    def _compile_command(self):
        """validates fsl options and generates command line argument"""
        valid_opts = self._validate()
        allargs = [self.cmd] + self.args + valid_opts
        return ' '.join(allargs)
  
    def run(self, infiles=None):
        """ runs fast command

        Parameters
        ----------
        infiles : filename(s)
            file(s) to segment/ bias-correct

        Returns
        --------
        fast : object
            return new fast object with updated fields
        """
        #newfast = self.update()
        if infiles is None:
            if self.opts.infiles is None:
                raise ValueError('infiles not specified')
            else:
                infiles = self.opts.infiles
        
        if type(infiles) is not list:
            infiles = [infiles]
        
        newfast = self.update(infiles = infiles)

        if len(infiles) > 1:
            newfast.args.extend([k for k in infiles])
        else:
            newfast.args.extend(infiles) 
            
        cmd = newfast._compile_command()
        
        newfast.cmdline = cmd
        newfast.infiles = list(infiles)
        (retcode, out, err) = newfast._runner(newfast.cmdline)
        newfast.retcode = retcode
        newfast.out = out
        newfast.err = err
        
        return newfast

    def update(self, **opts):
        newfast = Fast()
        [newfast.opts.__setattr__(k,v) for k, v in self.opts.iteritems() if v is not None ]
        newfast.opts.update(**opts)
        return newfast
  

class Flirt(CommandLine):

    _cmd = None
    @property
    def cmd(self):
        """sets base command, not editable"""
        if self._cmd is None:
            self._cmd = 'flirt'
        return self._cmd

    def __init__(self, **opts):
        """use fsl flirt for coregistration

        Options
        -------
        fsl.Flirt().opts_help()

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

        >>> fls.Flirt().opts_help()


        >>> flirter = fsl.Flirt(infile='subject.nii',
                                reference='template.nii',
                                outfile='moved_subject.nii',
                                outmatrix='subject_to_template.mat')
        >>> flitrd = flirter.run()

                          
        """
        
        super(Flirt,self).__init__()
        self.args = []
        self._populate_opts()
        self.opts.update(**opts)
        self.cmdline = ''
        self.infile = ''
        self.outfile = ''
        self.reference = ''
        self.outmatrix = ''
        self.inmatrix = ''
        
        
    def opts_help(self):
        doc = """

        POSSIBLE OPTIONS
        -----------------
        (all default to None and are unset)
        infile : /path/to/file
            file to be moved/registered into space of
            reference image
        outfile : /path/to/newfilename
            file to save the moved/registered image
        reference : /path/to/reference_image
            file of reference image
        outmatrix : /path/to/matrixfile.mat
            file that holds transform mapping infile to reference
        datatype : string {'char','short','int','float','double'}
            (force output data type)
        cost : string {'mutualinfo','corratio','normcorr','normmi','leastsq','labeldiff'}  
            (fsldefault is corratio)
        searchcost : string 
            {'mutualinfo','corratio','normcorr','normmi','leastsq','labeldiff'}  
            (FSL default = 'corratio')
        usesqform : Bool
            (initialise using appropriate sform or qform)
        displayinit : Bool
            (display initial matrix)
        anglerep :string {'quaternion','euler'}       
            (fsldefault is euler)
        interp : string  {'trilinear','nearestneighbour','sinc'}  
            (final interpolation: fsldefault = trilinear)
        sincwidth : int
            full-width in voxels  (fsldefault is 7)
        sincwindow : string {'rectangular','hanning','blackman'}
            function on the data in the sinc window
        bins : int 
            number of histogram bins   (fsldefault is 256)
        dof : int
            number of transform dofs (degrees of freedom)(fsldefault is 12)
        noresample : Bool                        
            (do not change input sampling)
        forcescaling : Bool                      
            (force rescaling even for low-res images)
        minsampling : float
            vox_dim (set minimum voxel dimension for sampling (in mm))
        applyisoxfm : float <scale>               
            used with applyxfm only! but forces isotropic resampling)
        paddingsize : int 
            number of voxels (for applyxfm: interpolates outside image by size)
        searchrx : list of ints [-90,90]
            [<min_angle> <max_angle>]  (angles in degrees: fsldefault is -90 90)
        searchry : list of ints [-90, 90]
            [<min_angle> <max_angle>]  (angles in degrees: default is -90 90)
        searchrz : list of ints [-90,90]
            [<min_angle> <max_angle>]  (angles in degrees: default is -90 90)
        nosearch : Bool
            (sets all angular search ranges to 0 0)
        coarsesearch : int <delta_angle>        
            (angle in degrees: fsldefault is 60)
        finesearch : int <delta_angle>          
            (angle in degrees: default is 18)
        refweight : string  <volume filename>                
            (use weights for reference volume)
        inweight : string <volume filename>                 
            (use weights for input volume)
        noclamp : Bool
            (do not use intensity clamping)
        noresampblur : Bool
            (do not use blurring on downsampling)
        rigid2D : Bool
            (use 2D rigid body mode - ignores dof)
        verbose : int <num>
            controls amount of output (0 is least and is fsldefault)
        
        flags : list 
            unsupported flags, use at your own risk!!  
            flags = ['-i']

        """
        print doc
    def _populate_opts(self):
        self.opts = Bunch(infile=None,
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

    def _validate(self):
        """validate fsl bet options
        if set to None ignore
        """
        out_opts = []
        opts = {}
        [opts.update({k:v}) for k, v in self.opts.iteritems() if v is not None ]
        for opt in opts:
            if opt in ['infile', 'outfile', 'reference', 'outmatrix','inmatrix']:
                continue
            if opt is 'datatype':
                val = opts['datatype']
                out_opts.extend(['-datatype %s'%(val)])
                continue
            if opt is 'cost':
                val = opts['cost']
                out_opts.extend(['-cost %s'%(val)])
                continue
            if opt is 'searchcost':
                val = opts['searchcost']
                out_opts.extend(['-searchcost %s'%(val)])
                continue
            if opt is 'usesqform':
                if opts[opt]:
                    out_opts.extend(['-usesqform'])
                continue
            if opt is 'displayinit':
                if opts[opt]:
                    out_opts.extend(['-displayinit'])
                continue
            if opt is 'anglerep':
                val = opts[opt]
                out_opts.extend(['-anglerep %s'%(val)])
                continue
            if opt is 'interp':
                val = opts[opt]
                out_opts.extend(['-interp'])
                continue
            if opt is 'sincwidth':
                val = int(opts[opt])
                out_opts.extend(['-sincwidth %d'%(val)])
                continue                    
            if opt is 'sincwindow':
                val = opts[opt]
                out_opts.extend(['-sincwindow %s'%(val)])
                continue
            if opt is 'bins':
                val = int(opts[opt])
                out_opts.extend(['-bins %d'%(val)])
                continue
            if opt is 'dof':
                val = int(opts[opt])
                out_opts.extend(['-dof %d'%(val)])
                continue
            if opt is 'noresample':
                if opts[opt]:
                    out_opts.extend(['-noresample'])
                continue
            if opt is 'forcescaling':
                if opts[opt]:
                    out_opts.extend(['-forcescaling'])
                continue
            if opt is 'minsampling':
                val = float(opts[opt])
                out_opts.extend(['-minsampling %f'%(val)])
                continue
            if opt is 'paddingsize':
                val = int(opts[opt])
                out_opts.extend(['-padingsize %d'%(val)])
                continue
            if opt is 'searchrx':
                val = opts[opt]
                out_opts.extend(['-searchrx %d %d'%(val[0], val[1])])
                continue
            if opt is 'searchry':
                val = opts[opt]
                out_opts.extend(['-searchry %d %d'%(val[0], val[1])])
                continue                    
            if opt is 'searchrz':
                val = opts[opt]
                out_opts.extend(['-searchrz %d %d'%(val[0], val[1])])
                continue
            if opt is 'nosearch':
                if opts[opt]:
                    out_opts.extend(['-nosearch'])
                continue
            if opt is 'coarsesearch':
                val = int(opts[opt])
                out_opts.extend(['-coarsesearch %d'%(val)])
                continue                   
            if opt is 'finesearch':
                val = int(opts[opt])
                out_opts.extend(['-finesearch %d'%(val)])
                continue   
            if opt is 'refweight':
                val = opts[opt]
                out_opts.extend(['-refweight %s'%(val)])
                continue                     
            if opt is 'inweight':
                val = opts[opt]
                out_opts.extend(['-refweight %s'%(val)])
                continue     
            if opt is 'noclamp':
                if opts[opt]:
                    out_opts.extend(['-noclamp'])
                continue     
            if opt is 'noresampblur':
                if opts[opt]:
                    out_opts.extend(['-noresampblur'])
                continue     
            if opt is 'rigid2D':
                if opts[opt]:
                    out_opts.extend(['-2D'])
                continue
            if opt is 'verbose':
                val = int(opts[opt])
                out_opts.extend(['-v %d'%(val)])
                continue
            if opt is 'flags':
                out_opts.extend(opts[opt])
                continue 
            print 'option %s not supported'%(opt)
        return out_opts

    def _compile_command(self):
        """validates fsl options and generates command line argument"""
        valid_opts = self._validate()
        allargs = self.args + valid_opts
        return ' '.join(allargs)
  
    def run(self, infile=None, reference=None, outfile=None, outmatrix=None):
        """ runs flirt command
         

        Parameters
        ----------
        infile : filename
            filename of volume to be moved
        reference : filename
            filename of volume used as target for registration
        outfile : filename
            filename of new volume of infile moved to space of reference
            if None,  only the transformation matrix will be calculated
        outmatrix : filename  q
            filename holding transformation matrix in asci format
            if None, the output matrix will not be saved to a file

        Returns
        --------
        flirt : object
            return new flirt object with updated fields

        Examples
        --------
        flirted = Flirt().run(infile, reference, outfile)
        flirted_estimate = Flirt().run(infile, reference, outfile=None, outmatrix=outmatrix)
        flirt_apply = Flirt().applyxfm(infile, reference, inmatrix, outfile)
            
        
        """
        #newflirt = self.update()
        if infile is None:
            if self.opts.infile is None:
                raise ValueError('infile is not specified')
            else:
                infile = self.opts.infile
        if reference is None:
            if self.opts.reference is None:
                raise ValueError('reference is not specified')
            else:
                reference = self.opts.reference
        if outfile is None:
            outfile = self.opts.outfile
        if outmatrix is None:
            outmatrix = self.opts.outmatrix
        newflirt = self.update(infile=infile, 
                               reference=reference,
                               outfile=outfile,
                               outmatrix = outmatrix)
        #newflirt.args =  [newflirt.cmd]
        newflirt.args.extend(['-in %s'%(newflirt.opts.infile)])
        newflirt.infile = infile
        newflirt.args.extend(['-ref %s'%(newflirt.opts.reference)])
        newflirt.reference = reference
        if newflirt.opts.outfile:
            newflirt.args.extend(['-out %s'%(newflirt.opts.outfile)])
            newflirt.outfile = outfile
        if newflirt.opts.outmatrix:
            newflirt.args.extend(['-omat %s'%(newflirt.opts.outmatrix)])
            newflirt.outmatrix = outmatrix
        
            
        cmd = newflirt._compile_command()
        
        newflirt.cmdline = cmd
        
        (retcode, out, err) = newflirt._runner(newflirt.cmdline)
        newflirt.retcode = retcode
        newflirt.out = out
        newflirt.err = err
        
        return newflirt

    def applyxfm(self, infile=None, reference=None, inmatrix=None, outfile=None):
        """ runs flirt command 
          eg.
          flirted = flirtter.applyxfm(self, infile=None, reference=None, inmatrix=None, outfile=None)
          flirt [options] -in <inputvol> -ref <refvol> -applyxfm -init <matrix> -out <outputvol>

        Parameters
        ----------
        infile : filename
            filename of volume to be moved
        reference : filename
            filename of volume used as target for registration
        inmatrix : filename  inmat.mat
            filename holding transformation matrix in asci format
        outfile : filename
            filename of new volume of infile moved to space of reference
            if None,  only the transformation matrix will be calculated

        Returns
        --------
        flirt : object
            return new flirt object with updated fields
        """
        #newflirt = self.update()
        if infile is None:
            if self.opts.infile is None:
                raise ValueError('input not specfied')
            else:
                infile = self.opts.infile
        if reference is None:
            if self.opts.reference is None:
                raise ValueError('reference is not specified')
            else:
                reference = self.opts.reference
        if outfile is None:
            if self.opts.outfile is None:
                raise ValueError('outfile not specified')
            else:
                outfile = self.opts.outfile
        if inmatrix is None:
            if self.opts.inmatrix is None:
                raise ValueError('inmatrix is not specified')
            else:
                inmatrix = self.opts.inmatrix
        newflirt = self.update(infile=infile, 
                               reference=reference,
                               outfile=outfile,
                               inmatrix = inmatrix)        
            
        newflirt.args.extend(['-in %s'%(infile)])
        newflirt.infile = infile
        
        newflirt.args.extend(['-ref %s'%(reference)])
        newflirt.reference = reference
        
        if newflirt.opts.applyisoxfm is not None:
            newflirt.args.extend(['-applyisoxfm %d'%(newflirt.opts['applyisoxfm'])])
            
        else:
            newflirt.args.extend(['-applyxfm'])
        
        newflirt.args.extend(['-init %s'%(inmatrix)])
        newflirt.inmatrix = inmatrix
        
        newflirt.args.extend(['-out %s'%(outfile)])
        newflirt.outfile = outfile
            
        cmd = newflirt._compile_command()
        
        newflirt.cmdline = cmd

        (retcode, out, err) = newflirt._runner(newflirt.cmdline)
        newflirt.retcode = retcode
        newflirt.out = out
        newflirt.err = err
        
        return newflirt

    def _compile_command(self):
        """validates fsl options and generates command line argument"""
        valid_opts = self._validate()
        if valid_opts is None:
            allargs = [self.cmd] + self.args
        else:
            allargs = [self.cmd] + valid_opts + self.args
        return ' '.join(allargs)

    def update(self, **opts):
        newflirt = Flirt()
        [newflirt.opts.__setattr__(k,v) for k, v in self.opts.iteritems() if v is not None ]
        newflirt.opts.update(**opts)
        return newflirt
        



class Fnirt(CommandLine):

    _cmd = None
    @property
    def cmd(self):
        """sets base command, not editable"""
        if self._cmd is None:
            self._cmd = 'fnirt'
        return self._cmd

    def __init__(self, **opts):
        """use fsl fnirt for non-linear registration
        
        Options
        -------
        see  
        fsl.Fnirt().opts_help()
        
        Example
        -------
        >>> fnirter = fsl.Fnirt(affine='affine.mat')
        >>> fnirted = fnirter.run(reference='ref.nii',moving='anat.nii')
        >>> fsl.Fnirt().opts_help()
       
       
        """
        super(Fnirt,self).__init__()
        self.args = []
        self._populate_opts()
        self.opts.update(**opts)
        self.cmdline = ''
        self.infile = ''
        self.reference = ''

    def opts_help(self):
        doc = """

        POSSIBLE OPTIONS
        -----------------
        (all default to None and are unset)
 
        http://www.fmrib.ox.ac.uk/fsl/fnirt/index.html#fnirt_parameters

        Parameters Specifying Input Files
        +++++++++++++++++++++++++++++++++
        infile : <filename>
            file that gets moved/warped
            can be set at .run(infile='infile')
        reference : <filename>
            file that specifies set space that infile
            gets moved/warped to
            can be set at .run(reference='reference')
        affine : <filename>
            name of file containing affine transform
	initwarp : <filename>
            name of file containing initial non-linear warps
	initintensity : <filename>
      	    name of file/files containing initial intensity maping
	configfile : <filename> 
	    Name of config file specifying command line arguments
	referencemask : <filename>
	    name of file with mask in reference space
	imagemask : <filename>	
            name of file with mask in input image space

        Parameters Specifying Output Files
        ++++++++++++++++++++++++++++++++++
	fieldcoeff_file: <filename>
	    name of output file with field coefficients
	outimage : <filename>
	    name of output image
	fieldfile : <filename>
	    name of output file with field
	jacobianfile : <filename>
	    name of file for writing out the Jacobian of the field 
            (for diagnostic or VBM purposes)
	reffile : <filename>	
            name of file for writing out intensity modulated reference
            (for diagnostic purposes)
	intensityfile : <filename>
	    name of files for writing information pertaining to 
            intensity mapping
	logfile : <filename>
	    Name of log-file

        verbose	: Bool
            If True, Print diagonostic information while running

        Parameters Specified "Once and for All"
        +++++++++++++++++++++++++++++++++++++++
        jacobian_range : [float,float]	
            Allowed range of Jacobian determinants, (FSLdefault 0.01,100.0)
            [0.01,100] generally ensures diffeomorphism (mapping invertible, 
            and there is exactly one position V for each position in U 
            (with mapping U -> V)
            [-1] allows jacobians to take any value (pos or neg)
            [0.2,5] suggested for VBM where the Jacobians are used to modulate 
            tissue probabilities, otherwise may have non-normal distributions
	warp_resolution: list [10.0,10.0,10.0]
	    (approximate) resolution (in mm) of warp basis 
            in x-, y- and z-direction, (FSLdefault 10,10,10)
	splineorder : int
	    Order of spline, 2->Qadratic spline, 3->Cubic spline. 
            (FSLDefault=3)
	implicit_refmask : Bool
	    If =True, use implicit masking based on value in --ref image. 
            (FSLDefault =1; True)
            Specifies a value implying that we are outside the valid FOV. 
            Typically that value will be zero, otherwise use
            implicit_refmaskval to specify other value  . 
            Occasionally a software will use some other value eg(NaN, 1024) 
	implicit_imgmask : Bool
	    If =1, use implicit masking based on value in --in image, 
            (FSLDefault =1; True) See explanation for implicit_refmask above
	implicit_refmaskval : float
	    Value to mask out in --ref image. FSLDefault =0.0
	implicit_imgmaskval : float
	    Value to mask out in --in image. FSLDefault =0.0
        ssqlambda : Bool	
            If True (=1), lambda is weighted by current sum of squares
            (FSLdefault =True), helps avoid solutions getting caught in 
            local minima
        regularization_model : string  {'membrane_energy', 'bending_energy'}
	    Model for regularisation of warp-field, 
            (FSLdefault 'bending_energy')
            Helps keep points close together in original image,
            close together in the warped image
        refderiv : Bool
 	    If True (1), reference image is used to calculate derivatives. 
            (FSLDefault = 0 ; False) Limited applicability
        intensity_model : string {'none', 'global_linear', 'global_non_linear',
            'local_linear', 'global_non_linear_with_bias', 'local_non_linear'}	
            Model for intensity-mapping: The purpose is to model intensity 
            differences between reference and image to avoid these affecting 
            the estimation of the warps. Modelling the intensity involves 
            extra estimation parameters (in addition to modelling the warps) 
            and willincrease both execution time and memory requirements. 
        intorder : int 	
            Determines the order of a polynomial that models a curvilinear 
            relationship between the intensities in (reference, image)
            (FSLdefault =  5)
        bias_resolution: [int, int, int]
            Determines the knot-spacing for splines used to model a bias-field.
            Relevant for intensity_models {'local_linear', 
            'global_non_linear_with_bias','local_non_linear'} 
            (FSLdefault=[50,50,50])
        bias_lambda : int
            Determines relative weight of sum-of-squared differences and  
            bending energy of the bias-field. Similar to the lambda paramter, 
            but for the bias-field rather than the warp-fields. 
            (FSLDefault is 10000) 
        hessian_datatype : string {'double', 'float'}
	    Precision for representing Hessian, Changing to float decreases
            amount of RAM needed to store Hessian allowing slightly higher 
            warp-resolution. Double used for most testing and validation 
            (FSL default = 'double') 

        Parameters Specified Once for each Sub-Sampling Level
        +++++++++++++++++++++++++++++++++++++++++++++++++++++
        Fnirt uses a multi-resolution, subsampling approach to
        identify best warps, starting at a coarse level, refining at
        higher resolutions.
        These parameters need to be set for each level 
        (typically 3 levels are used; greater levels = greater processing time)

        sub_sampling : list [4,2,1] 
	    sub-sampling scheme, default 4,2,1
            means image will be upsampled (factor of 4) at level one,
            upsampled (factor of 2) at level two, and
            then (full resolution) at level three
        max_iter : list [5,5,5]
	    Maximum number of non-linear iterations, at each level
            (FSLdefault 5,5,5)
	referencefwhm : list [4,2,1]
	    FWHM (in mm) of gaussian smoothing kernel for ref volume, 
            Smoothing should mirror sub_sampling
            sub_sampling = [4,2,1], referencefwhm = [8,4,1]
            (FSLdefault 4,2,0,0) reference often smooth, so can be less than image
	imgfwhm : list [6.0,4.0,2.0,2.0]
	    FWHM (in mm) of gaussian smoothing kernel for input volume, 
            Smoothing should mirror sub_sampling
            sub_sampling = [4,2,1], imgfwhm = [10,6,2]
            (FSLdefault 6,4,2,2)
	lambdas : list [300, 75, 30]
            Specifies relative weighting of the sum-of-squared differences 
            and the regularisation (smoothness) of the warps.
            FSLdefault depends on ssqlambda and regularization_model switches.
            Different "types" of data require different values
            You can specify **one** value, but best to modulate with 
            sub_sampling
        estintensity : list [1,1,0]
            Determines if the parameters of the chosen intesity-model should be 
            estimated at each level if intensity_model is not None
            eg [1,1,0] Estimates at first two levels but not at last level
            assuming estimates at that level are fairly correct
        applyrefmask : list [1,1,1]
	    Use specified refmask at each level
            (FSLdefault 1 (true)) eg [0,0,1] to not use brain mask for 
            initial coarse level registration, as extra-cranial tissue may
            provide information useful at initial steps
	applyimgmask : list [1,1,1]
	    Use specified imagemask at each level
            (FSLdefault 1 (true)) eg [0,0,1] to not use brain mask for 
            initial coarse level registration, as extra-cranial tissue may
            provide information useful at initial steps
        """
        print doc
    def _populate_opts(self):
        self.opts = Bunch(infile=None,
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

    def _validate(self):
        """validate fsl bet options
        if set to None ignore
        """
        out_opts = []
        opts = {}
        [opts.update({k:v}) for k, v in self.opts.iteritems() if v is not None ]
        for opt in opts:
            if opt in ['infile', 'reference']:
                continue
            if opt is 'affine':
                val = opts[opt]
                out_opts.extend(['--aff %s'%(val)])
                continue
            if opt is 'initwarp':
                val = opts[opt]
                out_opts.extend(['--inwarp %s'%(val)])
                continue                
            if opt is 'initintensity':
                val = opts[opt]
                out_opts.extend(['--intin %s'%(val)])
                continue
            if opt is 'configfile':
                val = opts[opt]
                out_opts.extend(['--config %s'%(val)])
                continue
            if opt is 'referencemask':
                val = opts[opt]
                out_opts.extend(['--refmask %s'%(val)])
                continue
            if opt is 'imagemask':
                val = opts[opt]
                out_opts.extend(['--inmask %s'%(val)])
                continue
            if opt is 'fieldcoeff_file':
                val = opts[opt]
                out_opts.extend(['--cout %s'%(val)])
                continue
            if opt is 'outimage':
                val = opts[opt]
                out_opts.extend(['--iout %s'%(val)])
                continue
            if opt is 'fieldfile':
                val = opts[opt]
                out_opts.extend(['--fout %s'%(val)])
                continue
            if opt is 'jacobianfile':
                val = opts[opt]
                out_opts.extend(['--jout %s'%(val)])
                continue
            if opt is 'reffile':
                val = opts[opt]
                out_opts.extend(['--refout %s'%(val)])
                continue
            if opt is 'intensityfile':
                val = opts[opt]
                out_opts.extend(['--intout %s'%(val)])
                continue
            if opt is 'logfile':
                val = opts[opt]
                out_opts.extend(['--logout %s'%(val)])
                continue
            if opt is 'verbose':
                if opts[opt]:
                    out_opts.extend(['--verbose'])
                continue
            if opt is 'sub_sampling':
                val = opts[opt]
                tmpstr = '--subsample '
                for item in val:
                    tmpstr = tmpstr + '%d, '%(item)
                out_opts.extend([tmpstr[:-2]])
                continue
            if opt is 'max_iter':
                val = opts[opt]
                tmpstr = '--miter '
                for item in val:
                    tmpstr = tmpstr + '%d, '%(item)
                out_opts.extend([tmpstr[:-2]])
                continue               
            if opt is 'referencefwhm':
                val = opts[opt]
                tmpstr = '--reffwhm '
                for item in val:
                    tmpstr = tmpstr + '%d, '%(item)
                out_opts.extend([tmpstr[:-2]])
                continue
            if opt is 'imgfwhm':
                val = opts[opt]
                tmpstr = '--infwhm '
                for item in val:
                    tmpstr = tmpstr + '%d, '%(item)
                out_opts.extend([tmpstr[:-2]])
                continue
            if opt is 'lambdas':
                val = opts[opt]
                tmpstr = '--lambda '
                for item in val:
                    tmpstr = tmpstr + '%d, '%(item)
                out_opts.extend([tmpstr[:-2]])
                continue
            if opt is 'estintensity':
                val = opts[opt]
                tmpstr = '--estint '
                for item in val:
                    tmpstr = tmpstr + '%d, '%(item)
                out_opts.extend([tmpstr[:-2]])
                continue
            if opt is 'applyrefmask':
                val = opts[opt]
                tmpstr = '--applyrefmask '
                for item in val:
                    tmpstr = tmpstr + '%d, '%(item)
                out_opts.extend([tmpstr[:-2]])
                continue
            if opt is 'applyimgmask':
                val = opts[opt]
                tmpstr = '--applyinmask '
                for item in val:
                    tmpstr = tmpstr + '%d, '%(item)
                out_opts.extend([tmpstr[:-2]])
                continue
            if opt is 'flags':
                out_opts.extend(opts[opt])
                continue
            print 'option %s not supported'%(opt)
        return out_opts
            
    def _compile_command(self):
        """validates fsl options and generates command line argument"""
        valid_opts = self._validate()
        allargs = self.args + valid_opts
        return ' '.join(allargs)
  
    def run(self, infile=None, reference=None):
        """ runs fnirt command
         

        Parameters
        ----------
        infile : filename
            filename of volume to be warped/moved
        reference : filename
            filename of volume used as target for  warp registration

        Returns
        --------
        fnirt : object
            return new fnirt object with updated fields

        Examples
        --------
        >>> #T1-> MNI153
        >>>fnirt_mprage = fsl.Fnirt(imgfwhm=[8,4,2],sub_sampling=[4,2,1],
                                   warp_resolution=[6,6,6])
        >>>fnirted_mprage = fnirt_mprage.run(infile='jnkT1.nii', reference='refimg.nii')
        """
        #newfnirt = self.update()
        if infile is None:
            if self.opts.infile is None:
                raise ValueError('infile is not specified')
            else:
                infile = self.opts.infile
        if reference is None:
            if self.opts.reference is None:
                raise ValueError('reference is not specified')
            else:
                reference = self.opts.reference
        newfnirt = self.update(infile=infile, reference=reference)
        newfnirt.args.extend(['--in %s'%(infile)])
        newfnirt.infile = infile
        newfnirt.args.extend(['--ref %s'%(reference)])
        newfnirt.reference = reference
        
        cmd = newfnirt._compile_command()
        newfnirt.cmdline = cmd
        
        (retcode, out, err) = newfnirt._runner(newfnirt.cmdline)
        newfnirt.retcode = retcode
        newfnirt.out = out
        newfnirt.err = err
        
        return newfnirt

    def _compile_command(self):
        """validates fsl options and generates command line argument"""
        valid_opts = self._validate()
        
        if valid_opts is None:
            allargs = [self.cmd] + self.args
        else:
            allargs = [self.cmd] + valid_opts + self.args
        return ' '.join(allargs)

    def update(self, **opts):
        newfnirt = Fnirt()
        [newfnirt.opts.__setattr__(k,v) for k, v in self.opts.iteritems() if v is not None ]
        newfnirt.opts.update(**opts)
        return newfnirt

    def write_config(self,configfile):
        """Writes out currently set options to specified config file
        
        Parameters
        ----------
        configfile : /path/to/configfile

                
        """
        valid_opts = self._validate() 
        try :
            fid = fopen(configfile, 'w+')
        except IOError:
            print ('unable to create config_file %s'%(configfile))
            
        for item in valid_opts:
            fid.write('%s\n'%(item))
        fid.close()


# These should probably get read in from a separate file, but I don't know how
# to do that safely in a module - lil' help? -DJC

# Also these are still somewhat specific to my experiment, but should be so in
# an obvious way.  Contrasts in particular need to be addressed more generally

# This seems quite clunky, and Cindee will hate that '/'!
# At a minimum, this should probably be redone with a setattr_on_read property,
# available currently in the model_dev branch
fsf_header_fname = os.path.dirname(__file__) + '/data/feat_template1.txt'
fsf_header_txt = open(fsf_header_fname).read()
fsf_header = Template(fsf_header_txt)

fsf_ev_template = Template('''
# EV title
set fmri(evtitle$ev_num) "$ev_name"

# Basic waveform shape
# 0 : Square
# 1 : Sinusoid
# 2 : Custom (1 entry per volume)
# 3 : Custom (3 column format)
# 4 : Interaction
# 10 : Empty (all zeros)
set fmri(shape$ev_num) 3

# Convolution
# 0 : None
# 1 : Gaussian
# 2 : Gamma
# 3 : Double-Gamma HRF
# 4 : Gamma basis functions
# 5 : Sine basis functions
# 6 : FIR basis functions
set fmri(convolve$ev_num) 2

# Convolve phase
set fmri(convolve_phase$ev_num) 0

# Apply temporal filtering
set fmri(tempfilt_yn$ev_num) 1

# Add temporal derivative
set fmri(deriv_yn$ev_num) 0

# Custom EV file
set fmri(custom$ev_num) "$base_dir/analysis/EVs/block$scan_num-$ev_name.txt"

# Gamma sigma
set fmri(gammasigma$ev_num) 3

# Gamma delay
set fmri(gammadelay$ev_num) 6
''')

fsf_ev_ortho = Template('''
# Orthogonalise EV wrt EV
set fmri(ortho$c0.$c1) 0
''')

contrasts_template = '''
# Contrast & F-tests mode
# real : control real EVs
# orig : control original EVs
set fmri(con_mode_old) orig
set fmri(con_mode) orig

# Display images for contrast_real 1
set fmri(conpic_real.1) 1

# Title for contrast_real 1
set fmri(conname_real.1) "left>right"

# Real contrast_real vector 1 element 1
set fmri(con_real1.1) 1

# Real contrast_real vector 1 element 2
set fmri(con_real1.2) -1.0

# Real contrast_real vector 1 element 3
set fmri(con_real1.3) 1.0

# Real contrast_real vector 1 element 4
set fmri(con_real1.4) -1.0

# Real contrast_real vector 1 element 5
set fmri(con_real1.5) 1.0

# Real contrast_real vector 1 element 6
set fmri(con_real1.6) -1.0

# Real contrast_real vector 1 element 7
set fmri(con_real1.7) 1.0

# Real contrast_real vector 1 element 8
set fmri(con_real1.8) -1.0

# Display images for contrast_orig 1
set fmri(conpic_orig.1) 1

# Title for contrast_orig 1
set fmri(conname_orig.1) "left>right"

# Real contrast_orig vector 1 element 1
set fmri(con_orig1.1) 1

# Real contrast_orig vector 1 element 2
set fmri(con_orig1.2) -1.0

# Real contrast_orig vector 1 element 3
set fmri(con_orig1.3) 1.0

# Real contrast_orig vector 1 element 4
set fmri(con_orig1.4) -1.0

# Real contrast_orig vector 1 element 5
set fmri(con_orig1.5) 1.0

# Real contrast_orig vector 1 element 6
set fmri(con_orig1.6) -1.0

# Real contrast_orig vector 1 element 7
set fmri(con_orig1.7) 1.0

# Real contrast_orig vector 1 element 8
set fmri(con_orig1.8) -1.0

# Contrast masking - use >0 instead of thresholding?
set fmri(conmask_zerothresh_yn) 0

# Do contrast masking at all?
set fmri(conmask1_1) 0

# Now options that don't appear in the GUI

# Alternative example_func image (not derived from input 4D dataset)
set fmri(alternative_example_func) ""

# Alternative (to BETting) mask image
set fmri(alternative_mask) ""

# Initial structural space registration initialisation transform
set fmri(init_initial_highres) ""

# Structural space registration initialisation transform
set fmri(init_highres) ""

# Standard space registration initialisation transform
set fmri(init_standard) ""


# For full FEAT analysis: overwrite existing .feat output dir?
set fmri(overwrite_yn) 1
'''

class FSFmaker:
    '''Use the template variables above to construct fsf files for feat.
    
    This doesn't actually run anything.
    
    Example usage
    -------------
    FSFmaker(5, ['left', 'right', 'both'])
        
    '''
    def __init__(self, num_scans, cond_names):
        subj_dir = dirname(getcwd())
        fsl_root = getenv('FSLDIR')
        for i in range(num_scans):
            fsf_txt = fsf_header.substitute(num_evs=len(cond_names), 
                                            base_dir=subj_dir, scan_num=i,
                                            fsl_root=fsl_root)
            for j, cond in enumerate(cond_names):
                fsf_txt += self.gen_ev(i, j+1, cond, subj_dir, len(cond_names))
            fsf_txt += contrasts_template

            f = open('scan%d.fsf' % i, 'w')
            f.write(fsf_txt)
            f.close()
                
                
    def gen_ev(self, scan, cond_num, cond_name, subj_dir, total_conds):
        args = (cond_num, cond_name) + (cond_num,) * 6 + \
                (scan, cond_name) + (cond_num, ) * 2

        ev_txt = fsf_ev_template.substitute(ev_num=cond_num, ev_name=cond_name,
                                        scan_num=scan, base_dir=subj_dir)

        for i in range(total_conds + 1):
            ev_txt += fsf_ev_ortho.substitute(c0=cond_num, c1=i) 

        return ev_txt


##################################################################################


    
    
def bet(*args, **kwargs):
    bet_element = BetElement(*args, **kwargs)
    
    # We should check the return value
    bet_element.execute()

    return load_image(bet_element.state['output'])

def flirt(target, moving, space=None, output_filename=None, **kwargs):
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
    target_filename = target.filename

    
def apply_transform(target, moving, transform, space=None, output_filename=None):
    """
    While this also uses flirt, it is a quite different usage, and as such gets
    it's own function.
    """
    pass
