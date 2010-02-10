"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 4.1.4.

Currently these tools are supported:

* BET v2.1: brain extraction
* FAST v4.1: segmentation and bias correction
* FLIRT v5.5: linear registration
* MCFLIRT: motion correction
* FNIRT v1.0: non-linear warp

Examples
--------
See the docstrings of the individual classes for examples.

"""

import os
import re
import subprocess
from copy import deepcopy
from glob import glob
import warnings
from shutil import rmtree # to delete dirs

from nipype.externals.pynifti import load
from nipype.utils.filemanip import (fname_presuffix, list_to_filename,
                                    filename_to_list, loadflat)
from nipype.interfaces.base import (Bunch, CommandLine, Interface,
                                    load_template, InterfaceResult)
from nipype.utils import setattr_on_read
from nipype.utils.docparse import get_doc
from nipype.utils.misc import container_to_string, is_container

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

class FSLInfo(object):
    '''A class to encapsulate stuff we'll need throughout the

    This should probably be a singleton class? or do we want to make it
    possible to wrap a few versions of FSL? In any case, currently we
    instantiate an instance here called fsl_info

    I'm also not sure this is the best ordering for the various attributes and
    methods. Please feel free to reorder.'''
    @property
    def version(self):
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
            return None

        out = clout.runtime.stdout
        basedir = os.path.split(os.path.split(out)[0])[0]
        clout = CommandLine('cat %s/etc/fslversion'%(basedir)).run()
        out = clout.runtime.stdout
        return out.strip('\n')

    ftypes = {'NIFTI':'nii',
              'NIFTI_PAIR':'img',
              'NIFTI_GZ':'nii.gz',
              'NIFTI_PAIR_GZ':'img.gz',
              None: 'env variable FSLOUTPUTTYPE not set'}

    def outputtype(self, ftype=None):
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
        if ftype is None:
            # get environment setting
            fsl_ftype = os.getenv('FSLOUTPUTTYPE','NIFTI_GZ')

        else:
            # set environment setting - updating environ automatically calls
            # putenv. Note, docs claim putenv may cause memory leaks on OSX and
            # FreeBSD :\ I see no workarounds -DJC
            # os.putenv('FSLOUTPUTTYPE',fsl_ftype)
            if ftype in self.ftypes.keys():
                os.environ['FSLOUTPUTTYPE'] = ftype
            else:
                raise IOError('FSLOUTPUTTYPE %s is not supported' % (ftype))
            fsl_ftype = ftype

        # This is inappropriate in a utility function
        # print 'FSLOUTPUTTYPE = %s (\"%s\")' % (fsl_ftype,
        #                                        self.ftypes[fsl_ftype] )
        return fsl_ftype, self.ftypes[fsl_ftype]

    def standard_image(self, img_name):
        '''Grab an image from the standard location.

        Could be made more fancy to allow for more relocatability'''
        fsldir = os.environ['FSLDIR']
        return os.path.join(fsldir, 'data/standard', img_name)

    def glob(self, fname):
        '''Check if, given a filename, FSL actually produced it.

        The maing thing we're doing here is adding an appropriate extension
        while globbing. Note that it returns a single string, not a list
        (different from glob.glob)'''
        # Could be made more faster / less clunky, but don't care until the API
        # is sorted out

        # While this function is a little globby, it may not be the best name.
        # Certainly, glob here is more expensive than necessary (could just use
        # os.path.exists)

        # stripping the filename of extensions that FSL will recognize and
        # substitute
        for ext in self.ftypes.values():
            if fname.endswith(ext):
                fname = fname[:-(len(ext)+1)]
                break

        _, ext = self.outputtype()
        files = glob(fname) or glob(fname + '.' + ext)

        try:
            return files[0]
        except IndexError:
            return None

    def gen_fname(self, basename, fname=None, cwd=None, suffix='_fsl',
                  check=False, cmd='unknown'):
        '''Define a generic mapping for a single outfile

        The filename is potentially autogenerated by suffixing inputs.infile

        Parameters
        ----------
        basename : string (required)
            filename to base the new filename on
        fname : string
            if not None, just use this fname
        cwd : string
            prefix paths with cwd, otherwise os.getcwd()
        suffix : string
            default suffix
        check : bool
            check if file exists, adding appropriate extension, raise exception
            if it doesn't
        '''
        if cwd is None:
            cwd = os.getcwd()

        if fname is None:
            ftype,ext = self.outputtype()
            suffix = '.'.join((suffix,ext))
            fname = fname_presuffix(list_to_filename(basename), suffix=suffix,
                                    use_ext=False, newpath=cwd)

        if check:
            fname = fsl_info.glob(fname)
            if fname is None:
                raise IOError('file %s not generated by %s' % (fname, cmd))

        # XXX This should ultimately somehow allow for relative paths if cwd is
        # specified or similar. For now, though, this needs to happen to make
        # the pipeline code work
        return os.path.realpath(fname)

fsl_info = FSLInfo()

def fslversion():
    msg = """fsl.fslversion is no longer available. instead replace with:

             fsl.fsl_info.version

             This message will be removed in the next release
          """
    raise Exception(msg)

def fsloutputtype(ftype=None):
    msg = """fsl.fsloutputtype is no longer available. instead replace with:

             fsl.fsl_info.outputtype(...)

             This message will be removed in the next release
          """
    raise Exception(msg)

class FSLCommand(CommandLine):
    '''General support for FSL commands'''
    opt_map = {}

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
        results : InterfaceResult
            An :class:`nipype.interfaces.base.InterfaceResult` object
            with a copy of self in `interface`

        """
        results = self._runner(cwd=os.getcwd())
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs()

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
        inputs = sorted((k, v) for k, v in self.inputs.iteritems()
                            if v is not None and k not in skip)
        for opt, value in inputs:
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
                elif isinstance(value, list) and self.__class__.__name__ == 'Fnirt':
                    # XXX Hack to deal with special case where some
                    # parameters to Fnirt can have a variable number
                    # of arguments.  Splitting the argument string,
                    # like '--infwhm=%d', then add as many format
                    # strings as there are values to the right-hand
                    # side.
                    argparts = argstr.split('=')
                    allargs.append(argparts[0] + '=' +
                                   ','.join([argparts[1] % y for y in value]))
                elif isinstance(value, list):
                    allargs.append(argstr % tuple(value))
                else:
                    # Append options using format string.
                    allargs.append(argstr % value)
            except TypeError, err:
                msg = 'Error when parsing option %s in class %s.\n%s' % \
                    (opt, self.__class__.__name__, err.message)
                warn(msg)
            except KeyError:
                warn("Option '%s' is not supported!" % (opt))
                raise

        return allargs

    def _populate_inputs(self):
        self.inputs = Bunch((k,None) for k in self.opt_map.keys())

    def inputs_help(self):
        """Print command line documentation for the command."""
        print get_doc(self.cmd, self.opt_map, '-h')

    def aggregate_outputs(self):
        raise NotImplementedError(
                'Subclasses of FSLCommand must implement aggregate_outputs')

    def outputs_help(self):
        """Print outputs help
        """
        print self.outputs.__doc__

    def outputs(self):
        """Virtual function"""
        raise NotImplementedError(
                'Subclasses of FSLCommand must implement outputs')

class Bet(FSLCommand):
    """Use FSL BET command for skull stripping.

    For complete details, see the `BET Documentation.
    <http://www.fmrib.ox.ac.uk/fsl/bet2/index.html>`_

    To print out the command line help, use:
        fsl.Bet().inputs_help()

    Examples
    --------
    Initialize Bet with no options, assigning them when calling run:

    >>> from nipype.interfaces import fsl
    >>> btr = fsl.Bet()
    >>> res = btr.run('infile', 'outfile', frac=0.5) # doctest: +SKIP

    Assign options through the ``inputs`` attribute:

    >>> btr = fsl.Bet()
    >>> btr.inputs.infile = 'foo.nii'
    >>> btr.inputs.outfile = 'bar.nii'
    >>> btr.inputs.frac = 0.7
    >>> res = btr.run() # doctest: +SKIP

    Specify options when creating a Bet instance:

    >>> btr = fsl.Bet(infile='infile', outfile='outfile', frac=0.5)
    >>> res = btr.run() # doctest: +SKIP

    Loop over many inputs (Note: the snippet below would overwrite the
    outfile each time):

    >>> btr = fsl.Bet(infile='infile', outfile='outfile')
    >>> fracvals = [0.3, 0.4, 0.5]
    >>> for val in fracvals:
    ...     res = btr.run(frac=val) # doctest: +SKIP

    """

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'bet'

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
        'functional':         '-F',
        'flags':              '%s',
        'reduce_bias':        '-B',
        'infile':             None,
        'outfile':            None,
        }
    # Currently we don't support -R, -S, -Z,-A or -A2

    def inputs_help(self):
        """Print command line documentation for Bet."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def _parse_inputs(self):
        """validate fsl bet options"""
        allargs = super(Bet, self)._parse_inputs(skip=('infile', 'outfile'))

        if self.inputs.infile:
            infile = list_to_filename(self.inputs.infile)
            allargs.insert(0, infile)
            outfile = fsl_info.gen_fname(infile,
                                         self.inputs.outfile,
                                         suffix='_brain')
            allargs.insert(1, outfile)

        return allargs

    def run(self, infile=None, outfile=None, **inputs):
        """Execute the command.

        Parameters
        ----------
        infile : string
            Filename to be skull stripped.
        outfile : string, optional
            Filename to save output to. If not specified, the ``infile``
            filename will be used with a "_brain" suffix.
        inputs : dict
            Additional ``inputs`` assignments can be passed in.  See
            Examples section.

        Returns
        -------
        results : InterfaceResult
            An :class:`nipype.interfaces.base.InterfaceResult` object
            with a copy of self in `interface`

        Examples
        --------
        To pass command line arguments to ``bet`` that are not part of
        the ``inputs`` attribute, pass them in with the ``flags``
        input.

        >>> from nipype.interfaces import fsl
        >>> import os
        >>> btr = fsl.Bet(infile='foo.nii', outfile='bar.nii', flags='-v')
        >>> cmdline = 'bet foo.nii %s -v'%os.path.join(os.getcwd(),'bar.nii')
        >>> btr.cmdline == cmdline
        True

        """
        if infile:
            self.inputs.infile = infile
        if self.inputs.infile is None:
            raise ValueError('Bet requires an input file')
        if isinstance(self.inputs.infile, list):
            raise ValueError('Bet does not support multiple input files')
        if outfile:
            self.inputs.outfile = outfile
        self.inputs.update(**inputs)
        return super(Bet, self).run()

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string,file
                path/name of skullstripped file
            maskfile : string, file
                binary brain mask if generated
        """
        outputs = Bunch(outfile=None,maskfile=None)
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        outputs = self.outputs()
        cwd = os.getcwd()
        outputs.outfile = fsl_info.gen_fname(self.inputs.infile,
                                self.inputs.outfile, cwd=cwd, suffix='_brain',
                                check=True)
        if self.inputs.mask or self.inputs.reduce_bias:
            outputs.maskfile = fsl_info.gen_fname(outputs.outfile, cwd=cwd,
                                                  suffix='_mask', check=True)
        return outputs


