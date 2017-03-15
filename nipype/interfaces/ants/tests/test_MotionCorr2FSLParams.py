import csv
import os

from nipype.interfaces.ants.preprocess import MotionCorr2FSLParams
from nipype.utils.tmpdirs import InTemporaryDirectory
from nipype.utils.filemanip import split_filename

def test_MotionCorr2FSLParams():
    with InTemporaryDirectory():
        cwd = os.getcwd()
        in_filename = os.path.join(cwd, 'in_file.csv')
        fp = open(in_filename, 'w+')
        fp.write("this line is ignored\n")
        fp.write(
            "0,-0.99918075422702,1.00028207678993,-7.41063731046199e-06,"
            "3.93289649449106e-05,1.24969530535555e-05,1.00021114616063,"
            "0.000233157514656132,-0.000195740079275366,-0.00033024846828514,"
            "0.999495881936253,-0.0168301940330171,-0.0549722774931478,"
            "0.202056708561567\n"
        )
        fp.close()
        # m2p - matrix 2 parameters
        m2p = MotionCorr2FSLParams()
        m2p.inputs.ants_matrix = in_filename
        m2p.run()

        pth, fname, _ = split_filename(in_filename)
        params_fname = '{}{}'.format(fname, '.par')
        params_fname = os.path.join(pth, params_fname)

        params_fp = open(params_fname)
        params_data = csv.reader(params_fp, delimiter=' ')
        line = next(params_data)
        assert len(line) == 6
