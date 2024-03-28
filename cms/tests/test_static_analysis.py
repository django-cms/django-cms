import os
from unittest import TestCase

from ruff.__main__ import find_ruff_bin


class AboveStaticAnalysisCodeTest(TestCase):
    """
    Name is pretty lame, but ensure it's executed before every other test
    """
    def test_ruff(self):
        ruff = find_ruff_bin()
        self.assertEqual(os.spawnv(os.P_WAIT, ruff, ["ruff", "check", "cms", "menus"]), 0)
