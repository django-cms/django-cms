# -*- coding: utf-8 -*-
from cms.forms.fields import PageSelectFormField, PlaceholderFormField
from cms.models.pagemodel import Page
from cms.models.placeholdermodel import Placeholder
from cms.utils.placeholder import PlaceholderNoAction, validate_placeholder_name
from django.db import models
from django.utils.text import capfirst
from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import class_prepared


def validate_placeholder_field(cls, field):
    dynamic_name_callable = field.dynamic_slot_callable % field.name
    try:
        slotname = getattr(cls, dynamic_name_callable)
    except AttributeError:
        msg = "Please provide slotname or define a %s callable in your model %s." % (dynamic_name_callable, cls.__name__)
        raise ImproperlyConfigured(msg)
    else:
        if not callable(slotname):
            msg = "Please make sure %s is a callable in your model %s." % (dynamic_name_callable, cls.__name__)
            raise ImproperlyConfigured(msg)


def validate_placeholder_fields(sender, **kwargs):
    opts = sender._meta
    for field in opts.local_fields:
        if isinstance(field, PlaceholderField) and not field.slotname:
            validate_placeholder_field(sender, field)


class PlaceholderField(models.ForeignKey):
    dynamic_slot_callable = 'get_%s_placeholder_slot'

    def __init__(self, slotname=None, default_width=None, actions=PlaceholderNoAction, **kwargs):
        if kwargs.get('related_name', None) == '+':
            raise ValueError("PlaceholderField does not support disabling of related names via '+'.")
        self.slotname = slotname
        self.default_width = default_width
        self.actions = actions()
        kwargs.update({'null': True})  # always allow Null
        kwargs.update({'editable': False}) # never allow edits in admin
        super(PlaceholderField, self).__init__(Placeholder, **kwargs)

    def _get_new_placeholder(self, instance):
        return Placeholder.objects.create(slot=self._get_placeholder_slot(instance), default_width=self.default_width)

    def _get_placeholder_slot(self, model_instance):
        if self.slotname is None:
            slot_callable = self.dynamic_slot_callable % self.name
            self.slotname = getattr(model_instance, slot_callable)()
            validate_placeholder_name(self.slotname)
        return self.slotname

    def pre_save(self, model_instance, add):
        if not model_instance.pk:
            setattr(model_instance, self.name, self._get_new_placeholder(model_instance))
        else:
            slot = self._get_placeholder_slot(model_instance)
            placeholder = getattr(model_instance, self.name)
            if placeholder.slot != slot:
                placeholder.slot = slot
                placeholder.save()
        return super(PlaceholderField, self).pre_save(model_instance, add)

    def save_form_data(self, instance, data):
        data = getattr(instance, self.name, '')
        if not isinstance(data, Placeholder):
            data = self._get_new_placeholder(model_instance)
        super(PlaceholderField, self).save_form_data(instance, data)

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect ourselves, since we inherit.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.related.ForeignKey"
        args, kwargs = introspector(self)
        # That's our definition!
        return (field_class, args, kwargs)

    def contribute_to_class(self, cls, name):
        super(PlaceholderField, self).contribute_to_class(cls, name)
        if not hasattr(cls._meta, 'placeholder_field_names'):
            cls._meta.placeholder_field_names = []
        if not hasattr(cls._meta, 'placeholder_fields'):
            cls._meta.placeholder_fields = {}
        if self.slotname is None:
            class_prepared.connect(validate_placeholder_fields, sender=cls, dispatch_uid='%s_placeholder_validation' % cls.__name__)
        else:
            validate_placeholder_name(self.slotname)
        cls._meta.placeholder_field_names.append(name)
        cls._meta.placeholder_fields[self] = name
        self.model = cls


class PageField(models.ForeignKey):
    default_form_class = PageSelectFormField
    default_model_class = Page

    def __init__(self, **kwargs):
        # we call ForeignKey.__init__ with the Page model as parameter...
        # a PageField can only be a ForeignKey to a Page
        super(PageField, self).__init__(self.default_model_class, **kwargs)

    def formfield(self, **kwargs):
        defaults = {
            'form_class': self.default_form_class,
        }
        defaults.update(kwargs)
        return super(PageField, self).formfield(**defaults)

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.related.ForeignKey"
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)
