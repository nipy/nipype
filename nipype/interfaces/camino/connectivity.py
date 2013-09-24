"""
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)

"""
from nipype.interfaces.base import (traits, TraitedSpec, File,
                                    CommandLine, CommandLineInputSpec,
                                    StdOutCommandLine, StdOutCommandLineInputSpec,
                                    Undefined, isdefined )
from nipype.utils.filemanip import split_filename
import os
import os.path as op


class ConmatInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, mandatory=True,
                    desc='A camino-format tracts file')

    roi_file = File(exists=True, argstr='-targetfile %s', mandatory=True,
                    desc='An image containing targets, as used in procstreamlines.')

    out_prefix = File(argstr='-outputroot %s',
                      desc='File root for the output. The extension will be\
                            determined from the input.')

    roi_names = File(exists=True, argstr='-targetnamefile %s', mandatory=False,
                    desc='Optional names of targets. This file should contain one\
                          entry per line, with the target intensity followed by the\
                          name, separated by white space')

    scalar_file = File(exists=True, argstr='-scalarfile %s',
                    mandatory=False,
                    desc='Optional scalar file for computing tract-based statistics.\
                          Must be in the same space as the target file.')

    tractstat = traits.Enum( 'mean', 'min', 'max', 'sum', 'median', 'var',
                             'meanvar', 'length', 'endpointsep',
                              argstr='-tractstat %s', mandatory=False,
                              desc='Tract statistic to use.' )


class ConmatOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='connectivity matrix in text file')
    out_tractstat = File( desc='tract chosen statistic average text file' )

class Conmat(CommandLine):
    """
    Creates a connectivity matrix using a 3D label image (the target image) and a set of streamlines.
    The connectivity matrix records how many streamlines connect each pair of targets, and optionally
    the mean tractwise statistic (eg tract-averaged FA, or length).

    The output is a comma separated variable file or files. The first row of the output matrix is label
    names. Label names may be defined by the user, otherwise they are assigned based on label intensity.

    Example
    -------

    >>> import nipype.interfaces.camino as cmon
    >>> mapper = cmon.Conmat()
    >>> mapper.inputs.in_file = 'brain_track.Bdouble'
    >>> mapper.inputs.roi_file = 'wm_undersampled.nii'
    >>> mapper.run()                  # doctest: +SKIP
    """
    _cmd = 'conmat'
    input_spec=ConmatInputSpec
    output_spec=ConmatOutputSpec

    def _parse_inputs( self, skip=None ):
        if skip is None:
            skip = []

        self._cmd = 'cat %s | conmat' % self.inputs.in_file
        skip+= 'in_file'

        if not isdefined( self.inputs.out_prefix ):
            _, name, _ = split_filename( self.inputs.in_file )
            self.inputs.out_prefix = op.abspath( './' + name + '_conmat_' )

        return super(Conmat, self)._parse_inputs(skip=skip)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self._gen_outfilename()
        outputs['out_tractstat'] = Undefined
        if isdefined( self.inputs.scalar_file ):
            outputs['out_tractstat'] = self.inputs.out_prefix + 'ts.csv'

        return outputs

    def _gen_outfilename(self):
        return self.inputs.out_prefix + 'sc.csv'

# OLD Conmap ---------------------------------------------------

class ConmapInputSpec(StdOutCommandLineInputSpec):
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

    threshold = traits.Int(argstr='-threshold %d', units='NA',
                desc='threshold indicates the minimum number of fiber connections that has to be drawn in the graph.')

class ConmapOutputSpec(TraitedSpec):
    conmap_txt = File(exists=True, desc='connectivity matrix in text file')

class Conmap(StdOutCommandLine):
    """
    Creates a graph representing the tractographic connections between the regions in the segmented image.

    This function creates 'Connectivity.png', shown in figure 1, with the graph representing the ROIs and the
    connections between them. The thickness of the connections is proportional to the number of fibers
    connecting those two regions. The vertices of the graph indicate the ROI and their diameter is
    proportional to the number of tracts reaching that vertex or ROI. Another file, 'ConnectionMatrix.txt',
    containing a matrix of the number of tracts connecting different regions, is created at the same location.

    If the mapping between few segments in the brain is required, the indices of those regions can be given separately. The labels and the indices of the different segments in wmparc.mgz can be found at brain1/stats/wmparc.stats. Create a file, say indices.txt with comma-separated indices of the required segments.

    1001,1002,1003,1004,1005

    where 1001,1002.. are the indices of the segments for which graph has to be drawn. The labels of the different vertices can be specified, by creating a file say indices-labels.txt in the following format.

    1001:lBSTS
    1002:lCAC
    1003:lCMF

    Example
    -------

    >>> import nipype.interfaces.camino as cmon
    >>> mapper = cmon.Conmap()
    >>> mapper.inputs.in_file = 'brain_track.Bdouble'
    >>> mapper.inputs.roi_file = 'wm_undersampled.nii'
    >>> mapper.inputs.index_file = 'indices.txt'
    >>> mapper.inputs.index_file = 'indices-labels.txt'
    >>> mapper.inputs.threshold = 100
    >>> mapper.run()                  # doctest: +SKIP
    """
    _cmd = 'conmap'
    input_spec=ConmapInputSpec
    output_spec=ConmapOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['conmap_txt'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '_conmap'