class Fast(FSLCommand):
    """Use FSL FAST for segmenting and bias correction.

    For complete details, see the `FAST Documentation.
    <http://www.fmrib.ox.ac.uk/fsl/fast4/index.html>`_

    To print out the command line help, use:
        fsl.Fast().inputs_help()

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> faster = fsl.Fast(out_basename='myfasted')
    >>> fasted = faster.run(['file1','file2'])

    >>> faster = fsl.Fast(infiles=['filea','fileb'], out_basename='myfasted')
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
            'probability_maps':     '-p',
            'infiles':               None,
            }

    def inputs_help(self):
        """Print command line documentation for FAST."""
        print get_doc(self.cmd, self.opt_map,trap_error=False)

    def run(self, infiles=None, **inputs):
        """Execute the FSL fast command.

        Parameters
        ----------
        infiles : string or list of strings
            File(s) to be segmented or bias corrected
        inputs : dict
            Additional ``inputs`` assignments can be passed in.

        Returns
        -------
        results : InterfaceResult
            An :class:`nipype.interfaces.base.InterfaceResult` object
            with a copy of self in `interface`

        """

        if infiles:
            self.inputs.infiles = infiles
        if not self.inputs.infiles:
            raise AttributeError('Fast requires input file(s)')
        self.inputs.update(**inputs)
        return super(Fast, self).run()

    def _parse_inputs(self):
        '''Call our super-method, then add our input files'''
        # Could do other checking above and beyond regular _parse_inputs here
        allargs = super(Fast, self)._parse_inputs(skip=('infiles'))
        if self.inputs.infiles:
            allargs.append(container_to_string(self.inputs.infiles))
        return allargs

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            Each attribute in ``outputs`` is a list.  There will be
            one set of ``outputs`` for each file specified in
            ``infiles``.  ``outputs`` will contain the following
            files:

            mixeltype : list
                filename(s)
            partial_volume_map : list
                filenames, one for each input
            partial_volume_files : list
                filenames, one for each class, for each input
            tissue_class_map : list
                filename(s), each tissue has unique int value
            tissue_class_files : list
                filenames, one for each class, for each input
            restored_image : list
                filename(s) bias corrected image(s)
            bias_field : list
                filename(s)
            probability_maps : list
                filenames, one for each class, for each input
        """
        outputs = Bunch(mixeltype = [],
                seg = [],
                partial_volume_map=[],
                partial_volume_files=[],
                tissue_class_map=[],
                tissue_class_files=[],
                bias_corrected=[],
                bias_field=[],
                prob_maps=[])
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object

        Notes
        -----
        For each item in Bunch:
        If [] empty list, optional file was not generated
        Else, list contains path,filename of generated outputfile(s)

        Raises
        ------
        IOError
            If any expected output file is not found.

        """
        _, ext = fsl_info.outputtype()
        outputs = self.outputs()

        if not is_container(self.inputs.infiles):
            infiles = [self.inputs.infiles]
        else:
            infiles = self.inputs.infiles
        for item in infiles:
            # get basename (correct fsloutpputytpe extension)
            if self.inputs.out_basename:
                pth, nme = os.path.split(item)
                jnk, ext = os.path.splitext(nme)
                item = pth + self.inputs.out_basename + '.%s' % (envext)
            else:
                nme, ext = os.path.splitext(item)
                item = nme + '.%s' % (envext)
            # get number of tissue classes
            if not self.inputs.number_classes:
                nclasses = 3
            else:
                nclasses = self.inputs.number_classes

            # always seg, (plus mutiple?)
            outputs.seg.append(fname_presuffix(item, suffix='_seg'))
            if self.inputs.segments:
                for i in range(nclasses):
                    outputs.seg.append(fname_presuffix(item,
                        suffix='_seg_%d'%(i)))
                    # always pve,mixeltype unless nopve = True
            if not self.inputs.nopve:
                fname = fname_presuffix(item, suffix='_pveseg')
                outputs.partial_volume_map.append(fname)
                fname = fname_presuffix(item, suffix='_mixeltype')
                outputs.mixeltype.append(fname)

                for i in range(nclasses):
                    fname = fname_presuffix(item, suffix='_pve_%d'%(i))
                    outputs.partial_volume_files.append(fname)

            # biasfield ?
            if self.inputs.output_biasfield:
                outputs.bias_field.append(fname_presuffix(item, suffix='_bias'))

            # restored image (bias corrected)?
            if self.inputs.output_biascorrected:
                fname = fname_presuffix(item, suffix='_restore')
                outputs.biascorrected.append(fname)

            # probability maps ?
            if self.inputs.probability_maps:
                for i in range(nclasses):
                    fname = fname_presuffix(item, suffix='_prob_%d'%(i))
                    outputs.prob_maps.append(fname)

        # For each output file-type (key), check that any expected
        # files in the output list exist.
        for outtype, outlist in outputs.iteritems():
            if len(outlist) > 0:
                for outfile in outlist:
                    if not len(glob(outfile))==1:
                        msg = "Output file '%s' of type '%s' was not generated"\
                                % (outfile, outtype)
                        raise IOError(msg)

        return outputs


class Flirt(FSLCommand):
    """Use FSL FLIRT for coregistration.

    For complete details, see the `FLIRT Documentation.
    <http://www.fmrib.ox.ac.uk/fsl/flirt/index.html>`_

    To print out the command line help, use:
        fsl.Flirt().inputs_help()

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> flt = fsl.Flirt(bins=640, searchcost='mutualinfo')
    >>> flt.inputs.infile = 'subject.nii'
    >>> flt.inputs.reference = 'template.nii'
    >>> flt.inputs.outfile = 'moved_subject.nii'
    >>> flt.inputs.outmatrix = 'subject_to_template.mat'
    >>> res = flt.run()


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
            'flags':              '%s',
            'infile':             None,
            'outfile':            None,
            'reference':          None,
            'outmatrix':          None,
            'inmatrix':           None,
            }

    def inputs_help(self):
        """Print command line documentation for FLIRT."""
        print get_doc(self.cmd, self.opt_map,'-help')


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

    def run(self, infile=None, reference=None, outfile=None,
            outmatrix=None, **inputs):
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
            Additional ``inputs`` assignments.

        Returns
        -------
        results : InterfaceResult
            An :class:`nipype.interfaces.base.InterfaceResult` object
            with a copy of self in `interface`

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
        return super(Flirt, self).run()

    def outputs(self):
        """Returns a bunch containing output parameters

        Parameters
        ----------

           outfile : string, file

           outmatrix : string, file

        """
        outputs = Bunch(outfile=None, outmatrix=None)
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            outfile
            outmatrix

        Raises
        ------
        IOError
            If expected output file(s) outfile or outmatrix are not found.

        """
        outputs = self.outputs()

        def raise_error(filename):
            raise IOError('File %s was not generated by Flirt' % filename)
        cwd = os.getcwd()
        if self.inputs.outfile:
            outputs.outfile = os.path.join(cwd, self.inputs.outfile)
            if not fsl_info.glob(outputs.outfile):
                raise_error(outputs.outfile)
        if self.inputs.outmatrix:
            outputs.outmatrix = os.path.join(cwd, self.inputs.outmatrix)
            if not fsl_info.glob(outputs.outmatrix):
                raise_error(outputs.outmatrix)
        return outputs

class ApplyXfm(Flirt):
    '''Use FSL FLIRT to apply a linear transform matrix.

    For complete details, see the `FLIRT Documentation.
    <http://www.fmrib.ox.ac.uk/fsl/flirt/index.html>`_

    To print out the command line help, use:
        fsl.ApplyXfm().inputs_help()

    Note: This class is currently untested. Use at your own risk!

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> xfm = ApplyXfm(infile='subject.nii', reference='mni152.nii', bins=640)
    >>> xfm_applied = xfm.run(inmatrix='xform.mat')
    '''
    def _parse_inputs(self):
        '''Call our super-method, then add our input files'''
        allargs = super(ApplyXFM, self)._parse_inputs()
        if not self.inputs.outfile:
            outfile = fsl_info.gen_fname(self.inputs.infile,
                                         self.inputs.outfile,
                                         suffix='_axfm')
            allargs.append(' '.join(('-out',outfile)))
        for idx,arg in enumerate(allargs):
            if '-out' in arg:
                continue
        allargs.insert(idx,'-applyxfm')
        return allargs

    def run(self, infile=None, reference=None, inmatrix=None,
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
            Filename for input transformation matrix, in ascii format.
        outfile : string, optional
            Filename of the output, registered volume.  If not
            specified, only the transformation matrix will be
            calculated.
        inputs : dict
            Additional ``inputs`` assignments.

        Returns
        -------
        results : InterfaceResult
            An :class:`nipype.interfaces.base.InterfaceResult` object
            with a copy of self in `interface`

        Examples
        --------
        >>> from nipype.interfaces import fsl
        >>> flt = fsl.Flirt(infile='subject.nii', reference='template.nii')
        >>> xformed = flt.run(inmatrix='xform.mat', outfile='xfm_subject.nii')

        """

        if infile:
            self.inputs.infile = infile
        if not self.inputs.infile:
            raise AttributeError('ApplyXfm requires an infile.')
        if reference:
            self.inputs.reference = reference
        if not self.inputs.reference:
            raise AttributeError('ApplyXfm requires a reference file.')
        if inmatrix:
            self.inputs.inmatrix = inmatrix
        if not self.inputs.inmatrix:
            raise AttributeError('ApplyXfm requires an inmatrix')
        if outfile:
            self.inputs.outfile = outfile
        self.inputs.update(**inputs)
        return super(ApplyXfm, self).run()

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string, filename
            outmatrix : string, filename
        """
        outputs = Bunch(outfile=None,outmatrix=None)
        return outputs

    def aggregate_outputs(self,verify_outmatrix=False):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            outfile

        Raises
        ------
        IOError
            If expected output file(s) outfile or outmatrix are not found.

        """
        outputs = self.outputs()
        # Verify output files exist
        outputs.outfile = fsl_info.gen_fname(self.inputs.infile,
                                             self.inputs.outfile,
                                             suffix='_axfm',
                                             check=True)
        if self.inputs.outmatrix:
            outputs.outmatrix = self.inputs.outmatrix

        def raise_error(filename):
            raise IOError('File %s was not generated by Flirt' % filename)

        if verify_outmatrix:
            outmatrix = glob(outputs.outmatrix)
            if not outmatrix:
                raise_error(outputs.outmatrix)
            else:
                outputs.outmatrix = outmatrix
        return outputs

class McFlirt(FSLCommand):
    """Use FSL MCFLIRT to do within-modality motion correction.

    For complete details, see the `MCFLIRT Documentation.
    <http://www.fmrib.ox.ac.uk/fsl/mcflirt/index.html>`_

    To print out the command line help, use:
        McFlirt().inputs_help()

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> mcflt = fsl.McFlirt(infile='timeseries.nii', cost='mututalinfo')
    >>> res = mcflt.run()

    """
    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'mcflirt'

    def inputs_help(self):
        """Print command line documentation for MCFLIRT."""
        print get_doc(self.cmd, self.opt_map, '-help', False)

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
            'report':      '-report',
            'reffile':     '-reffile %s',
            'infile':      None,
            }

    def _parse_inputs(self):
        """Call our super-method, then add our input files"""
        allargs = super(McFlirt, self)._parse_inputs(skip=('infile'))
        # XXX This would be handled properly by the standard mechanisms,
        # Why is it being done here?
        if self.inputs.infile:
            infile = list_to_filename(self.inputs.infile)
            allargs.insert(0,'-in %s'%infile)
            outfile = fsl_info.gen_fname(infile, self.inputs.outfile, suffix='_mcf')
            allargs.append(self.opt_map['outfile'] % outfile)
        
        return allargs

    def run(self, infile=None, **inputs):
        """Runs mcflirt

        Parameters
        ----------
        infile : string
            Filename of volume to be aligned
        inputs : dict
            Additional ``inputs`` assignments.

        Returns
        -------
        results : InterfaceResult
            An :class:`nipype.interfaces.base.InterfaceResult` object
            with a copy of self in `interface`

        Examples
        --------
        >>> from nipype.interfaces import fsl
        >>> mcflrt = fsl.McFlirt(cost='mutualinfo')
        >>> mcflrtd = mcflrt.run(infile='timeseries.nii')

        """
        if infile:
            self.inputs.infile = infile
        if not self.inputs.infile:
            raise AttributeError('McFlirt requires an infile.')

        self.inputs.update(**inputs)
        return super(McFlirt, self).run()

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string, filename
            varianceimg : string, filename
            stdimg : string, filename
            meanimg : string, filename
            parfile : string, filename
            outmatfile : string, filename
        """
        outputs = Bunch(outfile=None,
                        varianceimg=None,
                        stdimg=None,
                        meanimg=None,
                        parfile=None,
                        outmatfile=None)
        return outputs

    def aggregate_outputs(self):
        cwd = os.getcwd()

        outputs = self.outputs()
        # get basename (correct fsloutpputytpe extension)
        # We are generating outfile if it's not there already
        # if self.inputs.outfile:

        outputs.outfile = fsl_info.gen_fname(list_to_filename(self.inputs.infile),
                self.inputs.outfile, cwd=cwd, suffix='_mcf', check=True)

        # XXX Need to change 'item' below to something that exists
        # outfile? infile?
        # These could be handled similarly to default values for inputs
        if self.inputs.statsimgs:
            outputs.varianceimg = fsl_info.gen_fname(list_to_filename(self.inputs.infile),
                self.inputs.outfile, cwd=cwd, suffix='_variance', check=True)
            outputs.stdimg = fsl_info.gen_fname(list_to_filename(self.inputs.infile),
                self.inputs.outfile, cwd=cwd, suffix='_sigma', check=True)
            outputs.meanimg = fsl_info.gen_fname(list_to_filename(self.inputs.infile),
                self.inputs.outfile, cwd=cwd, suffix='_meanvol', check=True)
        if self.inputs.savemats:
            matnme, ext = os.path.splitext(list_to_filename(self.inputs.infile))
            matnme = matnme + '.mat'
            outputs.outmatfile = matnme
        if self.inputs.saveplots:
            # Note - if e.g. outfile has .nii.gz, you get .nii.gz.par, which is
            # what mcflirt does!
            outputs.parfile = outputs.outfile + '.par'
            if not os.path.exists(outputs.parfile):
                msg = "Output file '%s' for '%s' was not generated" \
                        % (outname, outtype)
                raise IOError(msg)
        return outputs


class Fnirt(FSLCommand):
    """Use FSL FNIRT for non-linear registration.

    For complete details, see the `FNIRT Documentation.
    <http://www.fmrib.ox.ac.uk/fsl/fnirt/index.html>`_

    To print out the command line help, use:
        fsl.Fnirt().inputs_help()

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> fnt = fsl.Fnirt(affine='affine.mat')
    >>> res = fnt.run(reference='ref.nii', infile='anat.nii') # doctests: +SKIP

    """
    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'fnirt'

    # Leaving this in place 'til we get round to a thread-safe version
    @property
    def cmdline(self):
        """validates fsl options and generates command line argument"""
        #self.update_optmap()
        allargs = self._parse_inputs()
        allargs.insert(0, self.cmd)
        return ' '.join(allargs)

    def inputs_help(self):
        """Print command line documentation for FNIRT."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    # XXX It's not clear if the '=' syntax (which is necessary for some
    # arguments) supports ' ' separated lists. We might need ',' separated lists
    opt_map = {
            'affine':           '--aff=%s',
            'initwarp':         '--inwarp=%s',
            'initintensity':    '--intin=%s',
            'configfile':       '--config=%s',
            'referencemask':    '--refmask=%s',
            'imagemask':        '--inmask=%s',
            'fieldcoeff_file':  '--cout=%s',
            'outimage':         '--iout=%s',
            'fieldfile':        '--fout=%s',
            'jacobianfile':     '--jout=%s',
            # XXX I think reffile is misleading / confusing
            'reffile':          '--refout=%s',
            'intensityfile':    '--intout=%s',
            'logfile':          '--logout=%s',
            'verbose':          '--verbose',
            'sub_sampling':     '--subsamp=%d',
            'max_iter':         '--miter=%d',
            'referencefwhm':    '--reffwhm=%d',
            'imgfwhm':          '--infwhm=%d',
            'lambdas':          '--lambda=%d',
            'estintensity':     '--estint=%s',
            'applyrefmask':     '--applyrefmask=%f',
            # XXX The closeness of this alternative name might cause serious
            # confusion
            'applyimgmask':      '--applyinmask=%f',
            'flags':            '%s',
            'infile':           '--in=%s',
            'reference':        '--ref=%s',
            }

    def run(self, infile=None, reference=None, **inputs):
        """Run the fnirt command

        Note: technically, only one of infile OR reference need be specified.

        You almost certainly want to start with a config file, such as
        T1_2_MNI152_2mm

        Parameters
        ----------
        infile : string
            Filename of the volume to be warped/moved.
        reference : string
            Filename of volume used as target for warp registration.
        inputs : dict
            Additional ``inputs`` assignments.

        Returns
        --------
        results : InterfaceResult
            An :class:`nipype.interfaces.base.InterfaceResult` object
            with a copy of self in `interface`

        Examples
        --------
        T1 -> Mni153

        >>> from nipype.interfaces import fsl
        >>> fnirt_mprage = fsl.Fnirt()
        >>> fnirt_mprage.inputs.imgfwhm = [8, 4, 2]
        >>> fnirt_mprage.inputs.sub_sampling = [4, 2, 1]

        Specify the resolution of the warps, currently not part of the
        ``fnirt_mprage.inputs``:

        >>> fnirt_mprage.inputs.flags = '--warpres 6, 6, 6'
        >>> res = fnirt_mprage.run(infile='subj.nii', reference='mni.nii')

        We can check the command line and confirm that it's what we expect.

        >>> fnirt_mprage.cmdline  #doctest: +NORMALIZE_WHITESPACE
        'fnirt --warpres 6, 6, 6 --infwhm=8,4,2 --in=subj.nii
            --ref=mni.nii --subsamp=4,2,1'

        """

        if infile:
            self.inputs.infile = infile
        if reference:
            self.inputs.reference = reference
        if self.inputs.reference is None and self.inputs.infile is None:
            raise AttributeError('Fnirt requires at least a reference' \
                                 'or input file.')
        self.inputs.update(**inputs)
        return super(Fnirt, self).run()

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

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        fieldcoeff_file
        warpedimage
        fieldfile
        jacobianfield
        modulatedreference
        intensitymodulation
        logfile
        """
        outputs = Bunch(fieldcoeff_file=None,
                        warpedimage=None,
                        fieldfile=None,
                        jacobianfield=None,
                        modulatedreference=None,
                        intensitymodulation=None,
                        logfile=None)
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object

        Raises
        ------
        IOError
             If the output file is not found.

        Notes
        -----
        For each item in the ``outputs``, if it's value is None then
        the optional file was not generated.  Otherwise it contains
        the path/filename of generated output file(s).

        """
        cwd = os.getcwd()
        outputs = self.outputs()

        # Note this is the only one that'll work with the pipeline code
        # currently
        if self.inputs.fieldcoeff_file:
            outputs.fieldcoeff_file = \
                    os.path.realpath(self.inputs.fieldcoeff_file)
        # the rest won't XX
        if self.inputs.outimage:
            # This should end with _warp
            outputs.warpedimage = self.inputs.outimage
        if self.inputs.fieldfile:
            outputs.fieldfile = self.inputs.fieldfile
        if self.inputs.jacobianfile:
            outputs.jacobianfield = self.inputs.jacobianfile
        if self.inputs.reffile:
            outputs.modulatedreference = self.inputs.reffile
        if self.inputs.intensityfile:
            outputs.intensitymodulation = self.inputs.intensityfile
        if self.inputs.logfile:
            outputs.logfile = self.inputs.logfile

        for item, file in outputs.iteritems():
            if file is not None:
                file = os.path.join(cwd, file)
                file = fsl_info.glob(file)
                if file is None:
                    raise IOError('file %s of type %s not generated'%(file,item))
                setattr(outputs, item, file)
        return outputs

