import platform
from distutils.version import LooseVersion

import django


DJANGO_VERSION = django.get_version()
PYTHON_VERSION = platform.python_version()

# These means "less than or equal to DJANGO_FOO_BAR"
DJANGO_1_8 = LooseVersion(DJANGO_VERSION) < LooseVersion('1.9')
DJANGO_1_9 = LooseVersion(DJANGO_VERSION) < LooseVersion('1.10')
DJANGO_1_10 = LooseVersion(DJANGO_VERSION) < LooseVersion('1.11')
DJANGO_1_11 = LooseVersion(DJANGO_VERSION) < LooseVersion('2.0')
DJANGO_2_0 = LooseVersion(DJANGO_VERSION) < LooseVersion('2.1')
DJANGO_2_1 = LooseVersion(DJANGO_VERSION) < LooseVersion('2.2')
DJANGO_2_2 = LooseVersion(DJANGO_VERSION) < LooseVersion('3.0')
DJANGO_3_0 = LooseVersion(DJANGO_VERSION) < LooseVersion('3.1')
