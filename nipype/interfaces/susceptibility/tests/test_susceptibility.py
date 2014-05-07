# Unit test for the susceptibility tools, requires FSL to run BET
from nipype.testing import assert_equal
from nipype.interfaces.susceptibility import GenFm, PhaseUnwrap, PmScale
import nipype.interfaces.fsl as fsl


parser = argparse.ArgumentParser(description='Susceptibility tools interface unit test')
parser.add_argument('-p','--phase', help='Phase image', required=True)
parser.add_argument('-i', '--mag', help='Magnitude image', required=True)
parser.add_argument('-m', '--mask', help='Mask image', required=False)
parser.add_argument('-etd', '--etd', help='Echo time difference', required=True)
parser.add_argument('-ped', '--ped', help='Phase encode direction', required=True)
parser.add_argument('-rot', '--rot', help='Read out time', required=True)
args = parser.parse_args()

# Begin by scaling the phase image
pm_scale = PmScale()
pm_scale.inputs.in_pm = args.phase
# Should rename the output of the scaled phase map
pm_scale.inputs.out_pm = args.phase

# If no mask image was provided, then we need to run BET to make one
if args.mask is None:
    #BET your heart out
    bet = fsl.BET()
    bet.inputs.in_file = args.mag
    #bet.outputs.out_file =
    #bet.run()

# Then unwrapping
pm_unwrap PhaseUnwrap()
pm_unwrap.inputs.in_fm = pm_scale.outputs.out_pm

# Finally, estimate the field map and the corresponding deformation field
gen_fm = GenFm()
#gen_fm.inputs.






