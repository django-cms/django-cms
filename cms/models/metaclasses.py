# -*- coding: utf-8 -*-
from django.conf import settings
from django.db.models.base import ModelBase
from publisher.manager import PublisherManager
from publisher.mptt_support import install_mptt, finish_mptt
from publisher.options import PublisherOptions


class PageMetaClass(ModelBase):
    def __new__(cls, name, bases, attrs):
        super_new = super(PageMetaClass, cls).__new__
        if not settings.CMS_MODERATOR:
            attrs = install_mptt(cls, name, bases, attrs)
            new_class = super_new(cls, name, bases, attrs)
            finish_mptt(new_class)
            return new_class
        
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
                    
        
        # take care of mptt, if required
        attrs = install_mptt(cls, name, bases, attrs)
        
        new_class = super_new(cls, name, bases, attrs)
        finish_mptt(new_class)
        return new_class