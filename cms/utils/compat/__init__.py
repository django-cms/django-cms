from distutils.version import LooseVersion
import django


# These means "less than or equal to DJANGO_FOO_BAR"
DJANGO_1_6 = LooseVersion(django.get_version()) < LooseVersion('1.7')
DJANGO_1_7 = LooseVersion(django.get_version()) < LooseVersion('1.8')
