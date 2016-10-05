import argparse
from nipype.interfaces.niftyreg import RegMeasure

parser = argparse.ArgumentParser(description='NiftyReg measure nipype unit tests')
parser.add_argument('-r','--ref', help='Reference image path', required=True)
parser.add_argument('-f','--flo', help='Floating image path', required=True)
parser.add_argument('-m','--mea', choices=['ncc', 'lncc', 'nmi', 'ssd'], 
                    default='ncc', help='Measure to compute', required=True);

args = parser.parse_args()

measure = RegMeasure()
measure.inputs.ref_file = args.ref
measure.inputs.flo_file = args.flo
measure.inputs.measure_type = args.mea

result = measure.run()
print(result.outputs.out_file)