from distutils.version import LooseVersion
import django


# These means "less than or equal to DJANGO_FOO_BAR"
DJANGO_1_8 = LooseVersion(django.get_version()) < LooseVersion('1.9')
DJANGO_1_9 = LooseVersion(django.get_version()) < LooseVersion('2.0')
