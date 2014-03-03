from unittest import TestCase
from cms.test_utils.util.static_analysis import pyflakes


class StaticAnalysisTest(TestCase):
    def test_pyflakes(self):
        self.assertEqual(pyflakes(), 0)