class ApplyWarp(FSLCommand):
    '''Use FSL's applywarp to apply the results of a Fnirt registration

    Note how little actually needs to be done if we have truly order-independent
    arguments!
    '''
    @property
    def cmd(self):
        return 'applywarp'

    opt_map = {'infile':            '--in=%s',
               'outfile':           '--out=%s',
               'reference':         '--ref=%s',
               'fieldfile':          '--warp=%s',
               'premat':            '--premat=%s',
               'postmat':           '--postmat=%s',
              }

    def inputs_help(self):
        """Print command line documentation for applywarp."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def run(self, infile=None, outfile=None, reference=None,
            fieldfile=None, **inputs):
        '''Interesting point - you can use coeff_files, or fieldfiles
        interchangeably here'''
        def set_attr(name, value, error=True):
            if value is not None:
                setattr(self.inputs, name, value)
            if self.inputs.get(name) is None and error:
                raise AttributeError('applywarp requires %s' % name)

        # XXX Even this seems overly verbose
        set_attr('infile', infile)
        set_attr('outfile', outfile, error=False)
        set_attr('reference', reference)
        set_attr('fieldfile', fieldfile)

        self.inputs.update(**inputs)
        return super(ApplyWarp, self).run()

    def _parse_inputs(self):
        """Call our super-method, then add our input files"""
        allargs = super(ApplyWarp, self)._parse_inputs()
        if self.inputs.infile is not None:
            # XXX This currently happens twice, slightly differently
            if self.inputs.outfile is None:
                # XXX newpath could be cwd, but then we have to put it in inputs
                # or pass it to _parse_inputs (or similar).
                outfile = fname_presuffix(self.inputs.infile,
                                            suffix='_warp', newpath='.')
                allargs.append(self.opt_map['outfile'] % outfile)

        return allargs

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

             outfile
        """
        outputs = Bunch(outfile=None)
        return outputs

    def aggregate_outputs(self):
        outputs = self.outputs()
        outputs.outfile = fsl_info.gen_fname(self.inputs.infile,
                self.inputs.outfile, suffix='_warp', check=True)
        return outputs

class Smooth(FSLCommand):
    '''Use fslmaths to smooth the image

    This is dumb, of course - we should use nipy for such things! But it is a
    step along the way to get the "standard" FSL pipeline in place.

    This is meant to be a throwaway class, so it's not currently very robust.
    Effort would be better spent integrating basic numpy into nipype'''
    @property
    def cmd(self):
        return 'fslmaths'

    opt_map = {'infile':  None,
               'fwhm':    None,
               'outfile': None,
              }


    def _get_outfile(self, check=False):
        return fsl_info.gen_fname(self.inputs.infile,
                                  self.inputs.outfile,
                                  suffix='_smooth',
                                  check=check)
        
    def _parse_inputs(self):
        return [self.inputs.infile,
                # ohinds: convert fwhm to stddev
                '-kernel gauss', str(self.inputs.fwhm/2.3548), 
                '-fmean',
                self._get_outfile()]

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

             smoothedimage
        """
        outputs = Bunch(smoothedimage=None)
        return outputs

    def aggregate_outputs(self):
        outputs = self.outputs()
        outputs.smoothedimage = self._get_outfile(check=True)
        return outputs

class Merge(FSLCommand):
    """Use fslmerge to concatenate images
    """
    
    @property
    def cmd(self):
        return 'fslmerge'

    opt_map = {'infile':  None,
               'dimension':    None,
               'outfile': None,
              }

    def _get_outfile(self, check=False):
        return fsl_info.gen_fname(self.inputs.infile[0],
                                  self.inputs.outfile,
                                  suffix='_merged',
                                  check=check)
        
    def _parse_inputs(self):
        allargs =  [self.inputs.dimension,
                    self._get_outfile()]
        allargs.extend(self.inputs.infile)
        return allargs

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

             mergedimage
        """
        outputs = Bunch(mergedimage=None)
        return outputs

    def aggregate_outputs(self):
        outputs = self.outputs()
        outputs.mergedimage = self._get_outfile(check=True)
        return outputs

class Level1Design(Interface):
    """Generate Feat specific files

    See Level1Design().inputs_help() for more information.

    Parameters
    ----------
    inputs : mapping
    key, value pairs that will update the Level1Design.inputs attributes
    see self.inputs_help() for a list of Level1Design.inputs attributes

    Attributes
    ----------
    inputs : Bunch
    a (dictionary-like) bunch of options that can be passed to
    spm_smooth via a job structure
    cmdline : string
    string used to call matlab/spm via SpmMatlabCommandLine interface

    Other Parameters
    ----------------
    To see optional arguments
    Level1Design().inputs_help()

    Examples
    --------

    """

    def __init__(self, *args, **inputs):
        self._populate_inputs()
        self.inputs.update(**inputs)

    @property
    def cmd(self):
        return 'fsl_fmri_design'

    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        return []

    def inputs_help(self):
        """
        Parameters
        ----------

        interscan_interval : float (in secs)
            Interscan  interval,  TR.
        session_info : list of bunches
            Stores session specific information generated by
            ``modelgen.SpecifyModel`` 
        bases : dict {'name':{'basesparam1':val,...}}
            name : string
                Name of basis function (hrf - double gamma hrf)

                hrf :
                    derivs : boolean
                        Model  HRF  Derivatives.
        model_serial_correlations : string
            Option to model serial correlations using an
            autoregressive estimator. Setting this option is only
            useful in the context of the fsf file. You need to repeat
            this option for FilmGLS
        contrasts : list of dicts
            List of contrasts with each list containing: 'name', 'stat',
            [condition list], [weight list].
        register : boolean
            Run registration at the end of session specific analysis.
            default - True
        reg_image : file
            image volume to register to. default -
                    MNI152_T1_2mm_brain.nii.gz
        reg_dof : int
            registration degrees of freedom. default - 12
            
        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        """ Initializes the input fields of this interface.
        """
        self.inputs = Bunch(interscan_interval=None,
                            session_info=None,
                            bases=None,
                            model_serial_correlations=None,
                            contrasts=None,
                            register=True,
                            reg_image=None,
                            reg_dof=12)

    def _create_ev_file(self,evfname,evinfo):
        f = open(evfname,'wt')
        for i in evinfo:
            if len(i)==3:
                f.write('%f %f %f\n'%(i[0],i[1],i[2]))
            else:
                f.write('%f\n'%i[0])
        f.close()

    def _create_ev_files(self,cwd,runinfo,runidx,usetd,contrasts):
        """Creates EV files from condition and regressor information.

           Parameters:
           -----------

           runinfo : dict
               Generated by `SpecifyModel` and contains information
               about events and other regressors.
           runidx  : int
               Index to run number
           usetd   : int
               Whether or not to use temporal derivatives for
               conditions
           contrasts : list of lists
               Information on contrasts to be evaluated               
        """
        conds = {}
        evname = []
        ev_hrf  = load_template('feat_ev_hrf.tcl')
        ev_none   = load_template('feat_ev_none.tcl')
        ev_ortho  = load_template('feat_ev_ortho.tcl')
        contrast_header  = load_template('feat_contrast_header.tcl')
        contrast_prolog  = load_template('feat_contrast_prolog.tcl')
        contrast_element = load_template('feat_contrast_element.tcl')
        contrastmask_header  = load_template('feat_contrastmask_header.tcl')
        contrastmask_footer  = load_template('feat_contrastmask_footer.tcl')
        contrastmask_element = load_template('feat_contrastmask_element.tcl')
        ev_txt = ''
        # generate sections for conditions and other nuisance
        # regressors
        num_evs = [0,0]
        for field in ['cond','regress']:
            for i,cond in enumerate(runinfo[field]):
                name = cond['name']
                evname.append(name)
                evfname = os.path.join(cwd,'ev_%s_%d_%d.txt'%(name,runidx,len(evname)))
                evinfo = []
                num_evs[0] += 1
                num_evs[1] += 1
                if field == 'cond':
                    for j,onset in enumerate(cond['onset']):
                        if len(cond['duration'])>1:
                            evinfo.insert(j,[onset,cond['duration'][j],1])
                        else:
                            evinfo.insert(j,[onset,cond['duration'][0],1])
                    ev_txt += ev_hrf.substitute(ev_num=num_evs[0],
                                                ev_name=name,
                                                temporalderiv=usetd,
                                                cond_file=evfname)
                    if usetd:
                        evname.append(name+'TD')
                        num_evs[1] += 1
                elif field == 'regress':
                    evinfo = [[j] for j in cond['val']]
                    ev_txt += ev_none.substitute(ev_num=num_evs[0],
                                                 ev_name=name,
                                                 cond_file=evfname)
                ev_txt += "\n"
                conds[name] = evfname
                self._create_ev_file(evfname,evinfo)
        # add orthogonalization
        for i in range(1,num_evs[0]+1):
            for j in range(0,num_evs[0]+1):
                ev_txt += ev_ortho.substitute(c0=i,c1=j)
                ev_txt += "\n"
        # add t contrast info
        ev_txt += contrast_header.substitute()
        for ctype in ['real','orig']:
            for j,con in enumerate(contrasts):
                ev_txt += contrast_prolog.substitute(cnum=j+1,
                                                     ctype=ctype,
                                                     cname=con[0])
                count = 0
                for c in range(1,len(evname)+1):
                    if evname[c-1].endswith('TD') and ctype == 'orig':
                        continue
                    count = count+1
                    if evname[c-1] in con[2]:
                        val = con[3][con[2].index(evname[c-1])]
                    else:
                        val = 0.0
                    ev_txt += contrast_element.substitute(cnum=j+1, element=count,
                                                          ctype=ctype, val=val)
                    ev_txt += "\n"
        # add contrast mask info
        ev_txt += contrastmask_header.substitute()
        for j,con1 in enumerate(contrasts):
            for k,con2 in enumerate(contrasts):
                if j != k:
                    ev_txt += contrastmask_element.substitute(c1=j+1,
                                                              c2=k+1)
        ev_txt += contrastmask_footer.substitute()
        return num_evs,ev_txt

    def run(self, **inputs):
        cwd = os.getcwd()
        self.inputs.update(inputs)
        fsf_header    = load_template('feat_header_l1.tcl')
        fsf_postscript= load_template('feat_nongui.tcl')

        prewhiten = int(self.inputs.model_serial_correlations == 'AR(1)')
        if self.inputs.bases and self.inputs.bases.has_key('hrf'):
            usetd = int(self.inputs.bases['hrf']['derivs'])
        else:
            usetd = 0
        session_info = self._get_session_info(self.inputs.session_info)
        func_files = self._get_func_files(session_info)

        n_tcon = 0
        n_fcon = 0
        for i,c in enumerate(self.inputs.contrasts):
            if c[1] == 'T':
                n_tcon+=1
            elif c[1] == 'F':
                n_fcon+=1
            else:
                print "unknown contrast type: %s"%str(c)
        print [n_tcon, n_fcon]

        register = int(self.inputs.register)
        if register:
            reg_image = self.inputs.reg_image
            if not reg_image:
                reg_image = fsl_info.standard_image('MNI152_T1_2mm_brain.nii.gz')
        reg_dof = self.inputs.reg_dof
        for i,info in enumerate(session_info):
            num_evs,cond_txt  = self._create_ev_files(cwd,info,i,usetd,self.inputs.contrasts)
            nim = load(func_files[i])
            (x,y,z,timepoints) = nim.get_shape()
            fsf_txt = fsf_header.substitute(run_num=i,
                                            interscan_interval=self.inputs.interscan_interval,
                                            num_vols=timepoints,
                                            prewhiten=prewhiten,
                                            num_evs=num_evs[0],
                                            num_evs_real=num_evs[1],
                                            num_tcon=n_tcon,
                                            num_fcon=n_fcon,
                                            high_pass_filter_cutoff=info['hpf'],
                                            func_file=func_files[i],
                                            register=register,
                                            reg_image=reg_image,
                                            reg_dof=reg_dof)
            fsf_txt += cond_txt
            fsf_txt += fsf_postscript.substitute(overwrite=1)

            f = open(os.path.join(cwd, 'run%d.fsf' % i), 'w')
            f.write(fsf_txt)
            f.close()

        runtime = Bunch(returncode=0,
                        messages=None,
                        errmessages=None)
        outputs=self.aggregate_outputs()
        return InterfaceResult(deepcopy(self), runtime, outputs=outputs)

    def _get_session_info(self, session_info_file):
        key = 'session_info'
        data = loadflat(session_info_file)
        session_info = data[key]
        if isinstance(session_info,dict):
            session_info = [session_info]
        return session_info
        
    def _get_func_files(self, session_info):
        """Returns functional files in the order of runs
        """
        func_files = []
        for i,info in enumerate(session_info):
            func_files.insert(i, info['scans'][0].split(',')[0])
        return func_files

    def outputs_help(self):
        """
        """
        print self.outputs.__doc__

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            fsf_files:
                FSL feat specification files
            func_files:
                Functional run files
            ev_files:
                condition information files
        """
        outputs = Bunch(fsf_files=None,
                        func_files=None,
                        ev_files=None)
        return outputs

    def aggregate_outputs(self):
        outputs = self.outputs()
        session_info = self._get_session_info(self.inputs.session_info)
        func_files = self._get_func_files(session_info)
        outputs.fsf_files = glob(os.path.abspath(os.path.join(os.getcwd(),'run*.fsf')))
        outputs.func_files = func_files
        outputs.ev_files  = glob(os.path.abspath(os.path.join(os.getcwd(),'ev_*.txt')))
        return outputs

