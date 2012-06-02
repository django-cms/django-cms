# -*- coding: utf-8 -*-
from cms.forms.fields import PageSelectFormField, PlaceholderFormField
from cms.forms.widgets import PlaceholderPluginEditorWidget
from cms.models.pagemodel import Page
from cms.models.placeholdermodel import Placeholder
from cms.utils.placeholder import PlaceholderNoAction, validate_placeholder_name
from django.db import models
from django.utils.text import capfirst



class PlaceholderField(models.ForeignKey):
    def __init__(self, slotname, default_width=None, actions=PlaceholderNoAction, **kwargs):
        validate_placeholder_name(slotname)
        self.slotname = slotname
        self.default_width = default_width
        self.actions = actions()
        kwargs.update({'null':True}) # always allow Null
        super(PlaceholderField, self).__init__(Placeholder, **kwargs)
    
    def formfield(self, **kwargs):
        """
        Returns a django.forms.Field instance for this database Field.
        """
        return self.formfield_for_admin(None, lambda qs: qs, **kwargs)
    
    def formfield_for_admin(self, request, filter_func, **kwargs):
        defaults = {'label': capfirst(self.verbose_name), 'help_text': self.help_text}
        defaults.update(kwargs)
        widget = PlaceholderPluginEditorWidget(request, filter_func)
        widget.choices = []
        return PlaceholderFormField(required=False, widget=widget, **defaults)
    
    def _get_new_placeholder(self):
        return Placeholder.objects.create(slot=self.slotname,
            default_width=self.default_width)

    def pre_save(self, model_instance, add):
        if not model_instance.pk:
            setattr(model_instance, self.name, self._get_new_placeholder())
        return super(PlaceholderField, self).pre_save(model_instance, add)

    def save_form_data(self, instance, data):
        if not instance.pk:
            data = self._get_new_placeholder()
        else:
            data = getattr(instance, self.name)
            if not isinstance(data, Placeholder):
                data = self._get_new_placeholder()
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
