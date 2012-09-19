# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft = python sts = 4 ts = 4 sw = 4 et:

import os
import re

def dicomAcquisitionOrder( dicomFile ):
    """
    Based on personal communication with Vince Magnotta (University of Iowa)
    for Siemans scanners at the U of I

    """
    dicomFile = os.path.abspath(dicomFile)
    pattern = r'(?<=sSliceArray\.ucMode)(.)*'
    result = output = None
    with open(dicomFile, 'rbU') as fid:
        for line in fid:
            # print line
            result = re.search(pattern, line, flags=re.MULTILINE)
            if not result is None:
                print line
                output = result.group(0).split('= ')[1]
                break
    return output

def convertCodeToTpattern(dicomDirectory, acquisitionCode):
    """
    From AFNI documentation of To3D():
    tpattern = Code word that identifies how the slices (z-direction)
               were gathered in time.  The values that can be used:

       alt+z = altplus    = alternating in the plus direction
       alt+z2             = alternating, starting at slice #1
       alt-z = altminus   = alternating in the minus direction
       alt-z2             = alternating, starting at slice #nz-2
       seq+z = seqplus    = sequential in the plus direction
       seq-z = seqminus   = sequential in the minus direction
       zero  = simult     = simultaneous acquisition
       FROM_IMAGE         = (try to) read offsets from input images
       @filename          = read temporal offsets from 'filename'

    For example if nz = 5 and TR = 1000, then the inter-slice
    time is taken to be dt = TR/nz = 200.  In this case, the
    slices are offset in time by the following amounts:

                    S L I C E   N U M B E R
      tpattern        0    1    2    3    4  Comment
      ----------   ---- ---- ---- ---- ----  -------------------------------
      altplus         0  600  200  800  400  Alternating in the +z direction
      alt+z2        400    0  600  200  800  Alternating, but starting at #1
      altminus      400  800  200  600    0  Alternating in the -z direction
      alt-z2        800  200  600    0  400  Alternating, starting at #nz-2
      seqplus         0  200  400  600  800  Sequential  in the +z direction
      seqminus      800  600  400  200    0  Sequential  in the -z direction
      simult          0    0    0    0    0  All slices acquired at once

    If @filename is used for tpattern, then nz ASCII-formatted numbers are
    read from the file.  These are used to indicate the time offsets (in ms)
    for each slice. For example, if 'filename' contains
       0 600 200 800 400
    then this is equivalent to 'altplus' in the above example.

    """
    ### TODO: Can we have To3D() use the @filename method to avoid the util.py file
    modes = {'0x1':'ascending', '0x2':'descending', '0x4':'interleave'}
    tpatterns = {'FROM_IMAGE', 'alt+z', 'alt+z2', 'alt-z', 'alt-z2',
                 'seq+z', 'seq-z', 'zero', '@filename'}
    """
    'The modes are:

    Ascending (0x1) - In this mode, slices are acquired from the negative direction to
    the positive direction
    Descending (0x2) - In this mode, slices are acquired from the positive direction to
    the negative direction
    Interleave (0x4) - In this mode, the order of acquisition depends on the number of
    slices acquired. If there is an odd number of slices (say 27), the slices will be
    collected as:
        1 3 5 7 9 11 13 15 17 19 21 23 25 27 2 4 6 8 10 12 14 16 18 20 22 24 26.
    If there is an even number of slices (say 28), the slices will be collected as:
        2 4 6 8 10 12 14 16 18 20 22 24 26 28 1 3 5 7 9 11 13 15 17 19 21 23 25 27.'
                                                          - V. Magnotta

                                                          """
    default = tpatterns[0]
    dicomDirectory = os.path.abspath(dicomDirectory)
    dicomList = glob.glob(os.path.join(dicomDirectory, '*.dcm'))
    count = len(dicomList)
    if modes[acquisitionCode] == 'interleave':
        if (count % 2) == 0:
            return ''
    return default

if __name__ == '__main__':
    print dicomAcquisitionOrder('/rjorge/structural/jorge_MR/10010/62671308/DTI_008/62671308_008_0001.dcm')
