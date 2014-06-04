# Unit test for NiftyFit
from nipype.interfaces.niftyfit import FitDwi
import argparse
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as niu
import nipype.interfaces.io as nio
import os

parser = argparse.ArgumentParser(description='FitDwi unit test')
parser.add_argument('-s','--source', help='Source DWI image', required=True)
parser.add_argument('-bval', '--bval', help='Bvalue file', required=True)
parser.add_argument('-bvec', '--bvec', help='Bvec file', required = True)
parser.add_argument('-m', '--mask', help='Mask image', required=False)
parser.add_argument('-p', '--prior', help='Prior file', required=False)
parser.add_argument('-gn', help='Use Gauss-Newton', required=False)
parser.add_argument('-op','--outputdir', help='Output Directory', required=False)


args = parser.parse_args()

pipeline = pe.Workflow('workflow')

input_node =  pe.Node(niu.IdentityInterface(
            fields=['source_image', 'bval', 'bvec', 'mask', 'prior']),
                        name='input_node')
input_node.inputs.source_image = os.path.abspath(args.source)
input_node.inputs.bval = os.path.abspath(args.bval)
input_node.inputs.bvec = os.path.abspath(args.bvec)
input_node.inputs.mask = args.mask


datasink = pe.Node(nio.DataSink(), name='sinker')
if args.outputdir:
    datasink.inputs.base_directory = os.path.abspath(args.outputdir)
else:
    datasink.inputs.base_directory = '/tmp/'


output_node = pe.Node(niu.IdentityInterface(
            fields=['out_rgbmap', 'out_famap']),
                        name='output_node')

# Begin by scaling the phase image
fit_dwi = pe.Node(interface=FitDwi(), name = 'fit_dwi')

pipeline.connect(input_node, 'source_image', fit_dwi, 'source_file')
pipeline.connect(input_node, 'bval', fit_dwi, 'bval_file')
pipeline.connect(input_node, 'bvec', fit_dwi, 'bvec_file')
pipeline.connect(fit_dwi,'rgbmap_file', output_node, 'out_rgbmap' )



pipeline.connect(output_node, 'out_rgbmap', datasink, 'rgbmap')
pipeline.connect(output_node, 'out_famap', datasink, 'famap')


pipeline.write_graph(graph2use='exec')
pipeline.run()



