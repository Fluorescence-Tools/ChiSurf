import utils
import os
import unittest
import sys
import json

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils.set_search_paths(TOPDIR)

import mfm


class Tests(unittest.TestCase):

    def test_create(self):
        p1 = mfm.parameter.Parameter()
        p1.value = 2.0
        self.assertEqual(p1.value, 2.0)

        p2 = mfm.parameter.Parameter(value=2.0)
        self.assertEqual(p2.value, 2.0)

    def test_equality(self):
        p1 = mfm.parameter.Parameter(value=2.0)
        p2 = mfm.parameter.Parameter(value=2.0)
        self.assertEqual(p1, p2)
        self.assertIsNot(p1, p2)

    def test_artimetics(self):
        p1 = mfm.parameter.Parameter(value=2.0)
        p2 = mfm.parameter.Parameter(value=3.0)

        p3 = p1 * p2
        self.assertEqual(p3.value, p1.value * p2.value)

        p3 = p1 / p2
        self.assertEqual(p3.value, p1.value / p2.value)

        p3 = p1 + p2
        self.assertEqual(p3.value, p1.value + p2.value)

        p3 = p1 - p2
        self.assertEqual(p3.value, p1.value - p2.value)


if __name__ == '__main__':
    unittest.main()
