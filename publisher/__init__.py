from django.conf import settings
from models import Publisher, MpttPublisher
from mptt_support import Mptt
from manager import PublisherManager

__all__ = ('Publisher', 'PublisherManager', 'MpttPublisher', 'Mptt', 'VERSION')

VERSION = (0, 4, 'sintab')