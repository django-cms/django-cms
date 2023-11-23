import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase

class DjangocmsCommandTest(TestCase):
    """
    Name is pretty lame, but ensure it's executed before every other test
    """
    def test_djangocms_command(self):
        with TemporaryDirectory() as dir:
            result = subprocess.run([sys.executable, "-m", "cms", "mysite", dir,  "--noinput"])
        self.assertEqual(result.returncode, 0)
