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
from nipype.utils.filemanip import list_to_filename
from nipype.interfaces.base import Bunch
from nipype.utils.docparse import get_doc

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


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
        return self._gen_fname(self.inputs.infile,
                                  self.inputs.outfile,
                                  suffix='_smooth',
                                  check=check)

    def _parse_inputs(self):
        return [self.inputs.infile,
                # ohinds: convert fwhm to stddev
                '-kernel gauss', str(self.inputs.fwhm / 2.3548),
                '-fmean',
                self._get_outfile()]

    def outputs(self):
        """Returns a :class:`nipype.interfaces.base.Bunch` with outputs

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
        return self._gen_fname(self.inputs.infile[0],
                                  self.inputs.outfile,
                                  suffix='_merged',
                                  check=check)

    def _parse_inputs(self):
        allargs = [self.inputs.dimension,
                    self._get_outfile()]
        allargs.extend(self.inputs.infile)
        return allargs

    def outputs(self):
        """Returns a :class:`nipype.interfaces.base.Bunch` with outputs

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


class ExtractRoi(FSLCommand):
    """Uses FSL Fslroi command to extract region of interest (ROI)
    from an image.

    You can a) take a 3D ROI from a 3D data set (or if it is 4D, the
    same ROI is taken from each time point and a new 4D data set is
    created), b) extract just some time points from a 4D data set, or
    c) control time and space limits to the ROI.  Note that the
    arguments are minimum index and size (not maximum index).  So to
    extract voxels 10 to 12 inclusive you would specify 10 and 3 (not
    10 and 12).
    """
    opt_map = {}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'fslroi'

    def inputs_help(self):
        """Print command line documentation for fslroi."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

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

        allargs = []
        # Add infile and outfile to the args if they are specified
        if self.inputs.infile:
            allargs.insert(0, self.inputs.infile)
            outfile = self._gen_fname(self.inputs.infile,
                                      self.inputs.outfile,
                                      suffix='_roi')
            allargs.insert(1, outfile)

        #concat all numeric variables into a string separated by space
        #given the user's option
        dim = [self.inputs.xmin, self.inputs.xsize, self.inputs.ymin,
               self.inputs.ysize,
               self.inputs.zmin, self.inputs.zsize, self.inputs.tmin,
               self.inputs.tsize]
        args = []
        for num in dim:
            if num is not None:
                args.append(repr(num))

        allargs.insert(2, ' '.join(args))

        return allargs

    def run(self, infile=None, outfile=None, **inputs):
        """Execute the command.
        >>> from nipype.interfaces import fsl
        >>> fslroi = fsl.ExtractRoi(infile='foo.nii', outfile='bar.nii', \
                                    tmin=0, tsize=1)
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
        """Returns a :class:`nipype.interfaces.base.Bunch` with outputs

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
        outputs.outfile = self._gen_fname(self.inputs.infile,
                                self.inputs.outfile, suffix='_roi', check=True)
        return outputs


class Split(FSLCommand):
    """Uses FSL Fslsplit command to separate a volume into images in
    time, x, y or z dimension.
    """
    opt_map = {'outbasename': None,  # output basename
               'time': '-t',  # separate images in time (default behaviour)
               'xdir': '-x',  # separate images in the x direction
               'ydir': '-y',  # separate images in the y direction
               'zdir': '-z',  # separate images in the z direction
               'infile': None}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'fslsplit'

    def inputs_help(self):
        """Print command line documentation for fslsplit."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def _parse_inputs(self):
        """validate fsl fslroi options"""

        allargs = super(Split, self)._parse_inputs(skip=('infile'))
        if self.inputs.infile:
            allargs.insert(0, self.inputs.infile)
        if self.inputs.outbasename:
            allargs.insert(0, self.inputs.outbasename)
        return allargs

    def run(self, infile=None, **inputs):
        """Execute the command.
        >>> from nipype.interfaces import fsl
        >>> fslsplit = fsl.Split(infile='foo.nii',time=True)
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
        """Returns a :class:`nipype.interfaces.base.Bunch` with outputs

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
        type, ext = FSLInfo.outputtype()
        outbase = 'vol*'
        if self.inputs.outbasename:
            outbase = '%s*' % self.inputs.outbasename
        outputs.outfiles = sorted(glob(os.path.join(os.getcwd(),
                                                    outbase + ext)))
        return outputs


class ImageMaths(FSLCommand):
    """Use FSL fslmaths command to allow mathematical manipulation of images
    """
    opt_map = {}

    @property
    def cmd(self):
        """sets base command, immutable"""
        return 'fslmaths'

    def inputs_help(self):
        """Print command line documentation for fslmaths."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(infile=None,
                            infile2=None,
                            outfile=None,
                            optstring=None,
                            suffix=None,  # ohinds: outfile suffix
                            outdatatype=None)  # ohinds: change outdatatype

    def _get_outfile(self):
        suffix = '_maths'  # ohinds: build suffix
        if self.inputs.suffix:
            suffix = self.inputs.suffix
        return self._gen_fname(self.inputs.infile,
                                  self.inputs.outfile,
                                  suffix=suffix)

    def _parse_inputs(self):
        """validate fsl fslmaths options"""

        # Add infile and outfile to the args if they are specified
        allargs = []
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

        if self.inputs.outdatatype:  # ohinds: assign odt
            allargs.append('-odt ' + self.inputs.outdatatype)

        return allargs

    def run(self, infile=None, infile2=None, outfile=None, **inputs):
        """Execute the command.
        >>> from nipype.interfaces import fsl
        >>> import os
        >>> maths = fsl.ImageMaths(infile='foo.nii', optstring= '-add 5', \
                                   outfile='foo_maths.nii')
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
        """Returns a :class:`nipype.interfaces.base.Bunch` with outputs

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