# satra: 2010-01-03
class Feat(FSLCommand):
    """Uses FSL feat to calculate first level stats
    """
    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'feat'

    opt_map = {
        'fsf_file':         None,
        }

    def inputs_help(self):
        """Print command line documentation for feat_model."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def _parse_inputs(self):
        """validate fsl feat_model options"""
        allargs = super(Feat, self)._parse_inputs(skip=('fsf_file'))

        if self.inputs.fsf_file:
            allargs.insert(0, self.inputs.fsf_file)
        return allargs

    def run(self, fsf_file=None, **inputs):
        """Execute the command.

        Parameters
        ----------
        fsf_file : string
            File specifying the feat design spec file

        Returns
        -------
        results : InterfaceResult
            An :class:`nipype.interfaces.base.InterfaceResult` object
            with a copy of self in `interface`

        Examples
        --------
        To pass command line arguments to ``feat_model`` that are not part of
        the ``inputs`` attribute, pass them in with the ``flags``
        input.

        >>> from nipype.interfaces import fsl
        >>> fmodel = fsl.FeatModel(fsf_file='foo.fsf')
        """
        if fsf_file:
            self.inputs.fsf_file = fsf_file
        if not self.inputs.fsf_file:
            raise ValueError('FeatModel requires an input file')
        if isinstance(self.inputs.fsf_file, list):
            raise ValueError('FeatModel does not support multiple input files')
        self.inputs.update(**inputs)
        return super(Feat, self).run()

    def outputs(self):
        """
            Parameters
            ----------
            (all default to None)

            statsdir:
                Directory containing the output of feat
        """
        outputs = Bunch(featdir=None)
        return outputs
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        outputs.featdir = glob(os.path.join(os.getcwd(),'*feat'))[0]
        return outputs

# interface to fsl command line model generation routine
# satra: 2010-01-03
class FeatModel(FSLCommand):
    """Uses FSL feat_model to generate design.mat files
    """
    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'feat_model'

    opt_map = {
        'fsf_file':         None,
        }

    def inputs_help(self):
        """Print command line documentation for feat_model."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def _parse_inputs(self):
        """validate fsl feat_model options"""
        allargs = super(FeatModel, self)._parse_inputs(skip=('fsf_file'))

        if self.inputs.fsf_file:
            allargs.insert(0, self._get_design_root(list_to_filename(self.inputs.fsf_file)))
        return allargs

    def _get_design_root(self, infile):
        path,fname = os.path.split(infile)
        return fname.split('.')[0]
        
    def run(self, fsf_file=None, **inputs):
        """Execute the command.

        Parameters
        ----------
        fsf_file : string
            File specifying the feat design spec file

        Returns
        -------
        results : InterfaceResult
            An :class:`nipype.interfaces.base.InterfaceResult` object
            with a copy of self in `interface`

        Examples
        --------
        To pass command line arguments to ``feat_model`` that are not part of
        the ``inputs`` attribute, pass them in with the ``flags``
        input.

        >>> from nipype.interfaces import fsl
        >>> fmodel = fsl.FeatModel(fsf_file='foo.fsf')
        """
        if fsf_file:
            self.inputs.fsf_file = fsf_file
        if not self.inputs.fsf_file:
            raise ValueError('FeatModel requires an input file')
        if isinstance(self.inputs.fsf_file, list):
            raise ValueError('FeatModel does not support multiple input files')
        self.inputs.update(**inputs)
        return super(FeatModel, self).run()

    def outputs(self):
        """
            Parameters
            ----------
            (all default to None)

            designfile:
                Mat file containing ascii matrix for design
            confile:
                Contrast file containing contrast vectors
        """
        outputs = Bunch(designfile=None,
                        confile=None)
        return outputs
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        root = self._get_design_root(list_to_filename(self.inputs.fsf_file))
        designfile = glob(os.path.join(os.getcwd(),'%s*.mat'%root))
        assert len(designfile) == 1, 'No mat file generated by Feat Model'
        outputs.designfile = designfile[0]
        confile = glob(os.path.join(os.getcwd(),'%s*.con'%root))
        assert len(confile) == 1, 'No con file generated by Feat Model'
        outputs.confile = confile[0]
        return outputs
    
# interface to fsl command line model fit routines
# ohinds: 2009-12-28
class FilmGLS(FSLCommand):
    """Use FSL film_gls command to fit a design matrix to voxel timeseries

    To print out the command line help, use:
        fsl.FilmGLS().inputs_help()

    Examples
    --------
    Initialize Bet with no options, assigning them when calling run:

    >>> from nipype.interfaces import fsl
    >>> fgls = fsl.FilmGLS()
    >>> res = fgls.run('infile', 'designfile', 'thresh', rn='stats')

    Assign options through the ``inputs`` attribute:

    >>> fgls = fsl.FilmGLS()
    >>> fgls.inputs.infile = 'filtered_func_data'
    >>> fgls.inputs.designfile = 'design.mat'
    >>> fgls.inputs.thresh = 10
    >>> fgls.inputs.rn = 'stats'
    >>> res = fgls.run()

    Specify options when creating an instance:

    >>> fgls = fsl.FilmGLS(infile='filtered_func_data', \
                           designfile='design.mat', \
                           thresh=10, rn='stats')
    >>> res = fgls.run()

    """

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'film_gls'

    opt_map = {
        'sa':             '-sa',
        'ms':             '-ms %d',
        'epith':          '-epith %d',
        'v':              '-v',
        'ac':             '-ac',
        'ar':             '-ar',
        'tukey':          '-tukey %d',
        'mt':             '-mt %d',
        'pava':           '-pava',
        'noest':          '-noest',
        'output_pwdata':  '-output_pwdata',
        'rn':             '-rn %s',
        'infile':         None,
        'designfile':     None,
        'thresh':         None,
        }
    # Currently we don't support -ven, -vef

    def inputs_help(self):
        """Print command line documentation for film_gls."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def _parse_inputs(self):
        """validate fsl film_gls options"""
        allargs = super(FilmGLS, self)._parse_inputs(skip=('infile',
                                                           'designfile',
                                                           'thresh'))

        # special defaults
        if not self.inputs.rn:
            allargs.append("-rn %s"%self._get_statsdir())

        if self.inputs.infile:
            allargs.append(list_to_filename(self.inputs.infile))

        if self.inputs.designfile:
            allargs.append(list_to_filename(self.inputs.designfile))

        if self.inputs.thresh:
            allargs.append(str(self.inputs.thresh))
        else:
            allargs.append('1000')

        return allargs

    def _get_statsdir(self):
        statsdir = self.inputs.rn
        if not statsdir:
            path,name = os.path.split(list_to_filename(self.inputs.designfile))
            statsdir = '.'.join((os.path.splitext(name)[0],'stats'))
        return statsdir
        
    def run(self, infile=None, designfile=None, thresh=None, **inputs):
        """Execute the command.

        Parameters
        ----------
        infile : string
            File specifying the functional data to be fit
        designfile : string
            File specifying design matrix
        thresh : float
            Some sort of threshold, not even sure this is used?

        inputs : dict
            Additional ``inputs`` assignments can be passed in.  See
            Examples section.

        Returns
        -------
        results : InterfaceResult
            An :class:`nipype.interfaces.base.InterfaceResult` object
            with a copy of self in `interface`

        Examples
        --------
        To pass command line arguments to ``film_gls`` that are not part of
        the ``inputs`` attribute, pass them in with the ``flags``
        input.

        >>> from nipype.interfaces import fsl
        >>> import os
        >>> fgls = fsl.FilmGLS(infile='foo.nii', \
                               designfile='design.mat', \
                               thresh=10, \
                               flags='-ven')
        """
        if infile:
            self.inputs.infile = infile
        if self.inputs.infile is None:
            raise ValueError('FilmGLS requires an input file')
        if isinstance(self.inputs.infile, list):
            raise ValueError('FilmGLS does not support multiple input files')
        if designfile:
            self.inputs.designfile = designfile
        if self.inputs.designfile is None:
            raise ValueError('FilmGLS requires a design file')
        if isinstance(self.inputs.designfile, list):
            raise ValueError('FilmGLS does not support multiple design files')
        if thresh:
            self.inputs.thresh = thresh
        self.inputs.update(**inputs)
        cwd = os.getcwd()
        statsdir = self._get_statsdir()
        if os.access(os.path.join(cwd, statsdir), os.F_OK):
            rmtree(os.path.join(cwd, statsdir))
        return super(FilmGLS, self).run()

    def outputs(self):
        """
            Parameters
            ----------
            (all default to None)

            pes:
                Parameter estimates for each column of the design matrix
                for each voxel
            res4d:
                Model fit residual mean-squared error for each time point
            dof:
                degrees of freedom
            sigmasquareds:
                See Woolrich, et. al., 2001
            statsdir :
                directory storing model estimation output
        """
        outputs = Bunch(pes=None,
                        res4d=None,
                        dof=None,
                        sigmasquareds=None,
                        statsdir=None)
        return outputs
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        pth = os.path.join(os.getcwd(), self._get_statsdir())

        pes = glob(os.path.join(pth,'pe[0-9]*.*'))
        assert len(pes) >= 1, 'No pe volumes generated by FSL Estimate'
        outputs.pes = pes
        
        res4d = glob(os.path.join(pth,'res4d.*'))
        assert len(res4d) == 1, 'No residual volume generated by FSL Estimate'
        outputs.res4d = res4d[0]
        
        dof = glob(os.path.join(pth,'dof'))
        assert len(dof) == 1, 'No degrees of freedom files generated by FSL Estimate'
        outputs.dof = dof

        sigmasquareds = glob(os.path.join(pth,'sigmasquareds.*'))
        assert len(sigmasquareds) == 1, 'No sigmasquareds volume generated by FSL Estimate'
        outputs.sigmasquareds = sigmasquareds[0];

        outputs.statsdir = os.path.join(os.getcwd(),self._get_statsdir())

        return outputs

# satra: 2010-01-23
class FixedEffectsModel(Interface):
    """Generate Feat specific files

    See FixedEffectsModel().inputs_help() for more information.

    Parameters
    ----------
    inputs : mapping
    key, value pairs that will update the FixedEffectsModel.inputs attributes
    see self.inputs_help() for a list of FixedEffectsModel.inputs attributes

    Attributes
    ----------
    inputs : Bunch
    a (dictionary-like) bunch of options that can be passed to
    spm_smooth via a job structure
    cmdline : string
    string used to call matlab/spm via SpmMatlabCommandLine interface

    Other Parameters
    ----------------
    To see optional arguments
    FixedEffectsModel().inputs_help()

    Examples
    --------

    """

    def __init__(self, *args, **inputs):
        self._populate_inputs()
        self.inputs.update(**inputs)

    @property
    def cmd(self):
        return 'feat_fe_design'

    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        return []

    def inputs_help(self):
        """
        Parameters
        ----------

        feat_dirs : list of directory names
            Lower level feat dirs
        num_copes : int
            number of copes evaluated in each session
        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        """ Initializes the input fields of this interface.
        """
        self.inputs = Bunch(feat_dirs=None,
                            num_copes=None
                            )

    def run(self, **inputs):
        self.inputs.update(inputs)
        fsf_header = load_template('feat_fe_header.tcl')
        fsf_footer = load_template('feat_fe_footer.tcl')
        fsf_copes = load_template('feat_fe_copes.tcl')
        fsf_dirs = load_template('feat_fe_featdirs.tcl')
        fsf_ev_header = load_template('feat_fe_ev_header.tcl')
        fsf_ev_element = load_template('feat_fe_ev_element.tcl')

        num_runs = len(filename_to_list(self.inputs.feat_dirs))
        fsf_txt = fsf_header.substitute(num_runs=num_runs,
                                        num_copes=self.inputs.num_copes)
        for i in range(self.inputs.num_copes):
            fsf_txt += fsf_copes.substitute(copeno = i+1)
        for i, rundir in enumerate(filename_to_list(self.inputs.feat_dirs)):
            fsf_txt += fsf_dirs.substitute(runno = i+1,
                                           rundir = os.path.abspath(rundir))
        fsf_txt += fsf_ev_header.substitute()
        for i in range(1,num_runs+1):
            fsf_txt += fsf_ev_element.substitute(input = i)
        fsf_txt += fsf_footer.substitute(overwrite=1)
        
        f = open(os.path.join(os.getcwd(), 'fixedeffects.fsf'), 'wt')
        f.write(fsf_txt)
        f.close()

        runtime = Bunch(returncode=0,
                        messages=None,
                        errmessages=None)
        outputs=self.aggregate_outputs()
        return InterfaceResult(deepcopy(self), runtime, outputs=outputs)

    def outputs_help(self):
        """
        """
        print self.outputs.__doc__

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            fsf_file:
                FSL feat specification file
        """
        outputs = Bunch(fsf_file=None)
        return outputs

    def aggregate_outputs(self):
        outputs = self.outputs()
        outputs.fsf_file = glob(os.path.abspath(os.path.join(os.getcwd(),'fixed*.fsf')))[0]
        return outputs

# satra: 2010-01-23
class FeatRegister(Interface):
    """Generate Feat specific files

    See FixedEffectsModel().inputs_help() for more information.

    Parameters
    ----------
    inputs : mapping
    key, value pairs that will update the FixedEffectsModel.inputs attributes
    see self.inputs_help() for a list of FixedEffectsModel.inputs attributes

    Attributes
    ----------
    inputs : Bunch
    a (dictionary-like) bunch of options that can be passed to
    spm_smooth via a job structure
    cmdline : string
    string used to call matlab/spm via SpmMatlabCommandLine interface

    Other Parameters
    ----------------
    To see optional arguments
    FixedEffectsModel().inputs_help()

    Examples
    --------

    """

    def __init__(self, *args, **inputs):
        self._populate_inputs()
        self.inputs.update(**inputs)

    @property
    def cmd(self):
        return 'feat_register'

    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        return []

    def inputs_help(self):
        """
        Parameters
        ----------

        feat_dirs : list of directory names
            Lower level feat dirs
        reg_image : file
            image to register to (will be treated as standard)
        reg_dof : int
            registration degrees of freedom [ default : 12 ]
        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        """ Initializes the input fields of this interface.
        """
        self.inputs = Bunch(feat_dirs=None,
                            reg_image=None,
                            reg_dof=12)

    def run(self, **inputs):
        self.inputs.update(inputs)
        fsf_header = load_template('featreg_header.tcl')
        fsf_footer = load_template('feat_nongui.tcl')
        fsf_dirs = load_template('feat_fe_featdirs.tcl')

        num_runs = len(filename_to_list(self.inputs.feat_dirs))
        fsf_txt = fsf_header.substitute(num_runs=num_runs,
                                        regimage=self.inputs.reg_image,
                                        regdof=self.inputs.reg_dof)
        for i, rundir in enumerate(filename_to_list(self.inputs.feat_dirs)):
            fsf_txt += fsf_dirs.substitute(runno = i+1,
                                           rundir = os.path.abspath(rundir))
        f = open(os.path.join(os.getcwd(), 'register.fsf'), 'wt')
        f.write(fsf_txt)
        f.close()

        runtime = Bunch(returncode=0,
                        messages=None,
                        errmessages=None)
        outputs=self.aggregate_outputs()
        return InterfaceResult(deepcopy(self), runtime, outputs=outputs)

    def outputs_help(self):
        """
        """
        print self.outputs.__doc__

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            fsf_file:
                FSL feat specification file
        """
        outputs = Bunch(fsf_file=None)
        return outputs

    def aggregate_outputs(self):
        outputs = self.outputs()
        outputs.fsf_files = glob(os.path.abspath(os.path.join(os.getcwd(),'reg*.fsf')))
        return outputs


# interface to fsl command line higher level model fit
# satra: 2010-01-09
class Flameo(FSLCommand):
    """Use FSL flameo command to perform higher level model fits

    To print out the command line help, use:
        fsl.Flameo().inputs_help()

    Examples
    --------
    Initialize Flameo with no options, assigning them when calling run:

    >>> from nipype.interfaces import fsl
    >>> flame = fsl.Flameo()
    >>> res = flame.run()

    >>> from nipype.interfaces import fsl
    >>> import os
    >>> flameo = fsl.Flameo(copefile='cope.nii.gz', \
                            varcopefile='varcope.nii.gz', \
                            designfile='design.mat', \
                            tconfile='design.con', \
                            runmode='fe')
    >>> flameo.cmdline
    'flameo --copefile=cope.nii.gz --designfile=design.mat --runmode=fe --tcontrastsfile=design.con --varcopefile=varcope.nii.gz'
    
    """

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'flameo'

    opt_map = {
        'copefile':       '--copefile=%s',
        'varcopefile':    '--varcopefile=%s',
        'dofvarcopefile': '--dofvarcopefile=%s',
        'maskfile':       '--maskfile=%s',
        'designfile':     '--designfile=%s',
        'tconfile':       '--tcontrastsfile=%s',
        'fconfile':       '--fcontrastsfile=%s',
        'covsplitfile':   '--covsplitfile=%s',
        'runmode':        '--runmode=%s',
        'njumps':         '--njumps=%d',
        'burnin':         '--burnin=%d',
        'sampleevery':    '--sampleevery=%d',
        'fixmean':        '--fixmean',
        'inferoutliers':  '--inferoutliers',
        'nopeoutput':     '--nopeoutput',
        'modelselect':    '--msm=%s',
        'sigma_dofs':     '--sigma_dofs=%s',
        'outlier_iter':   '--ioni=%d',
        'flags':          '%s'
        }
        # no support for ven, vef

    def inputs_help(self):
        """Print command line documentation for flameo."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def outputs(self):
        """
            Parameters
            ----------
            (all default to None)
            pes:
                Parameter estimates for each column of the design matrix
                for each voxel
            varcopes:
                Variance estimates
            res4d:
                Model fit residual mean-squared error for each time point
            dof:
                degrees of freedom
            copes:
                Contrast estimates for each contrast
            varcopes:
                Variance estimates for each contrast
            zstats:
                z-stat file for each contrast
            tstats:
                t-stat file for each contrast
            neff:
                neff file??
            statsdir :
                directory storing model estimation output
        """
        outputs = Bunch(pes=None,
                        res4d=None,
                        dof=None,
                        copes=None,
                        varcopes=None,
                        zstats=None,
                        tstats=None,
                        neffs=None,
                        statsdir=None)
        return outputs
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        pth = os.getcwd()

        pes = glob(os.path.join(pth,'pe[0-9]*.*'))
        assert len(pes) >= 1, 'No pe volumes generated by FSL Estimate'
        outputs.pes = pes
        
        res4d = glob(os.path.join(pth,'res4d.*'))
        assert len(res4d) == 1, 'No residual volume generated by FSL Estimate'
        outputs.res4d = res4d[0]
        
        dof = glob(os.path.join(pth,'dof'))
        assert len(dof) == 1, 'No degrees of freedom files generated by FSL Estimate'
        outputs.dof = dof

        copes = glob(os.path.join(pth,'cope[0-9]*.*'))
        assert len(copes) >= 1, 'No cope volumes generated by FSL CEstimate'
        outputs.copes = copes

        varcopes = glob(os.path.join(pth,'varcope[0-9]*.*'))
        assert len(varcopes) >= 1, 'No varcope volumes generated by FSL CEstimate'
        outputs.varcopes = varcopes

        zstats = glob(os.path.join(pth,'zstat[0-9]*.*'))
        assert len(zstats) >= 1, 'No zstat volumes generated by FSL CEstimate'
        outputs.zstats = zstats

        tstats = glob(os.path.join(pth,'tstat[0-9]*.*'))
        assert len(tstats) >= 1, 'No tstat volumes generated by FSL CEstimate'
        outputs.tstats = tstats

        neffs = glob(os.path.join(pth,'neff[0-9]*.*'))
        assert len(neffs) >= 1, 'No neff volumes generated by FSL CEstimate'
        outputs.neffs = neffs
        
        outputs.statsdir = pth

        return outputs


