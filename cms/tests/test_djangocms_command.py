import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase, skipIf


def has_no_internet():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(5)
        s.connect(('4.4.4.2', 80))
        s.send(b"hello")
    except socket.error:  # no internet
        return True
    return False


class DjangocmsCommandTest(TestCase):
    @skipIf(has_no_internet(), "No internet")
    def test_djangocms_command(self):
        with TemporaryDirectory() as dir:
            result = subprocess.run(
                [sys.executable, "-m", "cms", "mysite", dir,  "--noinput"],
                env={"DJANGOCMS_ALLOW_PIP_INSTALL": "True"},
            )
            self.assertEqual(result.returncode, 0)
