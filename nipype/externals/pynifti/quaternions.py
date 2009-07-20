'''
Functions to operate on, or return, quaternions

Note - rotation matrices here apply to column vectors, that is,
they are applied on the left of the vector.  For example:

>>> import numpy as np
>>> q = [0, 1, 0, 0] # 180 degree rotation around axis 0
>>> M = quat2mat(q) # from this module
>>> vec = np.array([1, 2, 3]).reshape((3,1)) # column vector
>>> tvec = np.dot(M, vec)
'''

import numpy as np

def fillpositive(xyz):
    ''' Compute unit quaternion from last 3 values
    Parameters
    ----------
    xyz : iterable containing 3 values

    Returns
    -------
    wxyz : array
         Full 4 values of quaternion

    Notes
    -----
    If w, x, y, z are the values in the full quaternion, assumes w is
    positive.

    Gives error if w*w is estimated to be negative

    w = 0 corresponds to a 180 degree rotation

    The unit quaternion specifies that np.dot(wxyz, wxyz) == 1.
    
    If w is positive (assumed here), w is given by:

    w = np.sqrt(1.0-(x*x+y*y+z*z))

    w2 = 1.0-(x*x+y*y+z*z) can be near zero, which will lead to
    numerical instability in sqrt.  Here we use the system maximum
    float type to reduce numerical instability

    Examples
    --------
    >>> import numpy as np
    >>> wxyz = fillpositive([0,0,0])
    >>> np.all(wxyz == [1, 0, 0, 0])
    True
    >>> wxyz = fillpositive([1,0,0]) # Corner case; w is 0
    >>> np.all(wxyz == [0, 1, 0, 0])
    True
    >>> np.dot(wxyz, wxyz)
    1.0
    '''
    # Check inputs (force error if < 3 values)
    if len(xyz) != 3:
        raise ValueError('xyz should have length 3')
    # Use maximum precision
    dt = np.maximum_sctype(np.float)
    xyz = np.asarray(xyz, dtype=dt)
    # Calculate w
    w2 = 1.0 - np.dot(xyz, xyz)
    if w2 < 0:
        raise ValueError('w should be positive')
    return np.r_[np.sqrt(w2), xyz]

def quat2mat(q):
    ''' Calculate rotation matrix corresponding to quaternion

    Parameters
    ----------
    q : 4 element array-like

    Returns
    -------
    M : (3,3) array
      Rotation matrix corresponding to input quaternion *q*

    Notes
    -----
    Rotation matrix applies to column vectors, and is applied to the
    left of coordinate vectors.  The algorithm here allows non-unit
    quaternions.

    References
    ----------
    Algorithm from 
    http://en.wikipedia.org/wiki/Rotation_matrix#Quaternion

    Examples
    --------
    >>> import numpy as np
    >>> M = quat2mat([1, 0, 0, 0]) # Identity quaternion
    >>> np.allclose(M, np.eye(3))
    True
    >>> M = quat2mat([0, 1, 0, 0]) # 180 degree rotn around axis 0
    >>> np.allclose(M, np.diag([1, -1, -1]))
    True
    '''
    qa = np.array(q)
    Nq = np.dot(qa, qa)
    if Nq > 0.0:
        s = 2/Nq
    else:
        s = 0.0
    w, x, y, z = q
    X = x*s
    Y = y*s
    Z = z*s
    wX = w*X; wY = w*Y; wZ = w*Z
    xX = x*X; xY = x*Y; xZ = x*Z
    yY = y*Y; yZ = y*Z; zZ = z*Z
    return np.array([[1.0-(yY+zZ), xY+wZ, xZ-wY],
                     [xY-wZ, 1.0-(xX+zZ), yZ+wX],
                     [xZ+wY, yZ-wX, 1.0-(xX+yY)]])

def mat2quat(M):
    ''' Calculate quaternion corresponding to given rotation matrix

    Parameters
    ----------
    M : array-like
      3x3 rotation matrix

    Returns
    -------
    q : (4,) array
      closest quaternion to input matrix, having positive q[0]

    Notes
    -----    
    Method claimed to be robust to numerical errors in M

    Constructs quaternion by calculating maximum eigenvector for
    matrix K (constructed from input *M*.  Although this is not
    tested, a maximum eigenvalue of 1 corresponds to a valid rotation.

    A quaternion q*-1 corresponds to the same rotation as q; thus the
    sign of the reconstructed quaternion is arbitrary, and we return
    quaternions with positive w (q[0]).
    
    References
    ----------
     * http://en.wikipedia.org/wiki/Rotation_matrix#Quaternion
     * Bar-Itzhack, Itzhack Y. (2000), "New method for extracting the
    quaternion from a rotation matrix", AIAA Journal of Guidance,
    Control and Dynamics 23(6):1085-1087 (Engineering Note), ISSN
    0731-5090

    Examples
    --------
    >>> import numpy as np
    >>> q = mat2quat(np.eye(3)) # Identity rotation
    >>> np.allclose(q, [1, 0, 0, 0])
    True
    >>> q = mat2quat(np.diag([1, -1, -1]))
    >>> np.allclose(q, [0, 1, 0, 0]) # 180 degree rotn around axis 0
    True

    '''
    r11,r12,r13,r21,r22,r23,r31,r32,r33=M.flat
    # Fill only lower half of symmetric matrix
    K = np.array([
        [r11-r22-r33, 0, 0, 0],
        [r21+r12, r22-r11-r33, 0, 0],
        [r31+r13, r32+r23, r33-r11-r22, 0],
        [r23-r32, r31-r13, r12-r21, r11+r22+r33]]) / 3
    # Use Hermitian eigenvectors, values for speed
    vals, vecs = np.linalg.eigh(K)
    # Select largest eigenvector, reorder
    q = vecs[[3, 0, 1, 2],np.argmax(vals)]
    # Prefer quaternion with positive w
    # (q * -1 corresponds to same rotation as q)
    if q[0]<0:
        q *= -1
    return q

# Routines below only used for testing, thus far

def mult(q1, q2):
    ''' Multiply two quaternions

    Parameters
    ----------
    q1 : 4 element sequence
    q2 : 4 element sequence

    Returns
    -------
    q12 : shape (4,) array
    '''
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    w = w1*w2 - x1*x2 - y1*y2 - z1*z2
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2
    y = w1*y2 + y1*w2 + z1*x2 - x1*z2
    z = w1*z2 + z1*w2 + x1*y2 - y1*x2
    return np.array([w, x, y, z])

def conjugate(q):
    return np.array(q) * np.array([1.0,-1,-1,-1])

def norm(q):
    return np.dot(q,q)

def isunit(q):
    return np.allclose(norm(q),1)

def inverse(q):
    return conjugate(q) / norm(q)

def eye():
    ''' Return identity quaternion '''
    return np.array([1.0,0,0,0])

