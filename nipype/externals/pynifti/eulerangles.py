''' These give the derivations for Euler angles to rotation matrix and
Euler angles to quaternion.  We use the rotation matrix derivation only
in the tests.  The quaternion derivation is in the tests, and,
in more compact form, in the ``euler2quat`` code.

The rotation matrices operate on column vectors, thus, if ``R`` is the
3x3 rotation matrix, ``v`` is the 3 x N set of N vectors to be rotated,
and ``vdash`` is the matrix of rotated vectors::

   vdash = np.dot(R, v)


'''

from sympy import Symbol, cos, sin
from sympy.matrices import Matrix


def x_rotation(theta):
    ''' Rotation angle `theta` around x-axis
    http://en.wikipedia.org/wiki/Rotation_matrix#Dimension_three
    '''
    return Matrix([[1, 0, 0],
                   [0, cos(theta), -sin(theta)],
                   [0, sin(theta), cos(theta)]])


def y_rotation(theta):
    ''' Rotation angle `theta` around y-axis
    http://en.wikipedia.org/wiki/Rotation_matrix#Dimension_three
    '''
    return Matrix([[cos(theta), 0, sin(theta)],
                  [0, 1, 0],
                  [-sin(theta), 0, cos(theta)]])


def z_rotation(theta):
    ''' Rotation angle `theta` around z-axis
    http://en.wikipedia.org/wiki/Rotation_matrix#Dimension_three
    '''
    return Matrix([[cos(theta), -sin(theta), 0],
                  [sin(theta), cos(theta), 0],
                  [0, 0, 1]])


def qmult(q1, q2):
    ''' Multiply two quaternions

    Parameters
    ----------
    q1 : 4 element sequence
    q2 : 4 element sequence

    Returns
    -------
    q12 : shape (4,) array

    Notes
    -----
    See : http://en.wikipedia.org/wiki/Quaternions#Hamilton_product
    '''
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    w = w1*w2 - x1*x2 - y1*y2 - z1*z2
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2
    y = w1*y2 + y1*w2 + z1*x2 - x1*z2
    z = w1*z2 + z1*w2 + x1*y2 - y1*x2
    return w, x, y, z


def quat_around_axis(theta, axis):
    ''' Quaternion for rotation of angle `theta` around axis `axis`

    Parameters
    ----------
    theta : symbol
       angle of rotation
    axis : 3 element sequence
       vector (assumed normalized) specifying axis for rotation

    Returns
    -------
    quat : 4 element sequence of symbols
       quaternion giving specified rotation

    Notes
    -----
    Formula from http://mathworld.wolfram.com/EulerParameters.html
    '''
    # axis vector assumed normalized
    t2 = theta / 2.0
    st2 = sin(t2)
    return (cos(t2),
            st2 * axis[0],
            st2 * axis[1],
            st2 * axis[2])


def quat2mat(quat):
    ''' Symbolic conversion from quaternion to rotation matrix

    For a unit quaternion
    
    From: http://en.wikipedia.org/wiki/Rotation_matrix#Quaternion
    '''
    w, x, y, z = quat
    return Matrix([
            [1 - 2*y*y-2*z*z, 2*x*y - 2*z*w, 2*x*z+2*y*w],
            [2*x*y+2*z*w, 1-2*x*x-2*z*z, 2*y*z-2*x*w],
            [2*x*z-2*y*w, 2*y*z+2*x*w, 1-2*x*x-2*y*y]])


# Formula for rotation matrix given Euler angles and z, y, x ordering
M_zyx = (x_rotation(Symbol('x')) *
         y_rotation(Symbol('y')) *
         z_rotation(Symbol('z')))

# Formula for quaternion given Euler angles, z, y, x ordering
q_zrot = quat_around_axis(Symbol('z'), [0, 0, 1])
q_yrot = quat_around_axis(Symbol('y'), [0, 1, 0])
q_xrot = quat_around_axis(Symbol('x'), [1, 0, 0])

q_zyx = qmult(q_xrot, qmult(q_yrot, q_zrot))
