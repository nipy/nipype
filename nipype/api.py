__author__ = 'satra'


from pipeline import Node, MapNode, JoinNode, Workflow

from .interfaces.io import DataGrabber, DataSink, SelectFiles
from .interfaces.utility import IdentityInterface, Rename, Function, Select, Merge
from .interfaces import fsl, spm, freesurfer, afni, ants, slicer, dipy, nipy, mrtrix, camino
