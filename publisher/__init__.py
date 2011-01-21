# -*- coding: utf-8 -*-
from django.conf import settings
from mptt_support import Mptt
from manager import PublisherManager

__all__ = ('PublisherManager', 'Mptt', 'VERSION')

VERSION = (0, 4, 'sintab')