class ContrastMgr(FSLCommand):
    """Use FSL contrast_mgr command to evaluate contrasts

    To print out the command line help, use:
        fsl.ContrastMgr().inputs_help()

    Examples
    --------
    """

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'contrast_mgr'

    opt_map = {
        'tconfile':      None,
        'fconfile':      '-f %a', 
        'statsdir':       None,
        'cope':          '-cope %d',
        'suffix':        '-suffix %s',
        }

    def inputs_help(self):
        """Print command line documentation for film_gls."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def _parse_inputs(self):
        """validate fsl contrast_mgr options"""
        allargs = super(ContrastMgr, self)._parse_inputs(skip=('tconfile',
                                                               'statsdir',))
        if self.inputs.statsdir:
            allargs.append(list_to_filename(self.inputs.statsdir))
        else:
            raise Exception('statsdir is mandatory')
        if self.inputs.tconfile:
            allargs.append(list_to_filename(self.inputs.tconfile))
        else:
            raise Exception('tconfile is mandatory')
        return allargs

    def run(self, tconfile=None, statsdir=None, **inputs):
        """Execute the command.

        Parameters
        ----------
        tconfile : file
            contrast specification file generated by FeatModel
        statsdir : directory
            directory containing model fit data
        inputs : dict
            Additional ``inputs`` assignments can be passed in.  See
            Examples section.

        Returns
        -------
        results : InterfaceResult
            An :class:`nipype.interfaces.base.InterfaceResult` object
            with a copy of self in `interface`

        Examples
        --------

        >>> from nipype.interfaces import fsl
        >>> import os
        >>> fgls = fsl.ContrastMgr(statsdir='stats',tconfile='run0.con')
        >>> fgls.cmdline
        'contrast_mgr stats run0.con'
        
        """
        if tconfile:
            self.inputs.tconfile = tconfile
        if not self.inputs.tconfile:
            raise ValueError('ContrastMgr requires an tconfile')
        if isinstance(self.inputs.tconfile, list):
            raise ValueError('ContrastMgr does not support multiple tcon files')
        if statsdir:
            self.inputs.statsdir = statsdir
        if not self.inputs.statsdir:
            raise ValueError('ContrastMgr requires a statsdir')
        if isinstance(self.inputs.statsdir, list):
            raise ValueError('ContrastMgr does not support multiple statsdirs')
        self.inputs.update(**inputs)
        return super(ContrastMgr, self).run()

    def outputs(self):
        """
            Parameters
            ----------
            (all default to None)

            copes:
                Contrast estimates for each contrast
            varcopes:
                Variance estimates for each contrast
            zstats:
                z-stat file for each contrast
            tstats:
                t-stat file for each contrast
            neff:
                neff file??
            statsdir :
                directory storing model estimation output
        """
        outputs = Bunch(copes=None,
                        varcopes=None,
                        zstats=None,
                        tstats=None,
                        neffs=None,
                        statsdir=None)
        return outputs
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        pth = self.inputs.statsdir

        copes = glob(os.path.join(pth,'cope[0-9]*.*'))
        assert len(copes) >= 1, 'No cope volumes generated by FSL CEstimate'
        outputs.copes = copes

        varcopes = glob(os.path.join(pth,'varcope[0-9]*.*'))
        assert len(varcopes) >= 1, 'No varcope volumes generated by FSL CEstimate'
        outputs.varcopes = varcopes

        zstats = glob(os.path.join(pth,'zstat[0-9]*.*'))
        assert len(zstats) >= 1, 'No zstat volumes generated by FSL CEstimate'
        outputs.zstats = zstats

        tstats = glob(os.path.join(pth,'tstat[0-9]*.*'))
        assert len(tstats) >= 1, 'No tstat volumes generated by FSL CEstimate'
        outputs.tstats = tstats

        neffs = glob(os.path.join(pth,'neff[0-9]*.*'))
        assert len(neffs) >= 1, 'No neff volumes generated by FSL CEstimate'
        outputs.neffs = neffs
        
        outputs.statsdir = self.inputs.statsdir
        
        return outputs


class ExtractRoi(FSLCommand):
    """Uses FSL Fslroi command to extract region of interest (ROI) from an image.
    You can a) take a 3D ROI from a 3D data set (or if it is 4D, the same ROI is taken
    from each time point and a new 4D data set is created), b) extract just some
    time points from a 4D data set, or c) control time and space limits to the ROI.
    Note that the arguments are minimum index and size (not maximum index).
    So to extract voxels 10 to 12 inclusive you would specify 10 and 3 (not 10 and 12).
    """
    opt_map={}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'fslroi'

    def inputs_help(self):
        """Print command line documentation for fslroi."""
        print get_doc(self.cmd,self.opt_map,trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(infile=None,
                            outfile=None,
                            xmin=None,
                            xsize=None,
                            ymin=None,
                            ysize=None,
                            zmin=None,
                            zsize=None,
                            tmin=None,
                            tsize=None)

    def _parse_inputs(self):
        """validate fsl fslroi options"""

        allargs=[]
        # Add infile and outfile to the args if they are specified
        if self.inputs.infile:
            allargs.insert(0, self.inputs.infile)
            outfile = fsl_info.gen_fname(self.inputs.infile,
                                         self.inputs.outfile,
                                         suffix='_roi')
            allargs.insert(1, outfile)

        #concat all numeric variables into a string separated by space given the user's option
        dim = [ self.inputs.xmin,self.inputs.xsize,self.inputs.ymin,self.inputs.ysize,
                self.inputs.zmin,self.inputs.zsize,self.inputs.tmin,self.inputs.tsize]
        args=[]
        for num in dim:
            if num is not None:
                args.append(repr(num))

        allargs.insert(2,' '.join(args))

        return allargs

    def run(self, infile=None, outfile=None, **inputs):
        """Execute the command.
        >>> from nipype.interfaces import fsl
        >>> fslroi = fsl.Fslroi(infile='foo.nii', outfile='bar.nii', tmin=0, tsize=1)
        >>> fslroi.cmdline
        'fslroi foo.nii bar.nii 0 1'

        """

        if infile:
            self.inputs.infile = infile
        if not self.inputs.infile:
            raise AttributeError('fslroi requires an input file')
        if outfile:
            self.inputs.outfile = outfile
        self.inputs.update(**inputs)
        return super(ExtractRoi, self).run()

    def outputs_help(self):
        """
        Parameters
        ----------
        (all default to None and are unset)

        outfile : /path/to/outfile
            path and filename of resulting file with desired ROI
        """
        print self.outputs_help.__doc__

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string,file
                path/name of file with ROI extracted
        """
        outputs = Bunch(outfile=None)
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        outputs = self.outputs()
        outputs.outfile = fsl_info.gen_fname(self.inputs.infile,
                                self.inputs.outfile, suffix='_roi', check=True)
        return outputs



