import os

import numpy

from nipype.interfaces.ants.preprocess import MotionCorr2FSLParams
from nipype.interfaces.fsl.utils import AvScale
from nipype.utils.tmpdirs import InTemporaryDirectory
from nipype.utils.filemanip import split_filename

def test_MotionCorr2FSLParams():
    with InTemporaryDirectory():
        cwd = os.getcwd()
        fsl_mat_fname = "fsl_style.mat"
        fp = open(fsl_mat_fname, 'w+')
        fp.write(
            "1.000000 0.000000 -0.000935 0.062539\n"
            "0.000001 0.999999 0.001470 -0.162467\n"
            "0.000935 -0.001470 0.999999 -0.279038\n"
            "0.000000 0.000000 0.000000 1.000000\n"
        )
        fp.close()

        in_filename = os.path.join(cwd, 'in_file.csv')
        fp = open(in_filename, 'w+')
        fp.write("this line is ignored\n")
        fp.write(
            "0,-0.99918075422702,1.000000,0.000000,-0.000935,0.000001,"
            "0.999999,0.001470,0.000935,-0.001470,0.999999,-0.279038,0.062539,"
            "-0.162467,-0.279038\n"
        )
        fp.close()

        # m2p - matrix 2 parameters
        m2p = MotionCorr2FSLParams()
        m2p.inputs.ants_matrix = in_filename
        m2p.run()

        pth, fname, _ = split_filename(in_filename)
        conv_params_fname = '{}{}'.format(fname, '.par')
        conv_params_fname = os.path.join(pth, conv_params_fname)

        avscale = AvScale()
        avscale.inputs.all_param = True
        avscale.inputs.mat_file = fsl_mat_fname
        avscale.run()
        avscale_out = avscale.aggregate_outputs()
        orig_params = []
        orig_params.extend(avscale_out.rot_angles)
        orig_params.extend(avscale_out.translations)
        conv_params = numpy.genfromtext(conv_params_fname, delimeter=' ')
        comp = numpy.isclose(conv_params, orig_params)

        assert(False not in comp)
