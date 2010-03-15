"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 4.1.4.

Examples
--------
See the docstrings of the individual classes for examples.

"""

import os
from glob import glob
import warnings

from nipype.interfaces.fsl.base import FSLCommand, FSLInfo
from nipype.interfaces.fsl.base import NEW_FSLCommand
from nipype.interfaces.base import Bunch, TraitedAttr
from nipype.utils.filemanip import fname_presuffix, list_to_filename
from nipype.utils.docparse import get_doc
from nipype.utils.misc import container_to_string, is_container

# We are shooting for interoperability for now - Traits or Traitlets
import nipype.externals.traitlets as traits
# import enthought.traits.api as traits

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class Bet(NEW_FSLCommand):
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

    class in_spec(TraitedAttr):
        '''Note: Currently we don't support -R, -S, -Z,-A or -A2'''
        # We use position args here as list indices - so a negative number will
        # put something on the end
        # Also, it would be nice to use traits.File types here, but Traitlets
        # doesn't support that (Yet)
        infile = traits.Str(desc = 'input file to skull strip',
                            argstr='%s', position=0, mandatory=True)
        outfile = traits.Str(desc = 'name of output skull stripped image',
                             argstr='%s', position=1, genfile=True)
        outline = traits.Bool(desc = 'create surface outline image',
                              argstr='-o')
        mask = traits.Bool(False, desc = 'create binary mask image', 
                           argstr='-m')
        skull = traits.Bool(desc = 'create skull image',
                            argstr='-s')
        nooutput = traits.Bool(argstr='-n')
        frac = traits.Float(0.5, desc = 'fractional intensity threshold',
                            argstr='-f %.2f')
        vertical_gradient = traits.Float(0.0, argstr='-g %.2f')
        radius = traits.Int(argstr='-r %d', units='mm')
        # Note - Traitlets doesn't actually support the 'trait' metadata, so it
        # is just plain ol' metadata. But we use the same 'trait' id here for
        # consistency with the Traits API. Likewise for minlen and maxlen.
        # XXX Currently, default_value won't work for a List
        center = traits.List(desc = 'center of gravity in voxels',
                             argstr='-c %s', trait=traits.Int, minlen=3,
                             maxlen=3, units='voxels')
        threshold = traits.Bool(argstr='-t')
        mesh = traits.Bool(argstr='-e')
        verbose = traits.Bool(argstr='-v')
        _xor_inputs = ('functional', 'reduce_bias')
        functional = traits.Bool(argstr='-F', xor=_xor_inputs)
        reduce_bias = traits.Bool(argstr='-B', xor=_xor_inputs)

    class out_spec(traits.HasTraits):
        # Note - desc has special meaning in Traits, similar to __doc__
        outfile = traits.Str(desc="path/name of skullstripped file")
        maskfile = traits.Str(
                        desc="path/name of binary brain mask (if generated)")

    def _gen_outfiles(self, check = False):
        outputs = self._outputs()
        outputs.outfile = self.inputs.outfile
        if not outputs.outfile and self.inputs.infile:
            outputs.outfile = self._gen_fname(self.inputs.infile,
                                              suffix = '_brain',
                                              check = check)
        if self.inputs.mesh:
            outputs.meshfile = self._gen_fname(outputs.outfile,
                                               suffix = '_mesh.vtk',
                                               change_ext = False,
                                               check = check)
        if self.inputs.mask or self.inputs.reduce_bias:
            outputs.maskfile = self._gen_fname(outputs.outfile,
                                               suffix = '_mask',
                                               check = check)
        return outputs

    def _convert_inputs(self, opt, value):
        if opt == 'outfile':
            if not value:
                outputs = self._gen_outfiles()
                return outputs.outfile
        return value


class Fast(FSLCommand):
    """Use FSL FAST for segmenting and bias correction.

    For complete details, see the `FAST Documentation.
    <http://www.fmrib.ox.ac.uk/fsl/fast4/index.html>`_

    To print out the command line help, use:
        fsl.Fast().inputs_help()

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> faster = fsl.Fast(out_basename = 'myfasted')
    >>> fasted = faster.run(['file1', 'file2'])

    >>> faster = fsl.Fast(infiles=['filea', 'fileb'], out_basename='myfasted')
    >>> fasted = faster.run()

    """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'fast'

    opt_map = {'number_classes':       '-n %d',
            'bias_iters':           '-I %d',
            'bias_lowpass':         '-l %d',  # in mm
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
            'use_priors':           '-P',  # must also set -a!
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
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def run(self, infiles=None, **inputs):
        """Execute the FSL fast command.

        Parameters
        ----------
        infiles : string or list of strings
            File(s) to be segmented or bias corrected
        inputs : dict, optional
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
        """Returns a :class:`nipype.interfaces.base.Bunch` with outputs

        Parameters
        ----------
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

        outputs = Bunch(mixeltype=[],
                seg=[],
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
        _, envext = FSLInfo.outputtype()
        outputs = self.outputs()

        if not is_container(self.inputs.infiles):
            infiles = [self.inputs.infiles]
        else:
            infiles = self.inputs.infiles
        for item in infiles:
            # get basename (correct fsloutpputytpe extension)
            if self.inputs.out_basename:
                pth, nme = os.path.split(item)
                _, _ = os.path.splitext(nme)
                item = pth + self.inputs.out_basename + envext
            else:
                nme, _ = os.path.splitext(item)
                item = nme + envext
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
                        suffix='_seg_%d' % (i)))
                    # always pve,mixeltype unless nopve = True
            if not self.inputs.nopve:
                fname = fname_presuffix(item, suffix='_pveseg')
                outputs.partial_volume_map.append(fname)
                fname = fname_presuffix(item, suffix='_mixeltype')
                outputs.mixeltype.append(fname)

                for i in range(nclasses):
                    fname = fname_presuffix(item, suffix='_pve_%d' % (i))
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
                    fname = fname_presuffix(item, suffix='_prob_%d' % (i))
                    outputs.prob_maps.append(fname)

        # For each output file-type (key), check that any expected
        # files in the output list exist.
        for outtype, outlist in outputs.items():
            if len(outlist) > 0:
                for outfile in outlist:
                    if not len(glob(outfile)) == 1:
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
        print get_doc(self.cmd, self.opt_map, '-help')

    def _parse_inputs(self):
        '''Call our super-method, then add our input files'''
        # Could do other checking above and beyond regular _parse_inputs here
        allargs = super(Flirt, self)._parse_inputs(skip=('infile',
            'outfile',
            'reference',
            'outmatrix',
            'inmatrix'))
        possibleinputs = [(self.inputs.outfile, '-out'),
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
            if not self._glob(outputs.outfile):
                raise_error(outputs.outfile)
        if self.inputs.outmatrix:
            outputs.outmatrix = os.path.join(cwd, self.inputs.outmatrix)
            if not self._glob(outputs.outmatrix):
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
        allargs = super(ApplyXfm, self)._parse_inputs()
        if not self.inputs.outfile:
            outfile = self._gen_fname(self.inputs.infile,
                                         self.inputs.outfile,
                                         suffix='_axfm')
            allargs.append(' '.join(('-out', outfile)))
        for idx, arg in enumerate(allargs):
            if '-out' in arg:
                continue
        allargs.insert(idx, '-applyxfm')
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
        """Returns a :class:`nipype.interfaces.base.Bunch` with outputs

        Parameters
        ----------
        (all default to None and are unset)

            outfile : string, filename
            outmatrix : string, filename
        """
        outputs = Bunch(outfile=None, outmatrix=None)
        return outputs

    def aggregate_outputs(self, verify_outmatrix=False):
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
        outputs.outfile = self._gen_fname(self.inputs.infile,
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

        if self.inputs.infile:
            infile = list_to_filename(self.inputs.infile)
            allargs.insert(0, '-in %s' % infile)
            if self.inputs.outfile is None:
                outfile = self._gen_fname(infile, self.inputs.outfile,
                                          suffix='_mcf')
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
        """Returns a :class:`nipype.interfaces.base.Bunch` with outputs

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

        outputs.outfile = self._gen_fname(list_to_filename(self.inputs.infile),
                self.inputs.outfile, cwd=cwd, suffix='_mcf', check=True)

        # XXX Need to change 'item' below to something that exists
        # outfile? infile?
        # These could be handled similarly to default values for inputs
        if self.inputs.statsimgs:
            outputs.varianceimg = self._gen_fname(list_to_filename(self.inputs.infile),
                self.inputs.outfile, cwd=cwd, suffix='_variance', check=True)
            outputs.stdimg = self._gen_fname(list_to_filename(self.inputs.infile),
                self.inputs.outfile, cwd=cwd, suffix='_sigma', check=True)
            outputs.meanimg = self._gen_fname(list_to_filename(self.inputs.infile),
                self.inputs.outfile, cwd=cwd, suffix='_meanvol', check=True)
        if self.inputs.savemats:
            matnme, _ = os.path.splitext(list_to_filename(self.inputs.infile))
            matnme = matnme + '.mat'
            outputs.outmatfile = matnme
        if self.inputs.saveplots:
            # Note - if e.g. outfile has .nii.gz, you get .nii.gz.par, which is
            # what mcflirt does!
            outputs.parfile = outputs.outfile + '.par'
            if not os.path.exists(outputs.parfile):
                msg = "Output file '%s' for '%s' was not generated" \
                        % (outputs.parfile, self.cmd)
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

    def write_config(self, configfile):
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
            print ('unable to create config_file %s' % (configfile))

        for item in valid_inputs:
            fid.write('%s\n' % (item))
        fid.close()

    def outputs(self):
        """Returns a :class:`nipype.interfaces.base.Bunch` with outputs

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

        for item, file in outputs.items():
            if file is not None:
                file = os.path.join(cwd, file)
                file = self._glob(file)
                if file is None:
                    raise IOError('file %s of type %s not generated' % (file, item))
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
        """Returns a :class:`nipype.interfaces.base.Bunch` with outputs

        Parameters
        ----------
        (all default to None and are unset)

             outfile
        """
        outputs = Bunch(outfile=None)
        return outputs

    def aggregate_outputs(self):
        outputs = self.outputs()
        outputs.outfile = self._gen_fname(self.inputs.infile,
                self.inputs.outfile, suffix='_warp', check=True)
        return outputs
