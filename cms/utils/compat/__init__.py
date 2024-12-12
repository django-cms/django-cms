from platform import python_version

from django import get_version
from packaging.version import Version

DJANGO_VERSION = get_version()
PYTHON_VERSION = python_version()

# These means "less than or equal to DJANGO_FOO_BAR"
DJANGO_4_2 = Version(DJANGO_VERSION) < Version('4.3')
DJANGO_5_1 = Version(DJANGO_VERSION) < Version('5.2.dev')  # To allow testing against django's main branch
