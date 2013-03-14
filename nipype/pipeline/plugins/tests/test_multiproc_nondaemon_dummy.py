#
# This file is part of the test_multiproc_nondaemon.py
#

def dummyFunction(filename):
    '''
    This function writes the value 45 to the given filename.
    '''
    j = 0
    for i in range(0,10):
      j += i

    # j is now 45 (0+1+2+3+4+5+6+7+8+9)

    with open(filename, 'w') as f:
      f.write(str(j))
      