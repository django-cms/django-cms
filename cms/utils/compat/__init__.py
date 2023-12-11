from platform import python_version

from django import get_version
from packaging.version import Version

DJANGO_VERSION = get_version()
PYTHON_VERSION = python_version()

# These means "less than or equal to DJANGO_FOO_BAR"
DJANGO_2_2 = Version(DJANGO_VERSION) < Version('3.0')
DJANGO_3_0 = Version(DJANGO_VERSION) < Version('3.1')
DJANGO_3_1 = Version(DJANGO_VERSION) < Version('3.2')
DJANGO_3_2 = Version(DJANGO_VERSION) < Version('3.3')
DJANGO_3 = Version(DJANGO_VERSION) < Version('4.0')
DJANGO_4_1 = Version(DJANGO_VERSION) < Version('4.2')
DJANGO_4_2 = Version(DJANGO_VERSION) < Version('4.3')
