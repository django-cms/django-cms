from distutils.version import LooseVersion
from platform import python_version

from django import get_version

DJANGO_VERSION = get_version()
PYTHON_VERSION = python_version()

# These means "less than or equal to DJANGO_FOO_BAR"
DJANGO_2_2 = LooseVersion(DJANGO_VERSION) < LooseVersion('3.0')
DJANGO_3_0 = LooseVersion(DJANGO_VERSION) < LooseVersion('3.1')
DJANGO_3_1 = LooseVersion(DJANGO_VERSION) < LooseVersion('3.2')
DJANGO_3_2 = LooseVersion('3.2') <= LooseVersion(DJANGO_VERSION) and  LooseVersion(DJANGO_VERSION) < LooseVersion('3.3')
