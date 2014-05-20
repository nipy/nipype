# Unit test for the susceptibility tools, requires FSL to run BET
from nipype.testing import assert_equal
from nipype.interfaces.susceptibility import GenFm, PhaseUnwrap, PmScale
import nipype.interfaces.fsl as fsl
import argparse
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as niu

parser = argparse.ArgumentParser(description='Susceptibility tools interface unit test')
parser.add_argument('-p','--phase', help='Phase image', required=True)
parser.add_argument('-i', '--mag', help='Magnitude image', required=True)
parser.add_argument('-m', '--mask', help='Mask image', required=False)
parser.add_argument('-etd', '--etd', help='Echo time difference (ms)', required=True,type=float)
parser.add_argument('-ped', '--ped', help='Phase encode direction (ms)', required=True)
parser.add_argument('-rot', '--rot', help='Read out time', required=True, type=float)
args = parser.parse_args()

pipeline = pe.Workflow('workflow')

input_node =  pe.Node(niu.IdentityInterface(
            fields=['phase_image', 'mag_image', 'etd', 'ped', 'rot']),
                        name='input_node')
input_node.inputs.phase_image = args.phase
input_node.inputs.mag_image = args.mag
input_node.inputs.etd = args.etd
input_node.inputs.ped = args.ped
input_node.inputs.rot = args.rot

# Begin by scaling the phase image
pm_scale = pe.Node(interface=PmScale(), name = 'pm_scale')

bet = pe.Node(interface=fsl.BET(), name='bet')
bet.inputs.mask = True
bet.inputs.no_output = True

pm_unwrap = pe.Node(interface=PhaseUnwrap(), name= 'phase_unwrap')

gen_fm = pe.Node(interface=GenFm(), name='gen_fm')

output_node = pe.Node(niu.IdentityInterface(
            fields=['out_fm', 'out_field']),
                        name='output_node')

pipeline.connect(input_node, 'phase_image', pm_scale, 'in_pm')
pipeline.connect(input_node, 'mag_image', bet, 'in_file')

pipeline.connect(bet, 'mask_file', pm_unwrap, 'in_mask')
pipeline.connect(pm_scale, 'out_pm', pm_unwrap, 'in_fm')
pipeline.connect(input_node, 'mag_image', pm_unwrap, 'in_mag' )

pipeline.connect(input_node, 'etd', gen_fm, 'in_etd')
pipeline.connect(input_node, 'rot', gen_fm, 'in_rot')
pipeline.connect(input_node, 'ped', gen_fm, 'in_ped')
pipeline.connect(bet, 'mask_file', gen_fm, 'in_mask' )
pipeline.connect(pm_unwrap, 'out_fm', gen_fm, 'in_ufm')

pipeline.connect(gen_fm, 'out_fm', output_node, 'out_fm')
pipeline.connect(gen_fm, 'out_field', output_node, 'out_field')

pipeline.write_graph(graph2use='exec')
pipeline.run()



