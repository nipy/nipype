import argparse
from nipype.interfaces.niftyreg import RegJacobian

parser = argparse.ArgumentParser(description='NiftyReg jacobian nipype unit tests')
parser.add_argument('-t','--trans', help='Transformation path', required=True)
parser.add_argument('-j','--jac', help='Jacobian determinant path')
parser.add_argument('-m','--jacM', help='Jacobian matrix path')
parser.add_argument('-l','--jacL', help='Log of jacobian determinant path')
parser.add_argument('-r','--ref', help='Reference/target image')

args = parser.parse_args()

jacobian = RegJacobian()
jacobian.inputs.trans_file = args.trans

if args.jac is not None:
    jacobian.inputs.jac_det_file = args.jac

if args.jacM is not None:
    jacobian.inputs.jac_mat_file = args.jacM

if args.jacL is not None:
    jacobian.inputs.jac_log_file = args.jacL

if args.ref is not None:
    jacobian.inputs.ref_file_name = args.ref

result = jacobian.run()