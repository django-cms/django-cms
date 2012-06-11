# -*- coding: utf-8 -*-
from django.conf import settings
from django.db.models.base import ModelBase
from cms.publisher.manager import PublisherManager
from mptt.models import MPTTModelBase
from cms.publisher.options import PublisherOptions


class PageMetaClass(MPTTModelBase):
    def __new__(cls, name, bases, attrs):
        super_new = super(PageMetaClass, cls).__new__
        if not settings.CMS_MODERATOR:
            return super_new(cls, name, bases, attrs)

        if 'objects' in attrs:
            if not isinstance(attrs['objects'], PublisherManager):
                raise ValueError, ("Model %s extends Publisher, " +
                                   "so its 'objects' manager must be " +
                                   "a subclass of publisher.PublisherManager") % (name,)
        else:
            attrs['objects'] = PublisherManager()

        attrs['_is_publisher_model'] = lambda self: True

        # build meta object
        publisher_meta = attrs.pop('PublisherMeta', None)
        attrs['_publisher_meta'] = PublisherOptions(name, bases, publisher_meta)

        return super_new(cls, name, bases, attrs)
