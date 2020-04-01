from unittest import TestCase

from cms.test_utils.util.static_analysis import pyflakes
from cms.utils.compat import DJANGO_3_0


class AboveStaticAnalysisCodeTest(TestCase):
    """
    Name is pretty lame, but ensure it's executed before every other test
    """
    def test_pyflakes(self):
        import cms
        import menus
        if not DJANGO_3_0:
            errors, message = pyflakes((cms, menus))
            self.assertEqual(errors, 0, message)
