from platform import python_version

from django import get_version
from packaging.version import Version

DJANGO_VERSION = get_version()
PYTHON_VERSION = python_version()

DJANGO_3_2 = Version(DJANGO_VERSION) < Version('3.3')
DJANGO_3 = Version(DJANGO_VERSION) < Version('4.0')
DJANGO_4_2 = Version(DJANGO_VERSION) < Version('4.3')
