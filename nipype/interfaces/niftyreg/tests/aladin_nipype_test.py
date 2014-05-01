import argparse
from nipype.interfaces.niftyreg import RegAladin

parser = argparse.ArgumentParser(description='NiftyReg aladin nipype unit tests')
parser.add_argument('-t','--ref', help='Reference/Target image path', required=True)
parser.add_argument('-f','--flo', help='Source/Floating image path', required=True)
parser.add_argument('-a','--aff', help='Output affine file path')
parser.add_argument('-r','--res', help='Output transformed floating image file path')

args = parser.parse_args()
aladin = RegAladin()

aladin.inputs.ref_file = args.ref
aladin.inputs.flo_file = args.flo

if args.aff is not None:
    aladin.inputs.aff_file = args.aff

if args.res is not None:
    aladin.inputs.result_file = args.res

result = aladin.run()