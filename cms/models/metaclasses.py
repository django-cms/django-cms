from django.db.models.base import ModelBase

from cms.publisher.manager import PublisherManager


class PageMetaClass(ModelBase):
    def __new__(cls, name, bases, attrs):
        super_new = super(PageMetaClass, cls).__new__

        if 'objects' in attrs:
            if not isinstance(attrs['objects'], PublisherManager):
                raise ValueError("Model %s extends Publisher, "
                                 "so its 'objects' manager must be "
                                 "a subclass of publisher.PublisherManager") % (name,)
        else:
            attrs['objects'] = PublisherManager()
        return super_new(cls, name, bases, attrs)
