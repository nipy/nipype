"""
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)

"""
from nipype.interfaces.base import (traits, TraitedSpec, File,
                                    StdOutCommandLine, StdOutCommandLineInputSpec)
from nipype.utils.filemanip import split_filename
import os

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
                desc="threshold indicates the minimum number of fiber connections that has to be drawn in the graph.")

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
