# -*- coding: utf-8 -*-
from cms.toolbar.constants import ALIGNMENTS
from django.conf import settings
from django.utils import simplejson
from django.utils.encoding import force_unicode
from django.utils.functional import Promise


class Serializable(object):
    """
    Base class for objects used in the toolbar. Abstracts the serialization and
    conversion to JSON.
    """
    # attributes that this type and all subclasses of this type should serialize
    base_attributes = []
    # additional attributes to serialize only on this type
    extra_attributes = []
    
    def as_json(self, context, **kwargs):
        """
        Converts the (serialized) data to JSON
        """
        data = self.serialize(context, **kwargs)
        return simplejson.dumps(data)
        
    def serialize(self, context, **kwargs):
        """
        Serializes it's data. Uses self.base_attributes, self.extra_attributes
        and self.get_extra_data to 
        """
        data = {}
        for python, javascript in self.base_attributes:
            self._populate(data, python, javascript, context, **kwargs)
        for python, javascript in self.extra_attributes:
            self._populate(data, python, javascript, context, **kwargs)
        data.update(self.get_extra_data(context, **kwargs))
        return data
    
    def _populate(self, container, python, javascript, context, **kwargs):
        """
        Populates the *container* using the key *javascript* by accessing the
        attribute *python* on *self* (or serialize_*python* if that's a callable
        on *self*).
        """
        if hasattr(self, 'serialize_%s' % python):
            meth = getattr(self, 'serialize_%s' % python)
            value = meth(context, **kwargs)
        else:
            value = getattr(self, python)
        if isinstance(value, Promise):
            value = force_unicode(value)
        container[javascript] = value
    
    def get_extra_data(self, context, **kwargs):
        """
        Hook for subclasses to add more data.
        """
        return {}


class Toolbar(object):
    """
    A base toolbar, implements the request_hook API and the get_items API.
    """
    def __init__(self, request):
        self.request = request
        
    def get_items(self, context, **kwargs):
        return []
    
    def get_extra_data(self, context, **kwargs):
        raw_items = self.get_items(context, **kwargs)
        items = []
        for item in raw_items:
            items.append(item.serialize(context, toolbar=self, **kwargs))
        return {
            'debug': settings.TEMPLATE_DEBUG,
            'items': items,
        }
        
    def request_hook(self):
        """
        May return a HttpResponse instance
        """
        return None

