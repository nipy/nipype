# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
================================
Analyzing data from openfMRI.org
================================

A growing number of datasets are available on openfmri.org. This script
demonstrates how to use nipype to analyze a data set.

    python openfmri_example.py
"""

import argparse

def get_local_datapath(url):
    pass

def analyze_openfmri_dataset(url):
    datapath = get_local_datapath(url)
    pass

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-d', '--dataset', dest='dataset', required=True)

  