#-------------------------------------------------------------------------------------------------------
class Split(FSLCommand):
    """Uses FSL Fslsplit command to split a 4D file into a series of 3D files.
    """
    opt_map={}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'fslsplit'

    def inputs_help(self):
        """Print command line documentation for fslsplit."""
        print get_doc(self.cmd,self.opt_map,trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(infile=None)

    def _parse_inputs(self):
        """validate fsl fslroi options"""
        
        allargs = super(Split, self)._parse_inputs(skip=('infile'))
        # Add infile and outfile to the args if they are specified
        if isinstance(self.inputs.infile, list):
            self.inputs.infile = self.inputs.infile[0]
        if self.inputs.infile:
            allargs.insert(0, self.inputs.infile)
            
        allargs.insert(1, '-t')

        return allargs

    def run(self, infile=None, outfile=None, **inputs):
        """Execute the command.
        >>> from nipype.interfaces import fsl
        >>> fslsplit = fsl.FSLSplit(infile='foo.nii')
        >>> fslsplit.cmdline
        'fslsplit foo.nii -t'

        """

        if infile:
            self.inputs.infile = infile
        if not self.inputs.infile:
            raise AttributeError('fslsplit requires an input file')
        self.inputs.update(**inputs)
        return super(Split, self).run()

    def outputs_help(self):
        """
        Parameters
        ----------
        (all default to None and are unset)

        outfiles : /path/to/outfile
            path/name of files with 3D volumes
        """
        print self.outputs_help.__doc__

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfiles : string,file
                path/name of files with 3D volumes
        """
        outputs = Bunch(outfiles=None)
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        outputs = self.outputs()
        type, ext = fsl_info.outputtype()
        outputs.outfiles = sorted(glob(os.path.join(os.getcwd(),'vol*.' + ext)))
        return outputs

class EddyCorrect(FSLCommand):
    """Use FSL eddy_correct command for correction of eddy current distortion
    """
    opt_map ={}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'eddy_correct'

    def inputs_help(self):
        """Print command line documentation for eddy_correct."""
        print get_doc(self.cmd,self.opt_map,trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(infile=None,outfile=None,reference_vol=None)

    def _parse_inputs(self):
        """validate fsl eddy_correct options"""

        # Add infile and outfile to the args if they are specified
        allargs=[]
        if self.inputs.infile:
            allargs.insert(0, self.inputs.infile)
            if not self.inputs.outfile:
                # If the outfile is not specified but the infile is,
                # generate an outfile
                pth, fname = os.path.split(self.inputs.infile)
                newpath=os.getcwd()
                self.inputs.outfile = fname_presuffix(fname, suffix='_eddc',
                                                      newpath=newpath)
        if self.inputs.outfile:
            allargs.insert(1, self.inputs.outfile)

        if self.inputs.reference_vol:
            allargs.insert(2, repr(self.inputs.reference_vol))

        return allargs

    def run(self, infile=None, outfile=None, **inputs):
        """Execute the command.
        >>> from nipype.interfaces import fsl
        >>> edd = fsl.Eddy_correct(infile='foo.nii', outfile='bar.nii', reference_vol=10)
        >>> edd.cmdline
        'eddy_correct foo.nii bar.nii 10'

        """

        if infile:
            self.inputs.infile = infile
        if not self.inputs.infile:
            raise AttributeError('Eddy_correct requires an input file')
        if outfile:
            self.inputs.outfile = outfile
        self.inputs.update(**inputs)
        return super(EddyCorrect, self).run()

    def outputs_help(self):
        """
        Parameters
        ----------
        (all default to None and are unset)

        outfile : /path/to/outfile
            filename of resulting eddy current corrected file
        """
        print self.outputs_help.__doc__

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string,file
                path/name of file of eddy-corrected image
        """
        outputs = Bunch(outfile=None)
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        outputs = self.outputs()
        if self.inputs.outfile:
            outfile = self.inputs.outfile
        else:
            pth,fname = os.path.split(self.inputs.infile)
            outfile = os.path.join(os.getcwd(),
                                   fname_presuffix(fname,suffix='_eddc'))

        if len(glob(outfile))==1:
            outputs.outfile = outfile

        return outputs



#----------------------------------------------------------------------------------------------------

class Bedpostx(FSLCommand):
    """ Use FSL  bedpostx command for local modelling of diffusion parameters
    """

    opt_map = {
        'fibres':               '-n %d',
        'weight':               '-w %.2f',
        'burn_period':          '-b %d',
        'jumps':                '-j %d',
        'sampling':             '-s %d'}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'bedpostx'

    def inputs_help(self):
        """Print command line documentation for eddy_correct."""
        print get_doc(self.cmd,self.opt_map,trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(directory=None,
                            fibres=None,
                            weight=None,
                            burn_period=None,
                            jumps=None,
                            sampling=None)

    def _parse_inputs(self):
        """validate fsl bedpostx options"""
        allargs = super(Bedpostx,self)._parse_inputs(skip=('directory'))

        # Add directory to the args if they are specified
        if self.inputs.directory:
            allargs.insert(0,self.inputs.directory)
        else:
            raise AttributeError('Bedpostx requires a directory \
                                    name where all input files are')

        return allargs

    def run(self, directory=None, noseTest=False, **inputs):
        """Execute the command.
        >>> from nipype.interfaces import fsl
        >>> bedp = fsl.Bedpostx(directory='subj1', fibres=1)
        >>> bedp.cmdline
        'bedpostx subj1 1'

        """

        if directory:
            self.inputs.directory = directory
        if not self.inputs.directory:
            raise AttributeError('Bedpostx requires a directory with standardized files')

        # incorporate other user options
        self.inputs.update(**inputs)

        # check that input directory has all the input files required
        if not noseTest:
            if not bedpostX_datacheck_ok(self.inputs.directory):
                raise AttributeError( 'Not all required files found in input \
                                    directory: %s' %self.inputs.directory )

        results = self._runner()
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs()

        return results



    def outputs_help(self):
        """
        Parameters
        ----------
        (all default input values set to None)

        outfile : /path/to/directory_with_input_files/files
            the files are
            1) merged_th<i-th fibre>samples - 4D volume - Samples from the distribution on theta
            2) merged_ph<i-th fibre>samples - Samples from the distribution on phi
            3) merged_f<i-th fibre>samples - 4D volume - Samples from the
                distribution on anisotropic volume fraction (see technical report).
            4) mean_th<i-th fibre>samples - 3D Volume - Mean of distribution on theta
            5) mean_ph<i-th fibre>samples - 3D Volume - Mean of distribution on phi
            6) mean_f<i-th fibre>samples - 3D Volume - Mean of distribution on f anisotropy
            7) dyads<i-th fibre> - Mean of PDD distribution in vector form.
            8) nodif_brain - brain extracted version of nodif - copied from input directory
            9) nodif_brain_mask - binary mask created from nodif_brain - copied from input directory

        """
        print self.outputs_help.__doc__

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string,file
                path/name of file of bedpostx image
        """
        outputs = Bunch(bvals=None,
                        bvecs=None,
                        nodif_brain=None,
                        nodif_brain_mask=None)
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        For bedpostx, the jobs get send to the sge if available and thus

        """

        outputs = self.outputs()
        #get path and names of the essential files that were generated by bedpostx
        files = glob(self.inputs.directory+'.bedpostX/*' )
        for line in files:
            if re.search('bvals',line) is not None:
                outputs.bvals=line

            elif re.search('bvecs',line) is not None:
                outputs.bvecs=line

            elif re.search('nodif_brain\.',line) is not None:
                outputs.nodif_brain=line

            elif re.search('nodif_brain_mask\.',line) is not None:
                outputs.nodif_brain_mask=line

        return outputs

#----------------------------------------------------------------------------------------------------

class Dtifit(FSLCommand):
    """Use FSL  dtifit command for fitting a diffusion tensor model at each voxel
    """

    opt_map = {
        'data':                     '-k %s',
        'basename':                 '-o %s',
        'bet_binary_mask':          '-m %s',
        'b_vector_file':            '-r %s',
        'b_value_file':             '-b %s',
        'min_z':                    '-z %d',
        'max_z':                    '-Z %d',
	'min_y':                    '-y %d',
	'max_y':                    '-Y %d',
	'min_x':                    '-x %d',
	'max_x':                    '-X %d',
        'verbose':                  '-V',
        'save_tensor':              '--save_tensor',
        'sum_squared_errors':       '--sse',
        'inp_confound_reg':         '--cni',
        'small_brain_area':         '--littlebit'}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'dtifit'

    def inputs_help(self):
        """Print command line documentation for dtifit."""
        print get_doc(self.cmd,self.opt_map,trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(data=None,
                            basename=None,
                            bet_binary_mask=None,
                            b_vector_file=None,
                            b_value_file=None,
                            min_z=None,
                            max_z=None,
                            min_y=None,
                            max_y=None,
                            min_x=None,
                            max_x=None,
                            verbose=None,
                            save_tensor=None,
                            sum_squared_errors=None,
                            inp_confound_reg=None,
                            small_brain_area=None)

    def _parse_inputs(self):
        """validate fsl dtifit options"""
        allargs = super(Dtifit,self)._parse_inputs()
        return allargs

    def run(self, data=None, noseTest=False,**inputs):
        """Execute the command.
        >>> from nipype.interfaces import fsl
        >>> dti = fsl.Dtifit(data='subj1Test')
        >>> dti.cmdline
        'dtifit -k subj1Test'
        """

        if data:
            self.inputs.data = data
        if not self.inputs.data:
            raise AttributeError('Dtifit requires input data')

        # incorporate other user options
        self.inputs.update(**inputs)

        # if data is a directory check existence of standardized files
        if not noseTest:

            if os.path.isdir(self.inputs.data):
                if not bedpostX_datacheck_ok(self.inputs.data):
                      raise AttributeError('Not all standardized files found \
                                        in input directory: %s' \
                                       %self.inputs.data)

            # if data is not a directory, check existences of inputs
            elif os.path.isfile(self.inputs.data):
                if not (os.path.exists(self.inputs.b_vector_file) \
                        and os.path.exists(self.inputs.b_value_file) \
                        and os.path.exists(self.inputs.bet_binary_mask)):
                       raise AttributeError('Not all standardized files have been supplied \
                            (ie. b_values_file, b_vector_file, and bet_binary_mask'  )

            else:
                raise AttributeError('Wrong input for Dtifit')

        results = self._runner()
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs()

        return results

    def outputs_help(self):
        """
        Parameters
        ----------
        (all default input values set to None)

        outfile : /path/to/directory_with_output_files/files
            the files are
            1) <basename>_V1 - 1st eigenvector
            2) <basename>_V2 - 2nd eigenvector
            3) <basename>_V3 - 3rd eigenvector
            4) <basename>_L1 - 1st eigenvalue
            5) <basename>_L2 - 2nd eigenvalue
            6) <basename>_L3 - 3rd eigenvalue
            7) <basename>_MD - mean diffusivity
            8) <basename>_FA - fractional anisotropy
            9) <basename>_SO - raw T2 signal with no diffusion weighting
        """
        print self.outputs_help.__doc__

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string,file
                path/name of file of dtifit image
        """
        outputs = Bunch(V1=None, V2=None, V3=None,
                        L1=None, L2=None, L3=None,
                        MD=None, FA=None, SO=None)

        return outputs


    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        outputs=self.outputs()
        #get path and names of the essential files that were generated by dtifit
        files = glob(os.getcwd()+'/'+self.inputs.basename+'*')
        for line in files:
            if re.search('_V1\.',line) is not None:
                outputs.V1=line

            elif re.search('_V2\.',line) is not None:
                outputs.V2=line

            elif re.search('_V3\.',line) is not None:
                outputs.V3=line

            elif re.search('_L1\.',line) is not None:
                outputs.L1=line

            elif re.search('_L2\.',line) is not None:
                outputs.L2=line

            elif re.search('_L3\.',line) is not None:
                outputs.L3=line

            elif re.search('_MD\.',line) is not None:
                outputs.MD=line

            elif re.search('_FA\.',line) is not None:
                outputs.FA=line

            elif re.search('_SO\.',line) is not None:
                outputs.SO=line

        return outputs



#--------------------------------------------------------------------------------------------------------------

class ImageMaths(FSLCommand):
    """
        Use FSL fslmaths command to allow mathematical manipulation of images
    """
    opt_map ={}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'fslmaths'

    def inputs_help(self):
        """Print command line documentation for fslmaths."""
        print get_doc(self.cmd,self.opt_map,trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(infile=None,
                            infile2=None,
                            outfile=None,
                            optstring=None,
                            suffix=None,      # ohinds: outfile suffix
                            outdatatype=None) # ohinds: change outdatatype

    def _get_outfile(self):
        suffix = '_maths' # ohinds: build suffix
        if self.inputs.suffix:
            suffix = self.inputs.suffix
        return fsl_info.gen_fname(self.inputs.infile,
                                  self.inputs.outfile,
                                  suffix=suffix)
    

    def _parse_inputs(self):
        """validate fsl fslmaths options"""

        # Add infile and outfile to the args if they are specified
        allargs=[]
        if self.inputs.infile:
            allargs.insert(0, list_to_filename(self.inputs.infile))
            self.outfile = self._get_outfile()
        if self.inputs.optstring:
            allargs.insert(1, self.inputs.optstring)

        if self.inputs.infile2:
            allargs.insert(2, list_to_filename(self.inputs.infile2))
            allargs.insert(3, self.outfile)
        else:
            allargs.insert(2, self.outfile)

        if self.inputs.outdatatype: # ohinds: assign odt
            allargs.append('-odt ' + self.inputs.outdatatype);

        return allargs

    def run(self, infile=None, infile2=None, outfile=None, **inputs):
        """Execute the command.
        >>> from nipype.interfaces import fsl
        >>> maths = fsl.Fslmaths(infile='foo.nii', optstring= '-add 5', outfile='foo_maths.nii')
        >>> maths.cmdline
        'fslmaths foo.nii -add 5 foo_maths.nii'

        """

        if infile:
            self.inputs.infile = infile
        if infile2:
            self.inputs.infile = infile2
        if not self.inputs.infile:
            raise AttributeError('Fslmaths requires an input file')
        if outfile:
            self.inputs.outfile = outfile
        self.inputs.update(**inputs)
        return super(ImageMaths, self).run()

    def outputs_help(self):
        """
        Parameters
        ----------
        (all default to None and are unset)

        outfile : /path/to/outfile
            path and filename to computed image
        """
        print self.outputs_help.__doc__

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string,file
                path/name of file of fslmaths image
        """
        outputs = Bunch(outfile=None)
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        outputs = self.outputs()
        outputs.outfile = glob(self._get_outfile())[0]
        return outputs


#-------------------------------------------------------------------------------------------------------------------

class Tbss2reg(FSLCommand):
    """
        Use FSL Tbss2reg for applying nonlinear registration of all FA images into standard space
    """
    opt_map ={ 'FMRIB58_FA_1mm':    '-T',
               'targetImage':       '-t %s',
               'findTarget':        '-n'}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'tbss_2_reg'

    def inputs_help(self):
        """Print command line documentation for tbss_2_reg."""
        print get_doc(self.cmd,self.opt_map,trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(FMRIB58_FA_1mm=None,
                            targetImage=None,
                            findTarget=None)

    def _parse_inputs(self):
        """validate fsl tbss_2_reg options"""
        allargs = super(Tbss2reg,self)._parse_inputs()
        return allargs

    def run(self, noseTest=False, **inputs):
        """Execute the command.
        >>> from nipype.interfaces import fsl
        >>> tbss2 = fsl.Tbss2reg(FMRIB58_FA_1mm=True)
        >>> tbss2.cmdline
        'tbss_2_reg foo -T foo.out'

        """
        self.inputs.update(**inputs)
        if (self.inputs.FMRIB58_FA_1mm is None) and \
           (self.inputs.targetImage is None) and \
           (self.inputs.findTarget is None):
            raise AttributeError('Tbss2reg needs at least one option')
        cwd=os.getcwd()
        results = self._runner(cwd=cwd)
        if not noseTest:
            results.outputs = self.aggregate_outputs(cwd)
        return results

    def outputs_help(self):
        """
        Parameters
        ----------
        (all default to None and are unset)

        outfile : /path/to/outfile
            path and filename to registered images with accompanying mask files
        """
        print self.outputs_help.__doc__

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string,file
                path/name of file of tbss_2_reg image
        """
        outputs = Bunch(outfiles=None)
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        outputs = self.outputs()
        outputs = tbss_1_2_getOutputFiles(outputs)

        if not outputs.outfiles:
            raise AttributeError('No output files created for tbss_2_reg')

        return outputs



#----------------------------------------------------------------------------------------------------------

def bedpostX_datacheck_ok(directory):
        """ checks if all the required files for bedpostx/dtifit have been supplied by the user"""

        proc = subprocess.Popen('bedpostx_datacheck  '+directory,
                     shell=True,
                     cwd=directory,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
        [stdout,stderr] = proc.communicate()

        bvalandbvec = []
        totalVols = []

        output = stdout.split('\n')
        for line in output:
            if re.search('data\s+does\s+not\s+exist\s*$',line) is not None:
                raise AttributeError('No 4D series of data volumes specified.\n')
            elif re.search('nodif_brain_mask\s+does\s+not\s+exist\s*$',line) is not None:
                raise AttributeError('No nodif_brain_mask specified.\n')
            elif re.match('^dim4\s+',line) is not None:
                totalVols.append(int(line.split(' ')[-1]))
            elif line.isdigit():
                bvalandbvec.append(int(line))

        # check that the bvals and bvecs are in the right order
        if (bvalandbvec[1]==totalVols[0]) and (bvalandbvec[1]*bvalandbvec[2]==bvalandbvec[3]):
            return True
        else:
            print 'bvals and bvecs values do not correspond with volumes in data.\n'

        return False

#----------------------------------------------------------------------------------------------------------

def tbss_1_2_getOutputFiles(outputs,cwd):
    """
        Extracts path and filename from the FA folder that ought to have been created
        if tbss_1_preproc and tbss_2_reg was executed correctly
    """

    if os.path.isdir(cwd+'/FA'):
            FA_files = glob(cwd+'/FA/*')
            origdata = glob(cwd+'/origdata/*.nii.gz')
    else:
        raise AttributeError('No FA subdirectory was found in cwd: \n'+cwd)

    outputs.outfiles=[]
    for line in origdata:
        path,fname = os.path.split(line)
        brainId = fname.split('.')[0]
        subject = [brainId,line]

        for FA in FA_files:
            if re.search(brainId,FA) is not None:
                subject.append(FA)
        outputs.outfiles.append(subject)

    return outputs


#-------------------------------------------------------------------------------------------------------------------

class Tbss1preproc(FSLCommand):
    """
        Use FSL Tbss1preproc for preparing your FA data in your TBSS working directory in the right format
    """
    opt_map ={}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'tbss_1_preproc'

    def inputs_help(self):
        """Print command line documentation for tbss_1_preproc."""
        print get_doc(self.cmd,self.opt_map,trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(infiles=None)

    def _parse_inputs(self):
        """validate fsl tbss_1_preproc options"""
        return [self.inputs.infiles]

    def run(self, noseTest=False, **inputs):
        """Execute the command.
        >>> from nipype.interfaces import fsl
        >>> tbss1 = fsl.Tbss1preproc(infiles='*.nii.gz')
        >>> tbss1.cmdline
        'tbss_1_preproc *.nii.gz'

        """
        self.inputs.update(**inputs)
        if self.inputs.infiles is None:
            raise AttributeError('tbss_1_preproc requires input files')
        cwd=os.getcwd()
        results = self._runner(cwd=cwd)
        if not noseTest:
            results.outputs = self.aggregate_outputs()
        return results

    def outputs_help(self):
        """
        Parameters
        ----------
        (all default to None and are unset)

        outfile : /path/to/outfile
            path and filename to the tbss preprocessed images
        """
        print self.outputs_help.__doc__

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string,file
                path/name of file of tbss_1_preproc image
        """
        outputs = Bunch(outfiles=None)
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        outputs=self.outputs()
        outputs = tbss_1_2_getOutputFiles(outputs,os.getcwd())
        if not outputs.outfiles:
            raise AttributeError('No output files created for tbss_1_preproc')

        return outputs

#----------------------------------------------------------------------------------------------------------

class Tbss3postreg(FSLCommand):
    """
        Use FSL Tbss3postreg for creating the mean FA image and skeletonise it
    """
    opt_map ={ 'subject_means':     '-S',
               'FMRIB58_FA':        '-T'}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'tbss_3_postreg'

    def inputs_help(self):
        """Print command line documentation for tbss_3_postreg."""
        print get_doc(self.cmd,self.opt_map,trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(subject_means=None,
                            FMRIB58_FA=None)

    def _parse_inputs(self):
        """validate fsl tbss_3_postreg options"""
        allargs = super(Tbss3postreg,self)._parse_inputs()
        return allargs

    def run(self,noseTest=False,**inputs):
        """Execute the command.
        >>> from nipype.interfaces import fsl
        >>> tbss3 = fsl.Tbss3postreg(subject_means=True)
        >>> tbss3.cmdline
        'tbss_3_postreg -S'

        """
        self.inputs.update(**inputs)
        if (self.inputs.subject_means is None) and (self.inputs.FMRIB58_FA is None):
            raise AttributeError('tbss_1_preproc requires at least one option flag to be set')
        results = self._runner(cwd=os.getcwd())
        if not noseTest:
            results.outputs = self.aggregate_outputs()
        return results

    def outputs_help(self):
        """
        Parameters
        ----------
        (all default to None and are unset)

        outfile : /path/to/outfile
            path and filename to tbss post-registration processed image
        """
        print self.outputs_help.__doc__

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string,file
                path/name of file of tbss_3_postreg image
        """
        outputs = Bunch(all_FA=None,
                        mean_FA_skeleton=None,
                        mean_FA_skeleton_mask=None,
                        mean_FA=None,
                        mean_FA_mask=None)
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        cwd = os.getcwd()
        outputs=self.outputs()
        if os.path.isdir(cwd+'/stats'):
            stats_files = glob(cwd+'/stats/*')
        else:
            raise AttributeError('No stats subdirectory was found in cwd: \n'+cwd)

        for imagePath in stats_files:
            if re.search('all_FA\.',imagePath):
                outputs.all_FA = imagePath
            elif re.search('mean_FA_skeleton\.',imagePath):
                outputs.mean_FA_skeleton = imagePath
            elif re.search('mean_FA\.',imagePath):
                outputs.mean_FA = imagePath
            elif re.search('mean_FA_mask\.',imagePath):
                outputs.mean_FA_mask = imagePath

        if (not outputs.all_FA) and (not outputs.mean_FA_skeleton):
            raise AttributeError('tbss_3_postreg did not create the desired files')

        return outputs

#--------------------------------------------------------------------------------------------------


class Tbss4prestats(FSLCommand):
    """
        Use FSL Tbss4prestats thresholds the mean FA skeleton image at the chosen threshold
    """
    opt_map ={}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'tbss_4_prestats'

    def inputs_help(self):
        """Print command line documentation for tbss_4_prestats."""
        print get_doc(self.cmd,self.opt_map,trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(threshold=None)

    def _parse_inputs(self):
        """validate fsl tbss_4_prestats options"""
        allargs=[]
        # Add source files to the args if they are specified
        if self.inputs.threshold:
            allargs.append(str(self.inputs.threshold))
        else:
            raise AttributeError('tbss_4_prestats requires threshold')

        return allargs

    def run(self, noseTest=False, **inputs):
        """Execute the command.
        >>> from nipype.interfaces import dti
        >>> tbss4 = fsl.Tbss4prestats(threshold=0.3)
        >>> tbss4.cmdline
        'tbss_4_postreg 0.3'

        """
        self.inputs.update(**inputs)
        results = self._runner(cwd=os.getcwd())
        if not noseTest:
            results.outputs = self.aggregate_outputs()
        return results

    def outputs_help(self):
        """
        Parameters
        ----------
        (all default to None and are unset)

        outfile : /path/to/outfile
            path and filename to tbss prestats thresholded mean FA image
        """
        print self.outputs_help.__doc__

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string,file
                path/name of file of tbss_4_prestats image
        """
        outputs = Bunch(all_FA_skeletonised=None,
                        mean_FA_skeleton_mask=None)
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        outputs = self.outputs()
        cwd = os.getcwd()
        if os.path.isdir(cwd+'/stats'):
            stats_files = glob(cwd+'/stats/*')
        else:
            raise AttributeError('No stats subdirectory was found in cwd: \n'+cwd)

        for imagePath in stats_files:
            if re.search('all_FA_skeletonised\.',imagePath):
                outputs.all_FA_skeletonised = imagePath
            elif re.search('mean_FA_skeleton_mask\.',imagePath):
                outputs.mean_FA_skeleton_mask = imagePath

        if not outputs.all_FA_skeletonised:
                raise AttributeError('tbss_4_prestats did not create the desired files')

        return outputs


#-----------------------------------------------------------------------------------------------------------

class Randomise(FSLCommand):
    """
        FSL Randomise: feeds the 4D projected FA data into GLM modelling and thresholding
        in order to find voxels which correlate with your model
    """
    opt_map ={'input_4D':                           '-i %s',
              'output_rootname':                    '-o %s',
              'demean_data':                        '-D',
              'one_sample_gmean':                   '-1',
              'mask_image':                         '-m %s',
              'design_matrix':                      '-d %s',
              't_contrast':                         '-t %s',
              'f_contrast':                         '-f %s',
              'xchange_block_labels':               '-e %s',
              'print_unique_perm':                  '-q',
              'print_info_parallelMode':            '-Q',
              'num_permutations':                   '-n %d',
              'vox_pvalus':                         '-x',
              'fstats_only':                        '--fonly',
              'thresh_free_cluster':                '-T',
              'thresh_free_cluster_2Dopt':          '--T2',
              'cluster_thresholding':               '-c %0.2f',
              'cluster_mass_thresholding':          '-C %0.2f',
              'fcluster_thresholding':              '-F %0.2f',
              'fcluster_mass_thresholding':         '-S %0.2f',
              'variance_smoothing':                 '-v %0.2f',
              'diagnostics_off':                    '--quiet',
              'output_raw':                         '-R',
              'output_perm_vect':                   '-P',
              'int_seed':                           '--seed %d',
              'TFCE_height_param':                  '--tfce_H %0.2f',
              'TFCE_extent_param':                  '--tfce_E %0.2f',
              'TFCE_connectivity':                  '--tfce_C %0.2f',
              'list_num_voxel_EVs_pos':             '--vxl %s',
              'list_img_voxel_EVs':                 '--vxf %s'}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'randomise'

    def inputs_help(self):
        """Print command line documentation for randomise."""
        print get_doc(self.cmd,self.opt_map,trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(input_4D=None,
                            output_rootname=None,
                            demean_data=None,
                            one_sample_gmean=None,
                            mask_image=None,
                            design_matrix=None,
                            t_contrast=None,
                            f_contrast=None,
                            xchange_block_labels=None,
                            print_unique_perm=None,
                            print_info_parallelMode=None,
                            num_permutations=None,
                            vox_pvalus=None,
                            fstats_only=None,
                            thresh_free_cluster=None,
                            thresh_free_cluster_2Dopt=None,
                            cluster_thresholding=None,
                            cluster_mass_thresholding=None,
                            fcluster_thresholding=None,
                            fcluster_mass_thresholding=None,
                            variance_smoothing=None,
                            diagnostics_off=None,
                            output_raw=None,
                            output_perm_vect=None,
                            int_seed=None,
                            TFCE_height_param=None,
                            TFCE_extent_param=None,
                            TFCE_connectivity=None,
                            list_num_voxel_EVs_pos=None,
                            list_img_voxel_EVs=None)

    def _parse_inputs(self):
        """validate fsl randomise options"""
        allargs = super(Randomise,self)._parse_inputs(skip=('input_4D','output_rootname'))

        # Add source files to the args if they are specified
        if self.inputs.input_4D:
            allargs.insert(0, '-i '+self.inputs.input_4D)
        else:
            raise AttributeError('randomise needs a 4D image as input')

        if self.inputs.output_rootname:
            allargs.insert(1, '-o '+self.inputs.output_rootname)

        return allargs

    def run(self, input_4D=None,output_rootname=None,**inputs):
        """Execute the command.
        >>> from nipype.interfaces import fsl
        >>> rand = fsl.Randomise(input_4D='infile2',output_rootname='outfile2',f_contrast='infile.f',one_sample_gmean=True,int_seed=4)
        >>> rand.cmdline
        'randomise -i infile2 -o outfile2 -1 -f infile.f --seed 4'
        """
        if input_4D:
            self.inputs.input_4D = input_4D
        if not self.inputs.input_4D:
            raise AttributeError('randomise requires an input file')

        if output_rootname:
            self.inputs.output_rootname = output_rootname

        self.inputs.update(**inputs)
        results = self._runner(cwd=os.getcwd())
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs()
        return results

    def outputs_help(self):
        """
        Parameters
        ----------
        (all default to None and are unset)

        outfile : /path/to/outfile
            path and filename to randomise generated files
        """
        print self.outputs_help.__doc__

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string,file
                path/name of file of randomise image
        """
        outputs = Bunch(tstat=None)
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        outputs=self.outputs()
        randFiles = glob(self.inputs.output_rootname+'*')
        outputs.tstat=[]

        for imagePath in randFiles:
            if re.search('tstat',imagePath):
                outputs.tstat.append(imagePath)

        if not outputs.tstat:
            raise AttributeError('randomise did not create the desired files')

        return outputs



#-----------------------------------------------------------------------------------------------------------


class Randomise_parallel(Randomise):
    """
        FSL Randomise_parallel: feeds the 4D projected FA data into GLM modelling and thresholding
        in order to find voxels which correlate with your model
    """
    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'randomise_parallel'

    def inputs_help(self):
        """Print command line documentation for randomise."""
        print get_doc('randomise',self.opt_map,trap_error=False)



#---------------------------------------------------------------------------------------------------------------

class Probtrackx(FSLCommand):

    """Use FSL  probtrackx for tractography and connectivity-based segmentation
    """

    opt_map = { 'basename':                      '-s %s',
                'binaryMask':                    '-m %s',
                'seedFile':                      '-x %s',
                'verbose':                       '-V %d',
                'helpDoc':                       '-h',
                'mode':                          '--mode=%s',   #options: simple, seedmask
                'targetMasks':                   '--targetmasks=%s',
                'secondMask':                    '--mask2=%s',
                'wayPointsMask':                 '--waypoints=%s',
                'activateNetwork':               '--network',
                'surfaceDescriptor':             '--mesh=%s',
                'refVol4seedVoxels':             '--seedref=%s',
                'finalVolDir':                   '--dir=%s',
                'useActualDirName':              '--forcedir',
                'outputPathDistribution':        '--opd',
                'correctPathDistribution':       '--pd',
                'outputSeeds2targets':           '--os2t',
                'outfBasename':                   '-o %s',
                'rejectMaskPaths':               '--avoid=%s',
                'noTrackingMask':                '--stop=%s',
                'preferedOrientation':           '--prefdir=%s',
                'Tmatrix':                       '--xfm=%s',
                'numOfSamples':                  '-P %d',
                'nstepsPersample':               '-S %d',
                'curvatureThreshold':            '-c %.2f',
                'steplength':                    '--steplength=%.2f',
                'performLoopcheck':              '-l',
                'useAnisotropy':                 '-f',
                'selectRandfibres':              '--randfib',
                'forceAstartingFibre':           '--fibst=%d',
                'modifiedEulerStreamlining':     '--modeuler',
                'randSeed':                      '--rseed',
                'outS2Tcounts':                  '--seedcountastext'}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'probtrackx'

    def inputs_help(self):
        """Print command line documentation for probtrackx."""
        print get_doc(self.cmd,self.opt_map,trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(    basename=None,
                                binaryMask=None,
                                seedFile=None,
                                verbose=None,
                                helpDoc=None,
                                mode=None,
                                targetMasks=None,
                                secondMask=None,
                                wayPointsMask=None,
                                activateNetwork=None,
                                surfaceDescriptor=None,
                                refVol4seedVoxels=None,
                                finalVolDir=None,
                                useActualDirName=None,
                                outputPathDistribution=None,
                                correctPathDistribution=None,
                                outputSeeds2targets=None,
                                outfBasename=None,
                                rejectMaskPaths=None,
                                noTrackingMask=None,
                                preferedOrientation=None,
                                Tmatrix=None,
                                numOfSamples=None,
                                nstepsPersample=None,
                                curvatureThreshold=None,
                                steplength=None,
                                performLoopcheck=None,
                                useAnisotropy=None,
                                selectRandfibres=None,
                                forceAstartingFibre=None,
                                modifiedEulerStreamlining=None,
                                randSeed=None,
                                outS2Tcounts=None )

    def _parse_inputs(self):
        """validate fsl probtrackx options"""
        allargs = super(Probtrackx,self)._parse_inputs(skip=('basename','binaryMask','seedFile'))

        # Add source files to the args if they are specified
        if self.inputs.basename:
            allargs.insert(0, '-s '+self.inputs.basename)
        else:
            raise AttributeError('probtrackx needs a basename as input')

        if self.inputs.binaryMask:
            allargs.insert(1, '-m '+self.inputs.binaryMask)
        else:
            raise AttributeError('probtrackx needs a binary mask as input')

        if self.inputs.seedFile:
            allargs.insert(2, '-x '+self.inputs.seedFile)
        else:
            raise AttributeError('probtrackx needs a seed volume, or voxel, \
                                    or ascii file with multiple volumes as input')

        return allargs


    def run(self, basename=None,binaryMask=None,seedFile=None,noseTest=False,**inputs):
        """Execute the command.
        >>> from nipype.interfaces import fsl
        >>> pbx = Probtrackx(basename='subj1',binaryMask='nodif_brain_mask',seedFile='standard')
        >>> pbx.cmdline
        'probtrackx -s subj1 -m nodif_brain_mask -x standard'
        """

        if basename:
            self.inputs.basename=basename

        if binaryMask:
            self.inputs.binaryMask=binaryMask

        if seedFile:
            self.inputs.seedFile=seedFile

        # incorporate user options
        self.inputs.update(**inputs)

        # if data directory specified, check existence of standardized
        # files
        cwd=os.getcwd()

        if not noseTest:
            directory=os.path.join(cwd,self.inputs.basename)
            if os.path.isdir(directory):
                if not probtrackx_datacheck_ok(directory):
                    raise AttributeError('Not all standardized files found \
                                         in input directory: %s' %directory)


        results = self._runner(cwd=cwd)
        if not noseTest:
            results.outputs = self.aggregate_outputs()

        return results



    def outputs_help(self):
        """
        Parameters
        ----------
        (all default input values set to None)

        outfile : /path/to/directory_with_output_files/files
            the files are

        """
        print self.outputs_help.__doc__

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string,file
                path/name of file of probtrackx image
        """
        outputs = Bunch(outfile=None)
        return outputs


    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        outputs=self.outputs()
        outputs.outfile = fsl_info.gen_fname(self.inputs.basename,
                                             fname=self.inputs.outfile,
                                             suffix='_pbx',
                                             check=True)
        return outputs


#---------------------------------------------------------------------------------------------------------------

def probtrackx_datacheck_ok(directory):

    """ checks whether the directory given to -s <directory> flag contains
        the three required standardized files """

    merged_ph = False
    merged_th = False
    nodif_brain_mask = False

    f1=fsl_info.glob(os.path.join(directory,'merged_ph*'))
    if f1 is not None:
        merged_ph=True

    f2=fsl_info.glob(os.path.join(directory,'merged_th*'))
    if f2 is not None:
        merged_th=True

    f3=fsl_info.glob(os.path.join(directory,'nodif_brain_mask*'))
    if f3 is not None:
        nodif_brain_mask=True


    return (merged_ph and merged_th and nodif_brain_mask)


#-------------------------------------------------------------------------------------------------------------------

class Vecreg(FSLCommand):
    """
        Use FSL Vecreg for registering vector data
    """
    opt_map ={ 'infile':            '-i %s',
               'outfile':           '-o %s',
               'refVolName':        '-r %s',
               'verbose':           '-v',
               'helpDoc':           '-h',
               'tensor':            '--tensor',
               'affineTmat':        '-t %s',
               'warpFile':          '-w %s',
               'interpolation':     '--interp %s',
               'brainMask':         '-m %s'}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'vecreg'

    def inputs_help(self):
        """Print command line documentation for Vecreg."""
        print get_doc(self.cmd,self.opt_map,trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(infile=None,
                            outfile=None,
                            refVolName=None,
                            verbose=None,
                            helpDoc=None,
                            tensor=None,
                            affineTmat=None,
                            warpFile=None,
                            interpolation=None,
                            brainMask=None,
                            cwd=None)

    def _parse_inputs(self):
        """validate fsl vecreg options"""
        allargs = super(Vecreg,self)._parse_inputs(skip=('infile','outfile','refVolName','cwd'))

        # Add source files to the args if they are specified
        if self.inputs.infile:
            allargs.insert(0, '-i '+self.inputs.infile)
        else:
            raise AttributeError('vecreg needs an input file')

        if self.inputs.outfile:
            allargs.insert(1, '-o '+self.inputs.outfile)
        else:
            outfile = fsl_info.gen_fname(self.inputs.infile,
                                         cwd=self.inputs.cwd,
                                         suffix='_vrg')
            self.inputs.outfile=outfile
            allargs.insert(1, '-o '+outfile)

        if self.inputs.refVolName:
            allargs.insert(2, '-r '+self.inputs.refVolName)
        else:
            raise AttributeError('vecreg needs a reference volume')

        return allargs

    def run(self, infile=None, outfile=None, refVolName=None, **inputs):
        """Execute the command.
        >>> from nipype.interfaces import fsl
        >>> vreg = fsl.Vecreg(infile='inf',output='infout',refVolName='MNI152')
        >>> vreg.cmdline
        'vecreg -i inf -o infout -r MNI152'

        """
        if infile:
            self.inputs.infile=infile

        if outfile:
            self.inputs.outfile=outfile

        if refVolName:
            self.inputs.refVolName=refVolName

        self.inputs.update(**inputs)
        return super(Vecreg, self).run()

    def outputs_help(self):
        """
        Parameters
        ----------
        (all default to None and are unset)

        outfile : /path/to/outfile
            path and filename to registered images with accompanying mask files
        """
        print self.outputs_help.__doc__

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string,file
                path/name of file of probtrackx image
        """
        outputs = Bunch(outfile=None)
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        outputs=self.outputs()
        outputs.outfile = fsl_info.gen_fname(self.inputs.infile,
                                             fname=self.inputs.outfile,
                                             cwd=self.inputs.cwd,
                                             suffix='_vrg',
                                             check=True)
        return outputs

##-------------------------------------------------------------------------------------------------------------------

class ProjThresh(FSLCommand):
    """
        Use FSL Proj_thresh for thresholding some outputs of probtrack
    """
    opt_map ={}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'proj_thresh'

    def inputs_help(self):
        """Print command line documentation for Proj_thresh."""
        print get_doc(self.cmd,self.opt_map,trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(volumes=None,threshold=None,cwd=None)

    def _parse_inputs(self):
        """validate fsl Proj_thresh options"""
        allargs = []

        if self.inputs.volumes:
            for vol in self.inputs.volumes:
                allargs.append(vol)
        else:
            raise AttributeError('proj_thresh needs input volumes')

        if self.inputs.threshold:
            allargs.append(repr(self.inputs.threshold))
        else:
            raise AttributeError('proj_thresh needs a threshold value')

        return allargs

    def run(self, volumes=None,threshold=None,**inputs):
        """Execute the command.
        >>> from nipype.interfaces import fsl
        >>> pThresh = fsl.ProjThresh(volumes=['seeds_to_M1','seeds_to_M2'],threshold=3)
        >>> pThresh.cmdline
        'proj_thresh seeds_to_M1 seeds_to_M2 3'

        """

        if volumes is not None:
            self.inputs.volumes=filename_to_list(volumes)

        if threshold is not None:
            self.inputs.threshold = threshold

        self.inputs.update(**inputs)
        return super(ProjThresh, self).run()

    def outputs_help(self):
        """
        Parameters
        ----------
        (all default to None and are unset)

        outfile : /path/to/outfile
            path and filename to registered images with accompanying mask files
        """
        print self.outputs_help.__doc__

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string,file
                path/name of file of probtrackx image
        """
        outputs = Bunch(outfile=None)
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        outputs=self.outputs()
        outputs.outfile=[]

        for files in self.inputs.volumes:
            outputs.outfile.append(fsl_info.glob(files+'_proj_seg_thr_*'))

        return outputs

#-------------------------------------------------------------------------------------------------------------------

class FindTheBiggest(FSLCommand):
    """
        Use FSL Find_the_biggest for performing hard segmentation on the outputs
        of connectivity-based thresholding in probtrack
    """
    opt_map ={}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'find_the_biggest'

    def inputs_help(self):
        """Print command line documentation for Find_the_biggest."""
        print get_doc(self.cmd,self.opt_map,trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(infile=None,
                            outfile=None)

    def _parse_inputs(self):
        """validate fsl Find_the_biggest options"""
        allargs=[]
        if self.inputs.infile:
            allargs.insert(0, self.inputs.infile)
        if self.inputs.outfile:
            allargs.insert(1, self.inputs.outfile)
        else:
            outfile = fsl_info.gen_fname(self.inputs.infile,
                                         fname=self.inputs.outfile,
                                         suffix='_fbg')
            allargs.insert(1, outfile)

        return allargs

    def run(self, infile=None, outfile=None, **inputs):
        """Execute the command.
        >>> from nipype.interfaces import fsl
        >>> fBig = fsl.Find_the_biggest(volumes='all*',outfile='biggestOut')
        >>> fBig.cmdline
        'find_the_biggest all* biggestOut'

        """
        if infile:
            self.inputs.infile=infile
        if not self.inputs.infile:
            raise AttributeError('find_the_biggest requires input file(s)')
        if outfile:
            self.inputs.outfile=outfile
        return super(FindTheBiggest, self).run()

    def outputs_help(self):
        """
        Parameters
        ----------
        (all default to None and are unset)

        outfile : /path/to/outfile
            path and filename to registered images with accompanying mask files
        """
        print self.outputs_help.__doc__

    def outputs(self):
        """Returns a bunch structure with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string,file
                path/name of file of probtrackx image
        """
        outputs = Bunch(outfile=None)
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        outputs=self.outputs()
        outputs.outfile = fsl_info.gen_fname(self.inputs.infile,
                                             fname=self.inputs.outfile,
                                             suffix='_fbg',
                                             check=True)

        return outputs

#-------------------------------------------------------------------------------------------------------------------
