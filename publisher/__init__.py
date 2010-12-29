from django.conf import settings
from models import MpttPublisher
from mptt_support import Mptt
from manager import PublisherManager

__all__ = ('PublisherManager', 'MpttPublisher', 'Mptt', 'VERSION')

VERSION = (0, 4, 'sintab')