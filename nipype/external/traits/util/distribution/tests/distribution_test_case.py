import unittest
import numpy

from traits.util.distribution.api import Uniform

class DistributionTest(unittest.TestCase):

    def test_random_state(self):
        """ tests the ability to reproduce distributions
            using the random state member

        """

        dist = Uniform(low=10.0, high=20.0)
        state = dist.get_state()

        dist2 = Uniform(low=10.0, high=20.0)

        self.assertFalse(numpy.equal(dist.values, dist2.values).all())

        dist2.set_state(state)
        self.assertTrue(numpy.equal(dist.values, dist2.values).all())

    def test_value_size(self):
        """ tests that the number of elements in a distribution is
            the same as what it was constructed to be

        """
        dist = Uniform(samples=123)
        self.assertEqual(123, (len(dist.values)))
