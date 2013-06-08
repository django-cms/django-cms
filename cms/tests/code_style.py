import cms
from django.test import testcases
import menus
import pep8
import os


class TestCodeFormat(testcases.TestCase):
    packages = [cms, menus]

    def test_pep8_conformance(self):
        pep8style = pep8.StyleGuide(show_source=True, max_line_length=120)
        for package in self.packages:
            dir = os.path.dirname(package.__file__)
            pep8style.input_dir(dir)
        self.assertEqual(pep8style.options.report.total_errors, 0)