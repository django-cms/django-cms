import sys
from distutils.version import LooseVersion
import django

DJANGO_1_4 = LooseVersion(django.get_version()) < LooseVersion('1.5')
DJANGO_1_5 = LooseVersion(django.get_version()) < LooseVersion('1.6')
DJANGO_1_6 = LooseVersion(django.get_version()) < LooseVersion('1.7')
DJANGO_1_7 = LooseVersion(django.get_version()) < LooseVersion('1.8')

PY2 = sys.version_info[0] == 2