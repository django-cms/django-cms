import doctest
import unittest

from mptt.tests import doctests
from mptt.tests import testcases

def suite():
    s = unittest.TestSuite()
    s.addTest(doctest.DocTestSuite(doctests))
    s.addTest(unittest.defaultTestLoader.loadTestsFromModule(testcases))
    return s
