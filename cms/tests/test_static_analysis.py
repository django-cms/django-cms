from django.test import testcases

from cms.test_utils.util.static_analysis import pyflakes


class AboveStaticAnalysisCodeTest(testcases.TestCase):
    """
    Name is pretty lame, but ensure it's executed before every other test
    """
    def test_pyflakes(self):
        import cms
        import menus
        errors, message = pyflakes((cms, menus))
        self.assertEqual(errors, 0, message)
