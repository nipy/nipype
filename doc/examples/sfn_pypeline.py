#!/usr/bin/env python 

# This script should be run from directly above the nifti directory where all
# brain imaging files are being kept.

import os
import nipype.pipeline.engine as pe
from sfn_preproc import *
from sfn_l1 import *

##########################
# Setup storage of results
##########################

datasink = nw.NodeWrapper(interface=nio.DataSink())
# I'd like this one to actually be preproc, but for now, I don't want to change
# the pipeline around because of data already being on S3
datasink.inputs.base_directory = os.path.abspath('./nifti/l1output')

#####################
# Set up preproc pype
#####################

preproc = pe.Pipeline()
preproc.config['workdir'] = os.path.abspath('./nifti/workingdir')
preproc.config['use_parameterized_dirs'] = True

preproc.connect([# preprocessing in native space
                 (datasource, skullstrip,[('struct','infile')]),
                 (datasource, motion_correct, 
                     [('func', 'infile'), ('func_ref', 'reffile')]),
                 (motion_correct, func_skullstrip,
                     [('outfile', 'infile')]),
                 (datasource, ref_skullstrip, [('func_ref', 'infile')]),
                 # T1 registration
                 (skullstrip, t1reg2std,[('outfile', 'infile')]),
                 (datasource, t1warp2std,[('struct', 'infile')]),
                 (t1reg2std, t1warp2std, [('outmatrix', 'affine')]),
                 (t1warp2std, t1applywarp, 
                     [('fieldcoeff_file', 'fieldfile')]),
                 # It would seem a little more parsimonious to get this from
                 # t1warp2std, but it's only an input there...
                 (datasource, t1applywarp, [('struct', 'infile')]),
                 # Functional registration
                 (ref_skullstrip, ref2t1, [('outfile', 'infile')]),
                 (skullstrip, ref2t1, [('outfile', 'reference')]),
                 (ref2t1, funcapplywarp, [('outmatrix', 'premat')]),
                 (t1warp2std, funcapplywarp,
                      [('fieldcoeff_file', 'fieldfile')]),
                 (func_skullstrip, funcapplywarp, [('outfile', 'infile')]),
                 # Smooth :\
                 (funcapplywarp, smoothing, [('outfile', 'infile')]),
                ])


# store relevant outputs from various stages of preprocessing
preproc.connect([(datasource,datasink,[('subject_id','subject_id')]),
                    (skullstrip, datasink, 
                        [('outfile', 'skullstrip.@outfile')]),
                    (func_skullstrip, datasink,
                        [('outfile', 'skullstrip.@outfile')]),
                    (motion_correct, datasink,
                        [('parfile', 'skullstrip.@parfile')]),
                    # We aren't really going to look at these, are we?
                    # (t1reg2std, datasink, 
                    #     [('outmatrix', 'registration.@outmatrix')]),
                    # (t1warp2std, datasink, 
                    #     [('fieldcoeff_file', 'registration.@fieldcoeff_file')]),
                    (t1applywarp, datasink,
                        [('outfile', 'registration.@outfile')]),
                    (funcapplywarp, datasink,
                        [('outfile', 'registration.@outfile')]),
                    (smoothing, datasink, 
                        [('outfile', 'registration.@outfile')]),
                    ])

####################
# Set up l1 pipeline
####################

l1 = pe.Pipeline()

preproc.config['workdir'] = os.path.abspath('./nifti/workingdir')
preproc.config['use_parameterized_dirs'] = True

l1.connect([(l1_datasource, l1_feat,[('struct','struct_file'),
                                     ('func',  'func_file')] ),
           ])

l1.connect([(l1_feat, datasink, [])])
# #########################################################################
# # setup level 2 pipeline
# 
# # collect all the con images for each contrast.
# contrast_ids = range(1,len(contrasts)+1)
# l2source = nw.NodeWrapper(nio.DataGrabber())
# l2source.inputs.file_template=os.path.abspath('l1output/*/con*/con_%04d.img')
# l2source.inputs.template_argnames=['con']
# 
# # iterate over all contrast images
# l2source.iterables = dict(con=lambda:contrast_ids)
# 
# # setup a 1-sample t-test node
# onesamplettest = nw.NodeWrapper(interface=spm.OneSampleTTest(),diskbased=True)
# 
# # setup the pipeline
# l2pipeline = pe.Pipeline()
# l2pipeline.config['workdir'] = os.path.abspath('l2output')
# l2pipeline.config['use_parameterized_dirs'] = True
# l2pipeline.connect([(l2source,onesamplettest,[('file_list','con_images')])])


if __name__ == '__main__':
    from sys import argv
    if 'preproc' in argv:
        preproc.run()
    if 'l1' in argv:
        l1.run()
