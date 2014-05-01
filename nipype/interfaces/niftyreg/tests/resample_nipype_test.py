import argparse
from nipype.interfaces.niftyreg import RegResample

parser = argparse.ArgumentParser(description='NiftyReg resampling nipype unit tests')
parser.add_argument('-t','--ref', help='Reference/Target image path', required=True)
parser.add_argument('-f','--flo', help='Source/Floating image path', required=True)
parser.add_argument('-a','--aff', help='Input affine/rigid transformation', required=False)
parser.add_argument('-c','--cpp', help='Input non-rigid transformation', required=False)
parser.add_argument('-r','--res', help='Output resampled image path', required=False)
parser.add_argument('-b','--bla', help='Output resampled grid image path', required=False)
parser.add_argument('-i','--int', help='Interpolation type', required=False)
parser.add_argument('-p','--pad', help='Padding value', required=False, type=int)

args = parser.parse_args()

resampler = RegResample()
resampler.inputs.ref_file = args.ref
resampler.inputs.flo_file = args.flo

if args.aff is not None:
    resampler.inputs.aff_file = args.aff

if args.cpp is not None:
    resampler.inputs.trans_file = args.cpp

if args.res is not None:
    resampler.inputs.res_file = args.res

if args.bla is not None:
    resampler.inputs.blank_file = args.bla

if args.int is not None:
    resampler.inputs.inter_val = args.int

if args.pad is not None:
    resampler.inputs.pad_val = args.pad

result = resampler.run()